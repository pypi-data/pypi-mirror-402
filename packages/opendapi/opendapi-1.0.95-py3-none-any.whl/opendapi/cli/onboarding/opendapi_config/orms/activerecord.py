"""
Interactive integration onboarding for ActiveRecord
"""

import os

from opendapi.cli.common import rich_formatted_print
from opendapi.defs import ORMIntegration

from ..base import InteractiveIntegrationOnboardBase
from ..defs import IncludeAllRequiresDialect


class ActiveRecordInteractiveIntegrationOnboard(
    InteractiveIntegrationOnboardBase,
    orm_integration=ORMIntegration.ACTIVERECORD,
    can_include_all=True,
    include_all_requires_dialect=IncludeAllRequiresDialect.MAYBE,
    explain_include_all_dialect=(
        "If you use .sql files instead of schema.rb files, "
        "you must set the dialect so the DDL parsing works correctly."
    ),
    explain_project_path="This is the service/library/project etc. for which you want to run RCA on.",
    explain_artifact_path=(
        "Please provide the path, relative from root, of your schema dump file, "
        "usually named schema.rb or structure.sql."
    ),
):
    """
    Interactive integration onboarding for ActiveRecord
    """

    @classmethod
    def _artifact_path_requires_dialect(cls, artifact_path: str) -> bool:
        """
        Determine if the artifact path requires a dialect
        """
        return artifact_path.endswith(".sql")

    @classmethod
    def _validate_artifact_path(cls, artifact_path: str) -> bool:
        """
        Validate the artifact path
        """
        if not artifact_path.endswith((".sql", ".rb")):
            rich_formatted_print(
                f"Invalid artifact path {artifact_path}.", style="bold red"
            )
            return False

        if not os.path.isfile(artifact_path):
            rich_formatted_print(
                f"Artifact path {artifact_path} does not exist.", style="bold red"
            )
            return False

        return True
