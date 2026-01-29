"""Module to interact with Azure DevOps builds."""
# Copyright (c) 2023, Fred Stober
# SPDX-License-Identifier: MIT

from collections.abc import Iterator
from datetime import datetime
from typing import Any, Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.networks import AnyUrl

from pyado.api_call import ADOUrl, ApiCall, get_test_api_call
from pyado.work_item import WorkItemId

BuildId: TypeAlias = int
TimelineId: TypeAlias = UUID
TaskId: TypeAlias = UUID
QueueId: TypeAlias = int
BuildLogId: TypeAlias = int
BuildRecordType: TypeAlias = Literal[
    "Checkpoint",
    "Checkpoint.Approval",
    "Checkpoint.Authorization",
    "Checkpoint.ExtendsCheck",
    "Phase",
    "Stage",
    "Job",
    "Task",
]


def get_build_api_call(project_api_call: ApiCall, build_id: BuildId) -> ApiCall:
    """Get pull request API call."""
    return project_api_call.build_call(
        "build",
        "builds",
        build_id,
    )


def iter_build_work_item_ids(build_api_call: ApiCall) -> Iterator[WorkItemId]:
    """Get work items linked to the build pipeline."""
    max_results = 100
    response = build_api_call.get(
        "workitems",
        parameters={"$top": max_results},
        version="7.0",
    )
    for entry in response["value"]:
        yield int(entry["id"])


class BuildLogInfo(BaseModel, extra="forbid"):
    """Type to store build log details."""

    id: BuildLogId
    log_type: Literal["Container"] = Field(alias="type")
    url: ADOUrl


class BuildRecordTypeInfo(BaseModel, extra="forbid"):
    """Type to store build task type details."""

    id: TaskId
    name: str
    version: str


class BuildAttemptInfo(BaseModel, extra="forbid"):
    """Type to store build attempt details."""

    attempt: int
    timeline_id: UUID = Field(alias="timelineId")
    record_id: UUID = Field(alias="recordId")


class BuildIssue(BaseModel, extra="forbid"):
    """Type for build message issues."""

    category: str | None = None
    data: dict[str, str] | None = {}
    message: str
    type: Literal["error", "warning"]


class BuildRecordInfo(BaseModel, extra="forbid"):
    """Type to store build task details."""

    attempt: int
    change_id: int | None = Field(alias="changeId")
    current_operation: Any = Field(alias="currentOperation")
    details: Any
    error_count: int | None = Field(default=None, alias="errorCount")
    finish_time: datetime | None = Field(alias="finishTime")
    id: TaskId
    identifier: str | None
    issues: list[BuildIssue] | None = None
    last_modified: datetime = Field(alias="lastModified")
    log: BuildLogInfo | None
    name: str
    order: int | None = None
    ref_name: str | None = Field(alias="refName")
    parent_id: TaskId | None = Field(alias="parentId")
    percent_complete: int | None = Field(alias="percentComplete")
    previous_attempts: list[BuildAttemptInfo] = Field(alias="previousAttempts")
    queue_id: QueueId | None = Field(default=None, alias="queueId")
    result: Literal["failed", "succeeded", "skipped", "canceled"] | None
    result_code: str | None = Field(alias="resultCode")
    start_time: datetime | None = Field(alias="startTime")
    state: Literal["completed", "pending", "inProgress"]
    task: BuildRecordTypeInfo | None
    type_name: BuildRecordType = Field(alias="type")
    url: AnyUrl | None
    warning_count: int | None = Field(default=None, alias="warningCount")
    worker_name: str | None = Field(alias="workerName")


class _BuildRecordInfoResults(BaseModel):
    """Type to read build record details results."""

    records: list[BuildRecordInfo]
    id: TimelineId


def iter_timeline_records(build_api_call: ApiCall) -> Iterator[BuildRecordInfo]:
    """Iterate over task in the timeline.

    Reference: https://github.com/MicrosoftDocs/vsts-rest-api-specs/blob/master
    /specification/build/7.1/build.json#L2478
    """
    response = build_api_call.get(
        "timeline",
        version="7.1",
    )
    results = _BuildRecordInfoResults.model_validate(response)
    yield from results.records


def test() -> None:
    """Function to test the functions."""
    test_api_call, test_config = get_test_api_call()
    build_api_call = get_build_api_call(test_api_call, test_config["build_id"])
    for build_work_item in iter_build_work_item_ids(build_api_call):
        print(build_work_item)
    for task in iter_timeline_records(build_api_call):
        print(task)


if __name__ == "__main__":
    test()
