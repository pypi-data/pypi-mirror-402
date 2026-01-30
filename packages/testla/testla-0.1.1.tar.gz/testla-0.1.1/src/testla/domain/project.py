"""Project domain model.

A project represents a repository/codebase that contains test cases.
Projects are the top-level organizational unit in Testla.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import NewType
from uuid import UUID, uuid4

ProjectId = NewType("ProjectId", UUID)


@dataclass(frozen=True)
class ProjectSettings:
    """
    Value object for project-level configuration.

    These settings can be overridden in .testla/config.yaml
    """

    default_priority: str = "medium"
    case_id_prefix: str = "TC"
    case_id_digits: int = 3


@dataclass
class Project:
    """
    Aggregate root for projects.

    A project maps to a git repository and contains test cases.
    The project entity in the backend stores metadata about the
    repository and settings, while the actual test cases live
    in the repository itself.
    """

    id: ProjectId
    name: str
    description: str = ""
    repo_url: str | None = None
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        name: str,
        *,
        description: str = "",
        repo_url: str | None = None,
    ) -> "Project":
        """
        Factory method for creating new projects.

        :param name: Project name
        :param description: Project description
        :param repo_url: URL to the git repository
        :return: New Project instance
        """
        now = datetime.now(UTC)
        return cls(
            id=ProjectId(uuid4()),
            name=name,
            description=description,
            repo_url=repo_url,
            created_at=now,
            updated_at=now,
        )

    def update_repo_url(self, repo_url: str) -> None:
        """
        Update the repository URL.

        :param repo_url: New repository URL
        """
        self.repo_url = repo_url
        self.updated_at = datetime.now(UTC)

    def update_settings(self, settings: ProjectSettings) -> None:
        """
        Update project settings.

        :param settings: New settings
        """
        self.settings = settings
        self.updated_at = datetime.now(UTC)
