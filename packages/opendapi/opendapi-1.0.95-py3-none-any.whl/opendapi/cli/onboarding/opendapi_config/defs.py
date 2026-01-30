"""Definitions for onboarding opendapi config"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from opendapi.config import OpenDAPIConfig
from opendapi.defs import IntegrationMode, ORMIntegration, SqlDialect


class IncludeAllRequiresDialect(Enum):
    """
    Enum to determine if a sql dialect is required for a given integration/project
    """

    ALWAYS = "always"
    NEVER = "never"
    MAYBE = "maybe"


@dataclass
class OnboardingOpendapiConfigInfo:
    """
    Information about the opendapi config to be created

    NOTE: this is more or less just a better opendapi config object -
          we might consider formalizing this in the future
    """

    org_name: str
    org_email_domain: str
    repo_urn: str
    mainline_branch_name: str
    integration_mode: IntegrationMode = IntegrationMode.OBSERVABILITY
    integrations: list[SingleIntegrationConfig] = field(default_factory=list)
    # NOTE: how to keep this in sync with what we render?
    schema: str = "https://opendapi.org/spec/0-0-3/opendapi.config.json"

    def for_config(self) -> dict:
        """
        Convert the onboarding opendapi config info to a dictionary
        """
        return {
            "schema": self.schema,
            "organization": {
                "name": self.org_name,
                "email_domain": self.org_email_domain,
            },
            "repository": {
                "urn": self.repo_urn,
                "mainline_branch": self.mainline_branch_name,
                "integration_mode": self.integration_mode.value,
            },
            "dapis": {
                "runtimes": {
                    "DEFAULT": {
                        "integrations": [
                            integration.for_config()
                            for integration in self.integrations
                        ],
                    },
                },
            },
        }

    def to_opendapi_config(
        self, root_dir: str, validate_config: bool = True
    ) -> OpenDAPIConfig:
        """
        Convert the onboarding opendapi config info to an opendapi config object
        """
        config = OpenDAPIConfig(
            root_dir=root_dir,
            json_config=self.for_config(),
        )
        if validate_config:
            config.validate()
        return config


@dataclass
class SingleProjectConfig:
    """
    Information about a single project to be onboarded
    """

    project_path: str
    artifact_path: str
    dialect: Optional[SqlDialect] = None
    model_allowlist: Optional[list[str]] = None

    def for_config(self) -> dict:
        """
        Convert the project config to a dictionary
        """
        return {
            "project_path": self.project_path,
            "artifact_path": self.artifact_path,
            **({"dialect": self.dialect.value} if self.dialect else {}),
            **(
                {"model_allowlist": self.model_allowlist}
                if self.model_allowlist
                else {}
            ),
        }


@dataclass
class SingleIntegrationConfig:
    """
    Information about a single integration to be onboarded
    """

    integration: ORMIntegration
    include_all: bool = True
    artifact_path: Optional[str] = None
    dialect: Optional[SqlDialect] = None
    model_allowlist: Optional[list[str]] = None
    projects: list[SingleProjectConfig] = field(default_factory=list)

    def for_config(self) -> dict:
        """
        Convert the integration config to a dictionary
        """
        return {
            "type": self.integration.value,
            "projects": {
                "include_all": self.include_all,
                **({"artifact_path": self.artifact_path} if self.artifact_path else {}),
                **({"dialect": self.dialect.value} if self.dialect else {}),
                **(
                    {"model_allowlist": self.model_allowlist}
                    if self.model_allowlist
                    else {}
                ),
                "overrides": [project.for_config() for project in self.projects],
            },
        }
