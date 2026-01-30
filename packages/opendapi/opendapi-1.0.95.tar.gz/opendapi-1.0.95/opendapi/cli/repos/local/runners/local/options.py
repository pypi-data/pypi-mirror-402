"""
Houses options for invocation of a local runner of a local repo,
in addition for the change_trigger_event construction
"""

from datetime import datetime, timezone

import click

from opendapi.adapters.git import ChangeTriggerEvent
from opendapi.cli.options import BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION

from .defs import RCAType


def construct_change_trigger_event(kwargs: dict) -> ChangeTriggerEvent:
    """
    Construct the ChangeTriggerEvent given that this a local repo and
    a local runner
    """
    return ChangeTriggerEvent(
        where="local",
        before_change_sha=(
            kwargs.get(BASE_COMMIT_SHA_PARAM_NAME_WITH_OPTION.name)
            or kwargs["mainline_branch_name"]
        ),
        after_change_sha="HEAD",
    )


def _validate_rca_type(ctx, param, value):  # pylint: disable=unused-argument
    try:
        return RCAType(value)
    except ValueError:  # pragma: no cover
        raise click.BadParameter(f"Invalid RCA type: {value}") from None


def rca_options(func: click.core.Command) -> click.core.Command:
    """
    Set of click options required for the RCA command
    """
    # NOTE: we analyze commits rn - not current state - we can expand to that later...
    options = [
        click.option(
            "--rca-type",
            type=click.Choice([e.value for e in RCAType]),
            default=RCAType.CONSECUTIVE_COMMITS.value,
            help=(
                "The type of RCA to perform. Consecutive-commits will analyze each consecutive pair of "
                "commits in the ancestry path (including the terminal commits), "
                "while terminal-commits will analyze only the terminal commits."
            ),
            callback=_validate_rca_type,
        ),
        click.option(
            "--from-sha",
            type=str,
            help="The SHA of the commit to start analyzing from (inclusive).",
        ),
        click.option(
            "--to-sha",
            type=str,
            default="HEAD",
            help="The SHA of the commit to stop analyzing at (inclusive).",
        ),
        click.option(
            "--from-timestamp",
            type=str,
            help="The timestamp to begin looking for commits from (inclusive).",
        ),
        click.option(
            "--to-timestamp",
            type=str,
            default=datetime.now(timezone.utc).isoformat(),
            help="The timestamp to stop looking for commits at (inclusive).",
        ),
        click.option(
            "--render",
            type=bool,
            default=False,
            help="Whether to render the opendapi_config file",
        ),
        click.option(
            "--runtime",
            type=str,
            default="DEFAULT",
            help="The runtime in your opendapi_config to use for the analysis",
        ),
    ]
    for option in reversed(options):
        func = option(func)
    return func
