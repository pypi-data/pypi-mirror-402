"""Module to interact with Azure DevOps repositories."""
# Copyright (c) 2023, Fred Stober
# SPDX-License-Identifier: MIT

from collections.abc import Iterator
from typing import TypeAlias
from uuid import UUID

from pydantic import BaseModel, Field, NonNegativeInt

from pyado.api_call import ADOUrl, ApiCall, get_test_api_call
from pyado.project import ProjectInfo

RepositoryName: TypeAlias = str
BranchName: TypeAlias = str
RepositoryId: TypeAlias = UUID
CommitId: TypeAlias = str
SshUrl: TypeAlias = str


class RepositoryInfo(BaseModel):
    """Type to store work item details."""

    id: RepositoryId
    name: RepositoryName
    project: ProjectInfo
    default_branch: BranchName | None = Field(alias="defaultBranch", default=None)
    size: NonNegativeInt
    remote_url: ADOUrl = Field(alias="remoteUrl")
    ssh_url: SshUrl = Field(alias="sshUrl")
    web_url: ADOUrl = Field(alias="webUrl")
    is_disabled: bool = Field(alias="isDisabled")
    is_in_maintenance: bool = Field(alias="isInMaintenance")


class _RepositoryInfoResults(BaseModel):
    """Type to read repository details results."""

    value: list[RepositoryInfo]


def iter_repository_details(project_api_call: ApiCall) -> Iterator[RepositoryInfo]:
    """Iterate over the repositories of the project."""
    response = project_api_call.get(
        "git",
        "repositories",
        version="7.0",
    )
    results = _RepositoryInfoResults.model_validate(response)
    yield from results.value


def test() -> None:
    """Function to test the functions."""
    test_api_call, test_config = get_test_api_call()
    del test_config
    for repo in iter_repository_details(test_api_call):
        print(repo)


if __name__ == "__main__":
    test()
