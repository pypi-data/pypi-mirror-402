"""
Base class for interactive integration onboarding
"""

from __future__ import annotations

import os
import re
from typing import ClassVar, Optional

from rich.rule import Rule

from opendapi.adapters.git import get_mainline_branch_name_from_origin
from opendapi.cli.common import (
    rich_formatted_print,
    rich_general_input,
    rich_yes_no_input,
)
from opendapi.defs import (
    CONFIG_FILEPATH_FROM_ROOT_DIR,
    ORMIntegration,
    RepoType,
    SqlDialect,
)
from opendapi.templates import (
    INTERACTIVE_ONBOARDING_OPENDAPI_CONFIG_TEMPLATE_PATH,
    render_template_file,
)
from opendapi.validators.dapi import get_validator_for_integration
from opendapi.validators.defs import IntegrationType

from .defs import (
    IncludeAllRequiresDialect,
    OnboardingOpendapiConfigInfo,
    SingleIntegrationConfig,
    SingleProjectConfig,
)


class InteractiveIntegrationOnboardBase:
    """Base class for interactive integration onboarding"""

    _REGISTRY: ClassVar[
        dict[ORMIntegration, type[InteractiveIntegrationOnboardBase]]
    ] = {}

    def __init_subclass__(
        cls,
        orm_integration: ORMIntegration,
        can_include_all: bool,
        include_all_requires_dialect: Optional[IncludeAllRequiresDialect] = None,
        explain_include_all_dialect: Optional[str] = None,
        explain_project_path: Optional[str] = None,
        explain_artifact_path: Optional[str] = None,
    ):
        # NOTE: in the future consider testing for exhaustion (other than DBT)
        if (
            orm_integration in InteractiveIntegrationOnboardBase._REGISTRY
        ):  # pragma: no cover
            raise ValueError(f"Integration {orm_integration} already registered")

        super().__init_subclass__()

        cls.ORM_INTEGRATION = orm_integration
        cls.CAN_INCLUDE_ALL = can_include_all
        cls.INCLUDE_ALL_REQUIRES_DIALECT = include_all_requires_dialect
        cls.EXPLAIN_INCLUDE_ALL_DIALECT = explain_include_all_dialect
        cls.EXPLAIN_PROJECT_PATH = explain_project_path
        cls.EXPLAIN_ARTIFACT_PATH = explain_artifact_path

        InteractiveIntegrationOnboardBase._REGISTRY[orm_integration] = cls

    @classmethod
    def _artifact_path_requires_dialect(
        cls, artifact_path: str  # pylint: disable=unused-argument
    ) -> bool:
        return False  # pragma: no cover

    @classmethod
    def _validate_artifact_path(
        cls, artifact_path: str  # pylint: disable=unused-argument
    ) -> bool:
        return True  # pragma: no cover

    @classmethod
    def _collect_artifact_path(cls) -> str:
        rich_formatted_print(cls.EXPLAIN_ARTIFACT_PATH, style="dim italic")
        artifact_path = rich_general_input(
            "Please enter the artifact path",
        )
        while not cls._validate_artifact_path(artifact_path):
            artifact_path = rich_general_input(
                "Invalid artifact path. Please enter a valid artifact path",
            )

        return artifact_path

    @classmethod
    def _collect_dialect(cls) -> SqlDialect:
        dialect = rich_general_input(
            "Please enter the dialect of the database you want to use for the projects",
            choices=[dialect.value for dialect in SqlDialect],
        )
        while True:
            try:
                return SqlDialect(dialect)
            except ValueError:
                dialect = rich_general_input(
                    "Invalid dialect. Please enter a valid dialect",
                    choices=[dialect.value for dialect in SqlDialect],
                )

    @classmethod
    def _collect_model_allowlist(cls) -> Optional[list[str]]:
        should_collect_model_allowlist = rich_yes_no_input(
            "Would you like to prune the analysis to only focus on specific models?",
        )
        # NOTE: for now we assume that we only care about direct model names and no exclusions
        if should_collect_model_allowlist:
            comma_separated_model_names = rich_general_input(
                "Please enter a case-sensitive comma-separated list of model names to focus on"
            )
            # rich does external trimming, but not internal, so we do so
            return [
                model_name.strip()
                for model_name in comma_separated_model_names.split(",")
            ]

        return None

    @classmethod
    def _onboard_single_project(cls) -> SingleProjectConfig:

        rich_formatted_print(cls.EXPLAIN_PROJECT_PATH, style="dim italic")
        project_path = rich_general_input(
            "Please enter the project path, relative from the repository root"
        )
        if not project_path.startswith("/"):
            project_path = f"/{project_path}"

        artifact_path = cls._collect_artifact_path()

        project_info = SingleProjectConfig(
            project_path=project_path,
            artifact_path=artifact_path,
        )

        if cls._artifact_path_requires_dialect(artifact_path):
            rich_formatted_print(
                f"The artifact path {artifact_path} requires specifying a dialect."
            )
            project_info.dialect = cls._collect_dialect()

        model_allowlist = cls._collect_model_allowlist()
        if model_allowlist:
            project_info.model_allowlist = model_allowlist

        return project_info

    @classmethod
    def _needs_runtime(cls) -> bool:
        return (
            get_validator_for_integration(cls.ORM_INTEGRATION).INTEGRATION_TYPE
            is IntegrationType.RUNTIME
        )

    @classmethod
    def onboard(cls) -> SingleIntegrationConfig:
        """
        Onboard a single integration
        """

        integration_config = SingleIntegrationConfig(
            integration=cls.ORM_INTEGRATION,
        )

        rich_formatted_print(Rule(f"Onboarding {cls.ORM_INTEGRATION.value}"))

        # NOTE: given most rca invocations will be without an opendapi config, this is the most natural place
        #       to prompt for this, but we might consider moving this to the outermost level in the future
        if cls._needs_runtime():
            rich_formatted_print(
                (
                    "NOTE: This integration requires entering a valid runtime. "
                    "Please make sure that you invoke this command from within a valid runtime environment/venv/etc."
                ),
                style="bold red",
            )

        if cls.CAN_INCLUDE_ALL:

            integration_config.include_all = rich_yes_no_input(
                "This integration supports auto discovery of projects. Do you want to include all projects?",
            )

            if integration_config.include_all:
                rich_formatted_print("Great! We will include all projects.")
                if (
                    cls.INCLUDE_ALL_REQUIRES_DIALECT is IncludeAllRequiresDialect.ALWAYS
                ):  # pragma: no cover
                    dialect = cls._collect_dialect()
                    integration_config.dialect = dialect

                elif (
                    cls.INCLUDE_ALL_REQUIRES_DIALECT is IncludeAllRequiresDialect.MAYBE
                ):
                    rich_formatted_print(
                        f"[dim italic]{cls.EXPLAIN_INCLUDE_ALL_DIALECT}[/dim italic]"
                    )
                    should_collect_dialect = rich_yes_no_input(
                        "Is collecting a dialect required?",
                    )
                    if should_collect_dialect:
                        dialect = cls._collect_dialect()
                        integration_config.dialect = dialect

                model_allowlist = cls._collect_model_allowlist()
                if model_allowlist:
                    integration_config.model_allowlist = model_allowlist

                return integration_config

            rich_formatted_print("We will only onboard specific projects.")

        else:
            integration_config.include_all = False
            rich_formatted_print(
                "This integration does not support auto discovery of projects. "
                "We will therefore onboard one project at a time."
            )

        should_onboard_another_project = True
        project_paths = set()
        while should_onboard_another_project:
            project_config = cls._onboard_single_project()
            if project_config.project_path in project_paths:
                rich_formatted_print(
                    f"Project path {project_config.project_path} already onboarded."
                    "Please enter a different project path."
                )
                continue

            project_paths.add(project_config.project_path)
            integration_config.projects.append(project_config)
            should_onboard_another_project = rich_yes_no_input(
                "Would you like to onboard another project for this integration?",
            )

        rich_formatted_print(Rule(f"Done onboarding {cls.ORM_INTEGRATION.value}"))
        return integration_config

    @staticmethod
    def onboard_opendapi_config(
        cwd: str,
        render: bool = False,
    ) -> OnboardingOpendapiConfigInfo:
        """
        Onboard the opendapi config
        """

        rich_formatted_print(Rule())

        if render:
            org_name = rich_general_input("Please enter the name of your organization")
            # NOTE: what to do for local?
            org_email_domain = rich_general_input(
                "Please enter the email domain of your organization"
            )
            # NOTE: this is from the opendapi config spec - how do we keep it in sync
            while not re.match(
                r"^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$", org_email_domain
            ):
                org_email_domain = rich_general_input(
                    "Invalid email domain. Please enter a valid email domain",
                )

            repo_type = RepoType(
                rich_general_input(
                    "Please select the type of repository you are using",
                    choices=[repo_type.value for repo_type in RepoType],
                )
            )
            # NOTE: what to do for local?
            remote_org_name = rich_general_input(
                "Please enter the name of your remote organization. If you are using a local repository, "
                "please enter the path to the repository"
            )
            remote_repo_name = rich_general_input(
                "Please enter the fully qualified name of your repository (org/repo). "
                "If you are using a local repository, please enter the path to the repository"
            )
            repo_urn = repo_type.create_repo_urn(
                remote_org_name=remote_org_name,
                remote_repo_name=remote_repo_name,
            )
            mainline_branch_name = rich_general_input(
                "Please enter the name of your mainline branch (trunk, main, master, etc.)"
            )

        else:
            org_name = "org"
            org_email_domain = "org.com"
            repo_urn = "remote:org/repo"
            try:
                mainline_branch_name = get_mainline_branch_name_from_origin(cwd)
            except Exception:  # pylint: disable=broad-exception-caught
                mainline_branch_name = rich_general_input(
                    "Please enter the name of your mainline branch (trunk, main, master, etc.)"
                )

        opendapi_config_onboarding_info = OnboardingOpendapiConfigInfo(
            org_name=org_name,
            org_email_domain=org_email_domain,
            repo_urn=repo_urn,
            mainline_branch_name=mainline_branch_name,
        )

        remaining_integrations = sorted(
            [
                ormi.value
                # NOTE: if there is an integration that we do not support during interactive onboarding
                #       it just will not be included in the registry - so no need to filter
                for ormi in InteractiveIntegrationOnboardBase._REGISTRY
            ]
        )

        first_pass = True
        while remaining_integrations:

            # we always require at least one, so we only allow for exiting after the first pass
            if first_pass:
                integration = rich_general_input(
                    "\nPlease select the integration you want to onboard",
                    choices=remaining_integrations,
                )
                first_pass = False

            else:
                integration = rich_general_input(
                    "\nPlease select the integration you want to onboard (Enter to finish)",
                    choices=remaining_integrations,
                    default="",
                )

            if not integration:
                break

            integration_onboarder = InteractiveIntegrationOnboardBase._REGISTRY[
                ORMIntegration(integration)
            ]
            opendapi_config_onboarding_info.integrations.append(
                integration_onboarder.onboard()
            )
            remaining_integrations.remove(integration)

        if render:
            rich_formatted_print(
                "\nGreat! We have onboarded all integrations. We will now render the "
                "opendapi config file and save it to the repository root."
            )
            InteractiveIntegrationOnboardBase.render_opendapi_config(
                cwd=cwd,
                opendapi_config_onboarding_info=opendapi_config_onboarding_info,
            )
        else:
            rich_formatted_print("\nGreat! We have onboarded all integrations.")

        rich_formatted_print(Rule())

        return opendapi_config_onboarding_info

    @staticmethod
    def render_opendapi_config(
        cwd: str, opendapi_config_onboarding_info: OnboardingOpendapiConfigInfo
    ) -> None:
        """Render the opendapi config"""
        render_template_file(
            output_filepath=os.path.join(cwd, CONFIG_FILEPATH_FROM_ROOT_DIR),
            template_path=INTERACTIVE_ONBOARDING_OPENDAPI_CONFIG_TEMPLATE_PATH,
            template_input=opendapi_config_onboarding_info,
        )
