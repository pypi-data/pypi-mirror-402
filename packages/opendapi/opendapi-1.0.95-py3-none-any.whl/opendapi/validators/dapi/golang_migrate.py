"""Golang migrate DAPI validator module"""

import os
import re
from dataclasses import dataclass
from typing import List, Tuple, Type

from opendapi.adapters.file import find_files_with_suffix
from opendapi.config import get_project_path_from_full_path
from opendapi.defs import ORMIntegration
from opendapi.models import ProjectConfig
from opendapi.validators.dapi.base.ddl import DdlBasedDapiValidator, DdlBasedProjectInfo


@dataclass
class GolangMigrateProjectInfo(DdlBasedProjectInfo):
    """Data class for a golang migrate project information"""

    integration: ORMIntegration = ORMIntegration.GOLANG_MIGRATE

    AUDITING_TABLE_NAMES = []
    MIGRATION_FILE_SUFFIXES = (".up.sql",)

    def _get_ddl__go(self, filename: str) -> str:
        """Get the DDL from a go file."""
        raise NotImplementedError(
            "Maintainers do not recommend this, as its obtuse, with a go binary required to be run"
        )

    def _get_ddl__sql(self, filename: str) -> str:
        """Get the DDL from a sql file."""
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_version_from_filename(self, filename: str) -> Tuple[int, str]:
        """
        Extract the numeric version prefix from a migration filename.

        Supports golang-migrate naming patterns:
        - Zero-padded sequential: "000001_initial.up.sql" -> (1, ...)
        - Non-zero-padded sequential: "10_initial.up.sql" -> (10, ...)
        - Timestamp-based: "20240101000000_initial.up.sql" -> (20240101000000, ...)

        Returns a tuple of (version_number, filename) for sorting.
        If no numeric prefix is found, returns (0, filename) to fall back to lexicographic sorting.

        Examples:
        - "000001_initial.up.sql" -> (1, "000001_initial.up.sql")
        - "1_initial.up.sql" -> (1, "1_initial.up.sql")
        - "10_add_indexes.up.sql" -> (10, "10_add_indexes.up.sql")
        - "20240101000000_initial.up.sql" -> (20240101000000, "20240101000000_initial.up.sql")
        - "initial.up.sql" -> (0, "initial.up.sql")
        """
        # Match numeric prefix at the start of the filename (before first underscore or dot)
        match = re.match(r"^(\d+)", filename)
        if match:
            return (int(match.group(1)), filename)
        return (0, filename)

    def _get_ddl(self) -> str:
        """
        Get the DDL from the golang migrations.
        We will just parse the sql files for now.

        Migration files are sorted by their numeric prefix to ensure
        they are processed in the correct order, matching how golang-migrate
        applies migrations.
        """

        migration_files = [
            file
            for file in os.listdir(self.artifact_full_path)
            if file.endswith(self.MIGRATION_FILE_SUFFIXES)
        ]

        # Sort by numeric prefix (extracted from filename) to ensure correct order
        sorted_files = sorted(migration_files, key=self._extract_version_from_filename)

        total_ddl_dml = []
        for migration_filename in sorted_files:
            migration_file_path = os.path.join(
                self.artifact_full_path, migration_filename
            )
            # Only process SQL files; .up.go files are not supported yet
            if migration_filename.endswith(".sql"):
                total_ddl_dml.append(self._get_ddl__sql(migration_file_path))

        return "\n".join(total_ddl_dml)


class GolangMigrateDapiValidator(DdlBasedDapiValidator[GolangMigrateProjectInfo]):
    """
    Validator class for DAPI files created for golang-migrate datasets
    """

    INTEGRATION_NAME: ORMIntegration = ORMIntegration.GOLANG_MIGRATE
    # Lookup files to identify Go services (similar to package.json for JS projects)
    GO_SERVICE_INDICATORS = ["main.go", "go.mod"]
    # golang migration files are located in the migrations directory
    DEFAULT_ARTIFACT_PATH = "migrations"
    PROJECT_INFO_TYPE: Type[GolangMigrateProjectInfo] = GolangMigrateProjectInfo

    def get_all_projects(self) -> List[GolangMigrateProjectInfo]:
        """
        Get all projects by:
        1. Finding Go services (identified by main.go or go.mod files)
        2. Looking for migrations directories within those Go services
        """
        artifact_path = (
            self.integration_config.artifact_path or self.DEFAULT_ARTIFACT_PATH
        )

        # Find all Go services by looking for main.go or go.mod files
        go_service_dirs = set()
        for indicator in self.GO_SERVICE_INDICATORS:
            indicator_files = find_files_with_suffix(
                self.root_dir,
                [f"/{indicator}"],
                exclude_dirs=self.EXCLUDE_DIRS_FOR_AUTODISCOVERY,
            )
            for indicator_file in indicator_files:
                # Get the directory containing the indicator file (the Go service)
                go_service_dir = os.path.dirname(indicator_file)
                go_service_dirs.add(os.path.abspath(go_service_dir))

        # For each Go service, look for a migrations directory
        migrations_dirs = set()
        for go_service_dir in go_service_dirs:
            migrations_dir = os.path.join(go_service_dir, artifact_path)
            if os.path.isdir(migrations_dir):
                migrations_dirs.add(os.path.abspath(migrations_dir))

        projects = []
        for migrations_dir in sorted(migrations_dirs):
            # Get the project path (parent of migrations directory, which is the Go service)
            project_full_path = os.path.dirname(migrations_dir)
            project_path = get_project_path_from_full_path(
                self.root_dir, project_full_path
            )

            override = ProjectConfig(
                project_path=project_path,
                artifact_path=artifact_path,
                dialect=self.integration_config.dialect,
                include_models=self.integration_config.include_models,
            )

            projects.append(self.get_project(override))

        return projects
