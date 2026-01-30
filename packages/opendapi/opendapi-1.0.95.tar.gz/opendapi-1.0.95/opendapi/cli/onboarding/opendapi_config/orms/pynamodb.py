"""
Interactive integration onboarding for PynamoDB
"""

import importlib

from opendapi.cli.common import rich_formatted_print
from opendapi.defs import ORMIntegration

from ..base import InteractiveIntegrationOnboardBase
from ..defs import IncludeAllRequiresDialect


class PynamoDBInteractiveIntegrationOnboard(
    InteractiveIntegrationOnboardBase,
    orm_integration=ORMIntegration.PYNAMODB,
    can_include_all=False,
    include_all_requires_dialect=IncludeAllRequiresDialect.NEVER,
    explain_project_path="This is the service/library/project etc. for which you want to run RCA on.",
    explain_artifact_path=(
        "The artifact path points the CLI at the base class used for declaring PynamoDB models. "
        "The format is <module_name>:<class_name> - i.e. my_server.models.base:BaseModel"
    ),
):
    """
    Interactive integration onboarding for PynamoDB
    """

    @classmethod
    def _validate_artifact_path(cls, artifact_path: str) -> bool:
        """
        Validate the artifact path
        """
        els = artifact_path.split(":")
        if len(els) != 2:
            rich_formatted_print(
                (
                    f"Invalid artifact path {artifact_path}. "
                    "The format is <module_name>:<class_name> - i.e. my_server.models.base:BaseModel"
                ),
                style="bold red",
            )
            return False

        module_name, class_name = els
        try:
            importlib.import_module(module_name)
        except ImportError:
            rich_formatted_print(
                f"Module {module_name} not found. Please ensure the module is installed.",
                style="bold red",
            )
            return False

        # NOTE: maybe check superclass being pynamodb.models.Model? this is sorta weird since idk if there
        #       are other patterns that folks use to instantiate, and idk for certain that
        #       the import is there - we could try to import here since this is a runtime integration?
        #       or get the file info from the superclass? but what if they do multiple inheritence?
        #       maybe this is overkill... something to consider...
        try:
            getattr(importlib.import_module(module_name), class_name)
        except AttributeError:
            rich_formatted_print(
                (
                    f"Class {class_name} not found in module {module_name}. "
                    "Please ensure the class is defined in the module."
                ),
                style="bold red",
            )
            return False

        return True
