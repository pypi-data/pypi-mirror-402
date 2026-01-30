"""
CLI for performing root cause analysis on data model changes:
`opendapi local local rca`
"""

import datetime
import os
from collections import defaultdict
from typing import Callable, Dict, NamedTuple, Optional, Tuple

import click
from rich.console import Group
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TimeElapsedColumn, TimeRemainingColumn
from rich.rule import Rule
from rich.text import Text

from opendapi.adapters.git import (
    ChangeTriggerEvent,
    CommitInfo,
    get_ancestry_path,
    get_commit_after_timestamp,
    get_commit_before_timestamp,
    get_commit_info,
)
from opendapi.cli.common import (
    get_opendapi_config_from_root,
    get_root_dir_validated,
    rich_formatted_print,
    swallow_outputs,
)
from opendapi.cli.context_agnostic import (
    collect_collected_files,
    server_sync_minimal_schemas,
)
from opendapi.cli.onboarding.opendapi_config import InteractiveIntegrationOnboardBase
from opendapi.cli.repos.local.runners.local.options import rca_options
from opendapi.defs import CommitType, IntegrationMode, OpenDAPIEntity
from opendapi.validators.defs import CollectedFile, OpenDAPIEntityCICDMetadata

from .defs import RCAType

######### Types #########


class SingleCommitCollectedFilesInfo(NamedTuple):
    """Information about the collected files for a single commit."""

    from_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]]
    to_collected_files: Dict[OpenDAPIEntity, Dict[str, CollectedFile]]
    from_sha: str
    to_sha_commit_info: CommitInfo


class DapiFieldInfo(NamedTuple):
    """Information about a field in a DAPI."""

    name: str
    data_type: str
    is_nullable: bool
    is_addition: bool

    def nullability_str(self) -> str:
        """Get the nullability string."""
        return "nullable" if self.is_nullable else "not nullable"


class SingleCommitDiffInfo(NamedTuple):
    """Information about the changes in a single commit."""

    additions: list[DapiFieldInfo]
    removals: list[DapiFieldInfo]
    commit_info: CommitInfo
    dapi_was_created: bool
    dapi_was_deleted: bool

    def risky_diffs(self) -> list[DapiFieldInfo]:
        """Get the risky diffs."""
        return self.removals

    def benign_diffs(self) -> list[DapiFieldInfo]:
        """Get the benign diffs."""
        removal_field_names = {removal.name for removal in self.removals}
        return [
            addition
            for addition in self.additions
            if addition.name not in removal_field_names
        ]

    def get_diff(self) -> Group:
        """Get the diff."""
        lines: list[Text] = []

        additions_by_field_name = {
            addition.name: addition for addition in self.additions
        }
        removals_by_field_name = {removal.name: removal for removal in self.removals}
        total_field_names = (
            additions_by_field_name.keys() | removals_by_field_name.keys()
        )
        if self.dapi_was_created:
            lines.append(Text("  + Model created", style="green"))
        if self.dapi_was_deleted:
            lines.append(Text("  - Model deleted", style="red"))

        # NOTE: if we want to roll up the changes when there is a model creation/deletion,
        #       we can add an if statement here (if model not model created then show)
        for field_name in total_field_names:
            addition = additions_by_field_name.get(field_name)
            if addition:
                t = Text(
                    f"  + {field_name} ({addition.data_type} · {addition.nullability_str()})"
                )
                t.stylize("green")
                lines.append(t)

            removal = removals_by_field_name.get(field_name)
            if removal:
                t = Text(
                    f"  - {field_name} ({removal.data_type} · {removal.nullability_str()})"
                )
                t.stylize("red")
                lines.append(t)

        return Group(*lines)

    def render(self) -> Panel:
        """Render the commit diff."""
        # First line: commit + timestamp
        header = Text()
        header.append("• ", style="bold")
        header.append(self.commit_info.sha[:12], style="bold cyan")
        header.append(f"  ({self.commit_info.to_utc_iso_timestamp()})", style="dim")

        # Message
        commit_subject = Text()
        if self.commit_info.subject:
            commit_subject.append("  Subject: ", style="dim")
            commit_subject.append(self.commit_info.subject)

        commit_body = Text()
        if self.commit_info.body:
            commit_body.append("  Body: ", style="dim")
            commit_body.append(self.commit_info.body)

        additions_by_field_name = {
            addition.name: addition for addition in self.additions
        }

        # Risk block
        risk = Text()
        risky_diffs = self.risky_diffs()
        if risky_diffs or self.dapi_was_deleted:
            risk.append("  High-risk changes:\n", style="bold red")

        if self.dapi_was_deleted:
            risk.append("    *  Model deleted\n", style="red")

        # NOTE: if we want to roll up the changes when there is a model creation/deletion,
        #       we can add an if statement here (if model not model created then show)
        for risky_diff in risky_diffs:
            maybe_addition = additions_by_field_name.get(risky_diff.name)
            if not maybe_addition:
                risk.append("    *  Field deleted: ", style="red")
                risk.append(risky_diff.name, style="bold red")
                risk.append(
                    f" ({risky_diff.data_type} · {risky_diff.nullability_str()})\n",
                    style="red",
                )
                continue

            if maybe_addition.data_type != risky_diff.data_type:
                risk.append("    * Field data type changed: ", style="red")
                risk.append(risky_diff.name, style="bold red")
                risk.append(
                    f" ({maybe_addition.data_type} ➜ {risky_diff.data_type})\n",
                    style="red",
                )
                continue

            if maybe_addition.is_nullable != risky_diff.is_nullable:
                risk.append("    * Field nullability changed: ", style="red")
                risk.append(risky_diff.name, style="bold red")
                risk.append(
                    f" ({maybe_addition.nullability_str()} ➜ {risky_diff.nullability_str()})\n",
                    style="red",
                )
                continue

        benign = Text()
        benign_diffs = self.benign_diffs()
        if benign_diffs or self.dapi_was_created:
            benign.append("  Low-risk changes:\n", style="bold green")
        if self.dapi_was_created:
            benign.append("    *  Model created\n", style="green")

        # NOTE: if we want to roll up the changes when there is a model creation/deletion,
        #       we can add an if statement here (if model not model created then show)
        for benign_diff in benign_diffs:
            benign.append("    * Field added: ")
            benign.append(benign_diff.name, style="bold green")
            benign.append(
                f" ({benign_diff.data_type} · {benign_diff.nullability_str()})\n",
                style="green",
            )

        # Group them vertically inside a panel
        els = [
            header,
            *([commit_subject] if commit_subject else []),
            *([commit_body] if commit_body else []),
            *([Text("\n"), risk] if risk else []),
            *([Text("\n"), benign] if benign else []),
        ]
        body = Group(*els)

        return Panel(
            body,
            padding=(0, 1),
            border_style="grey37",
        )


class OverallDapiInfo(NamedTuple):
    """Information about the changes in a single DAPI."""

    dapi_urn: str
    ordered_diff_infos: list[SingleCommitDiffInfo]
    # NOTE: this can be None if the changes were undone (changes canceled each other out)
    terminal_diff: Optional[SingleCommitDiffInfo] = None

    def total_dapi_was_created(self) -> int:
        """
        Get the total number of DAPI was created.

        NOTE: this does not check only the terminal diff since if a model was created and then deleted
              in a timeframe each change is important to call out
        """
        return len([diff for diff in self.ordered_diff_infos if diff.dapi_was_created])

    def total_dapi_was_deleted(self) -> int:
        """
        Get the total number of DAPI was deprecated.

        NOTE: this does not check only the terminal diff since if a model was deprecated and then created
              in a timeframe each change is important to call out
        """
        return len([diff for diff in self.ordered_diff_infos if diff.dapi_was_deleted])

    def total_risky_changes(self) -> int:
        """Get the total risky diffs."""
        return (
            sum(len(diff.risky_diffs()) for diff in self.ordered_diff_infos)
            + self.total_dapi_was_deleted()
        )

    def total_benign_changes(self) -> int:
        """Get the total benign diffs."""
        return (
            sum(len(diff.benign_diffs()) for diff in self.ordered_diff_infos)
            + self.total_dapi_was_created()
        )

    def render_model(self) -> None:
        """Render the model."""
        # Rule with model name as title
        rich_formatted_print(Rule(self.dapi_urn))
        if self.terminal_diff and self.terminal_diff.dapi_was_created:
            rich_formatted_print("New model")
        elif self.terminal_diff and self.terminal_diff.dapi_was_deleted:
            rich_formatted_print("Deleted model")
        else:
            rich_formatted_print("Modified model")

        risky_changes = self.total_risky_changes()
        benign_changes = self.total_benign_changes()
        total_changes = risky_changes + benign_changes
        # these can get awkward if we roll up field changes when there is a model creation/deletion -
        # so for now we just show them all until we split model risks VS field risks
        rich_formatted_print(
            f"{total_changes} total changes: {risky_changes} high-risk\n"
        )

        if self.terminal_diff:
            rich_formatted_print("Overall diff:")
            rich_formatted_print(self.terminal_diff.get_diff())
            rich_formatted_print()
        else:
            rich_formatted_print(
                "There is no overall diff. This means that the changes in this timeframe "
                "to the model canceled each other out."
            )
            rich_formatted_print()

        # Build one vertical block per commit
        for commit in self.ordered_diff_infos:
            rich_formatted_print(commit.render())

        rich_formatted_print()


######### Helpers #########


def _get_single_commit_diff_infos_by_dapi_urn(
    from_to_pairs_and_to_sha_commit_infos: list[SingleCommitCollectedFilesInfo],
    callback: Callable[[], None] = lambda: None,
) -> dict[str, list[SingleCommitDiffInfo]]:
    """Get the single commit diff infos by DAPI urn."""
    dapi_urn_to_ordered_diff_infos: Dict[str, list[SingleCommitDiffInfo]] = defaultdict(
        list
    )
    for (
        from_collected_files,
        to_collected_files,
        _,
        to_sha_commit_info,
    ) in from_to_pairs_and_to_sha_commit_infos:
        dapi_only_from_collected_files = {
            OpenDAPIEntity.DAPI: from_collected_files.get(OpenDAPIEntity.DAPI, {}),
        }
        dapi_only_to_collected_files = {
            OpenDAPIEntity.DAPI: to_collected_files.get(OpenDAPIEntity.DAPI, {}),
        }
        opendapi_file_metadatas = OpenDAPIEntityCICDMetadata.get_from_collected_files(
            integration_mode=IntegrationMode.OBSERVABILITY,
            base_collected_files=dapi_only_from_collected_files,
            head_collected_files=dapi_only_to_collected_files,
        )

        for opendapi_file_metadata in opendapi_file_metadatas:
            if not opendapi_file_metadata.entity_changed_from_base:
                continue

            to_info = (
                {
                    (field["name"], field["data_type"], field["is_nullable"])
                    for field in opendapi_file_metadata.head_collect.generated.get(
                        "fields", []
                    )
                }
                if opendapi_file_metadata.head_collect
                and opendapi_file_metadata.head_collect.generated
                else set()
            )
            from_info = (
                {
                    (field["name"], field["data_type"], field["is_nullable"])
                    for field in opendapi_file_metadata.base_collect.generated.get(
                        "fields", []
                    )
                }
                if opendapi_file_metadata.base_collect
                and opendapi_file_metadata.base_collect.generated
                else set()
            )

            # NOTE: we do merged in case the file existed at HEAD, since then head_collect would be not None
            #       even though generated would be None... cleaner
            dapi_urn = (
                opendapi_file_metadata.head_collect
                or opendapi_file_metadata.base_collect
            ).merged["urn"]
            dapi_urn_to_ordered_diff_infos[dapi_urn].append(
                SingleCommitDiffInfo(
                    additions=[
                        DapiFieldInfo(
                            name=name,
                            data_type=data_type,
                            is_nullable=is_nullable,
                            is_addition=True,
                        )
                        for name, data_type, is_nullable in to_info - from_info
                    ],
                    removals=[
                        DapiFieldInfo(
                            name=name,
                            data_type=data_type,
                            is_nullable=is_nullable,
                            is_addition=False,
                        )
                        for name, data_type, is_nullable in from_info - to_info
                    ],
                    commit_info=to_sha_commit_info,
                    dapi_was_created=opendapi_file_metadata.entity_is_new,
                    dapi_was_deleted=opendapi_file_metadata.entity_is_deprecated,
                )
            )
        callback()

    return dapi_urn_to_ordered_diff_infos


def _get_from_to_shas__timestamps(
    cwd: str,
    from_timestamp: str,
    to_timestamp: str,
) -> Optional[Tuple[str, str]]:
    """Get the from and to shas from the timestamps."""
    from_dt = None
    to_dt = None
    invalid_msgs = []

    # Try parsing both timestamps, collect all errors
    try:
        from_dt = datetime.datetime.fromisoformat(from_timestamp)
    except ValueError:
        invalid_msgs.append(
            f"Error: The from timestamp '{from_timestamp}' is not a valid ISO format."
        )

    try:
        to_dt = datetime.datetime.fromisoformat(to_timestamp)
    except ValueError:
        invalid_msgs.append(
            f"Error: The to timestamp '{to_timestamp}' is not a valid ISO format."
        )

    if invalid_msgs:
        for msg in invalid_msgs:
            rich_formatted_print(msg, style="bold red")
        raise click.Abort()

    # Check that end is after start (non-inclusive)
    if to_dt <= from_dt:
        rich_formatted_print(
            f"Error: To timestamp '{to_timestamp}' must be after from timestamp '{from_timestamp}'.",
            style="bold red",
        )
        raise click.Abort()

    try:
        with swallow_outputs():
            from_sha = get_commit_after_timestamp(cwd, from_timestamp)
            to_sha = get_commit_before_timestamp(cwd, to_timestamp)
            return from_sha, to_sha
    except BaseException:  # pylint: disable=broad-exception-caught
        rich_formatted_print(
            "Error: We were unable to derive shas from the timestamps. Exiting...",
            style="bold red",
        )
        raise click.Abort() from None


def _get_from_to_shas__shas(
    cwd: str,
    from_sha: str,
    to_sha: str,
) -> Optional[Tuple[str, str]]:
    """Get the from and to shas from the shas, ensuring from is strictly before to."""
    try:
        with swallow_outputs():
            from_commit_info = get_commit_info(cwd, from_sha)
            to_commit_info = get_commit_info(cwd, to_sha)
    except BaseException:  # pylint: disable=broad-exception-caught
        rich_formatted_print(
            "Error: We were unable to get commit information for the shas. Exiting...",
            style="bold red",
        )
        raise click.Abort() from None

    from_dt = from_commit_info.timestamp_dt()
    to_dt = to_commit_info.timestamp_dt()

    if from_dt >= to_dt:
        rich_formatted_print(
            f"Error: 'from' commit ({from_sha}, {from_dt}) must be strictly before 'to' commit ({to_sha}, {to_dt}).",
            style="bold red",
        )
        raise click.Abort()

    return from_sha, to_commit_info.sha


######### cli #########


@click.command()
@rca_options
def cli(**kwargs):  # pylint: disable=too-many-locals
    """CLI for performing root cause analysis on data model changes."""

    ##### Input validation #####

    try:

        try:
            with swallow_outputs():
                cwd = get_root_dir_validated()
        except click.Abort:
            rich_formatted_print(
                "Error: This command must be run from the root of your repository. Exiting...",
                style="bold red",
            )
            raise click.Abort() from None

        rca_type = kwargs["rca_type"]
        # NOTE: since we cannot distinguish easily if the user passed in to_timestamp or to_sha due to the defaults,
        #       to the defaults, we determine which "flow" should be used by the "from*" presence...
        #       this is a little clunky in that folks might supply a start timestamp
        #       while doing the sha flow and we don't fail, but if they gave enough to do the sha
        #       flow we will just do that, and vice versa...
        og_from_timestamp = kwargs.get("from_timestamp")
        og_to_timestamp = kwargs.get("to_timestamp")
        timestamp_present = bool(og_from_timestamp)

        og_from_sha = kwargs.get("from_sha")
        og_to_sha = kwargs.get("to_sha")
        sha_present = bool(og_from_sha)

        if not (timestamp_present or sha_present):
            rich_formatted_print(
                "Error: You must provide either timestamps or shas. Please provide one.",
                style="bold red",
            )
            raise click.Abort()

        if timestamp_present and sha_present:
            rich_formatted_print(
                "Error: You cannot provide both timestamps and shas. Please provide only one.",
                style="bold red",
            )
            raise click.Abort()

        if timestamp_present:
            if not (og_from_timestamp and og_to_timestamp):  # pragma: no cover
                rich_formatted_print(
                    "Error: You must provide both start and end timestamps.",
                    style="bold red",
                )
                raise click.Abort()

            from_sha, to_sha = _get_from_to_shas__timestamps(
                cwd, og_from_timestamp, og_to_timestamp
            )

        else:
            if not (og_from_sha and og_to_sha):  # pragma: no cover
                rich_formatted_print(
                    "Error: You must provide both from and to shas.",
                    style="bold red",
                )
                raise click.Abort()

            from_sha, to_sha = _get_from_to_shas__shas(cwd, og_from_sha, og_to_sha)

        ##### Opendapi config #####

        # NOTE: this is a hack present so that the opendapi config creation
        #       upserts this inforrmation should it not be present...
        os.environ["WOVEN_INTEGRATION_MODE"] = IntegrationMode.OBSERVABILITY.value

        rich_formatted_print(
            "\n\nWoven.dev gives you the visibility, controls, and tools needed to bridge the application "
            "engineering-to-data engineering divide. Learn more at https://woven.dev.\n"
        )

        try:
            # NOTE: while using the existing opendapi config is nice, it is sorta clunky
            #       in that the model allowlist etc. is currently set in the opendapi config.
            #       what that means is that if there is an opendapi config present,
            #       the user is not able to specify a model allowlist, etc., in addition to us
            #       likely doing more validation than they need (other integration, etc.)...
            #       punting on this for now, but something to consider
            #       (do we set envvars? do we expect them to create a temp minimal opendapi config anyway? etc.)
            with swallow_outputs():
                opendapi_config = get_opendapi_config_from_root(
                    local_spec_path=kwargs.get("local_spec_path"),
                    validate_config=True,
                )
            rich_formatted_print(
                "We see that you already have an opendapi config present - great! Let us begin with our analysis."
            )

        # the errors raised from get_opendapi_config_from_root
        except (FileNotFoundError, click.Abort):
            rich_formatted_print(
                "We see that you do not have an opendapi config present - let's walk through the onboarding "
                "flow so you can get started on the analysis.\n"
            )
            opendapi_onboarding_info = (
                InteractiveIntegrationOnboardBase.onboard_opendapi_config(
                    cwd, render=kwargs["render"]
                )
            )

            try:
                with swallow_outputs():
                    opendapi_config = opendapi_onboarding_info.to_opendapi_config(
                        root_dir=cwd,
                    )
            except BaseException:  # pylint: disable=broad-exception-caught
                rich_formatted_print(
                    "Error: We were unable to create an opendapi config from the onboarding info. Exiting...",
                    style="bold red",
                )
                raise click.Abort() from None

        try:
            runtime = opendapi_config.assert_runtime_exists(kwargs["runtime"])
        except RuntimeError:
            rich_formatted_print(
                (
                    f"Error: We see that you do not have a runtime called {kwargs['runtime']} - "
                    "please provide a valid runtime, or update your opendapi "
                    "config to include the runtime.\nExiting...",
                ),
                style="bold red",
            )
            raise click.Abort() from None

        ##### Get ancestry path #####

        with swallow_outputs():
            from_to_shas = (
                [from_sha, to_sha]
                if rca_type is RCAType.TERMINAL_COMMITS
                else get_ancestry_path(cwd, from_sha, to_sha)
            )

        if timestamp_present:
            if rca_type is RCAType.TERMINAL_COMMITS:
                rich_formatted_print(
                    "We will be analyzing only the terminal commits in the ancestry path found "
                    f"between the timestamps {og_from_timestamp} and {og_to_timestamp}."
                )
            else:
                rich_formatted_print(
                    f"{len(from_to_shas)} commits found between the timestamps "
                    f"{og_from_timestamp} and {og_to_timestamp}."
                )

        elif sha_present:
            to_sha_str = to_sha if og_to_sha != "HEAD" else f"HEAD ({to_sha})"
            if rca_type is RCAType.TERMINAL_COMMITS:
                rich_formatted_print(
                    "We will be analyzing only the terminal commits supplied."
                )
            else:
                rich_formatted_print(
                    f"{len(from_to_shas)} commits found between the shas {from_sha} and {to_sha_str}."
                )

        ##### Collect data model metadata #####

        rich_formatted_print("Gathering data model metadata...")
        ordered_collected_files = []
        ordered_commit_infos = []
        with Progress(
            BarColumn(bar_width=50),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("", total=len(from_to_shas))
            for commit_sha in from_to_shas:
                with swallow_outputs():
                    change_trigger_event = ChangeTriggerEvent(
                        where="local",
                        before_change_sha=commit_sha,
                        # NOTE: this is sort of a hack, but it really does not matter, since
                        #       below we are just using the commit sha at BASE when we collect,
                        #       so after_change_sha being the same is okay
                        after_change_sha=commit_sha,
                    )
                    ordered_collected_files.append(
                        # NOTE: this technically runs for non-dapis as well, and is therefore
                        #       a candidate for a performance opt in the future...
                        collect_collected_files(
                            # we pass in the opendapi config since it is not likely to exist
                            opendapi_config,
                            change_trigger_event=change_trigger_event,
                            commit_type=CommitType.BASE,
                            runtime_skip_generation=False,
                            dbt_skip_generation=False,
                            # we only need the ORM related info, so we use this minimal schema
                            minimal_schemas=server_sync_minimal_schemas(),
                            runtime=runtime,
                            # we will
                            commit_already_checked_out=False,
                            kwargs=kwargs,
                        )
                    )
                    ordered_commit_infos.append(get_commit_info(cwd, commit_sha))
                progress.advance(task)
                progress.refresh()

        ##### Analyze data model changes #####

        from_to_pairs_and_to_sha_commit_infos = [
            SingleCommitCollectedFilesInfo(*raw_tup)
            for raw_tup in zip(
                ordered_collected_files[:-1],
                ordered_collected_files[1:],
                from_to_shas[:-1],
                ordered_commit_infos[1:],
            )
        ]
        rich_formatted_print("\nAnalyzing data model changes...")
        with Progress(
            BarColumn(bar_width=50),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            # there are n-1 sequential pairs, + 1 terminal pair = n
            task = progress.add_task(
                "Analyzing data model changes...", total=len(from_to_shas)
            )
            dapi_urn_to_ordered_diff_infos = _get_single_commit_diff_infos_by_dapi_urn(
                from_to_pairs_and_to_sha_commit_infos,
                callback=lambda: (progress.advance(task), progress.refresh()),
            )
            terminal_urn_to_terminal_diff_info = {
                # for each dapi we compare only the terminal commits, so this list is
                # always length 1
                dapi_urn: single_commit_infos[0]
                for dapi_urn, single_commit_infos in _get_single_commit_diff_infos_by_dapi_urn(
                    [
                        SingleCommitCollectedFilesInfo(
                            ordered_collected_files[0],
                            ordered_collected_files[-1],
                            from_to_shas[0],
                            ordered_commit_infos[-1],
                        )
                    ],
                    callback=lambda: (progress.advance(task), progress.refresh()),
                ).items()
            }

        ordered_overall_dapi_infos = sorted(
            [
                OverallDapiInfo(
                    dapi_urn,
                    ordered_diff_infos,
                    terminal_urn_to_terminal_diff_info.get(dapi_urn),
                )
                for dapi_urn, ordered_diff_infos in dapi_urn_to_ordered_diff_infos.items()
            ],
            key=lambda x: x.dapi_urn,
        )

        ##### Render summary #####

        individual_changed_dapis = len(ordered_overall_dapi_infos)
        total_risky_changes = sum(
            overall_dapi_info.total_risky_changes()
            for overall_dapi_info in ordered_overall_dapi_infos
        )
        total_benign_changes = sum(
            overall_dapi_info.total_benign_changes()
            for overall_dapi_info in ordered_overall_dapi_infos
        )
        total_changes = total_risky_changes + total_benign_changes
        total_days_between_commits = (
            ordered_commit_infos[-1].timestamp_dt()
            - ordered_commit_infos[0].timestamp_dt()
        ).days + 1
        # round up
        average_changes_per_day = (
            total_changes + total_days_between_commits - 1
        ) / total_days_between_commits

        rich_formatted_print("\n\nSummary:")
        rich_formatted_print(f"- {len(from_to_shas)} commits analyzed")
        # NOTE: the risks currently are not split between model and fields, and the counts can get weird
        #       if we roll up changes (do not display field level ones when a model is created/deleted) -
        #       or if a model is created/deleted/created (there are multiple model changes
        #       but its net one model changed).. so for now we just show them all.
        #       It makes the average seem higher possibly (its fields + model creation/deletion changes),
        #       but that is the most coherent thing for now - the other ones make the counts sorta nonsensical...
        rich_formatted_print(f"- {individual_changed_dapis} unique models changed")
        rich_formatted_print(
            f"- {total_changes} total changes: {total_risky_changes} high-risk"
        )
        rich_formatted_print(
            f"- {total_days_between_commits}-day change velocity: {average_changes_per_day} changes per day (avg)\n"
        )

        for overall_dapi_info in ordered_overall_dapi_infos:
            overall_dapi_info.render_model()

    except (click.Abort, KeyboardInterrupt):
        raise

    except BaseException:  # pylint: disable=broad-exception-caught
        rich_formatted_print(
            "\nAn unexpected error occurred.",
            style="bold red",
        )
        raise click.Abort() from None
