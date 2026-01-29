"""Module to interact with Azure DevOps work items."""
# Copyright (c) 2023, Fred Stober
# SPDX-License-Identifier: MIT

from collections.abc import Iterator
from datetime import datetime
from typing import Any, TypeAlias
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.networks import AnyUrl

from pyado.api_call import ApiCall, JsonPatchAdd, get_test_api_call

SprintIterationId: TypeAlias = UUID
SprintIterationPath: TypeAlias = str
WorkItemField: TypeAlias = str
WorkItemId: TypeAlias = int
WorkItemRelationType: TypeAlias = str


class WorkItemRelation(BaseModel):
    """Type to store work item relationships."""

    rel: WorkItemRelationType
    url: AnyUrl
    attributes: dict[str, Any] | None = None


class WorkItemInfo(BaseModel):
    """Type to store work item details."""

    id: WorkItemId
    fields: dict[WorkItemField, Any]
    relations: list[WorkItemRelation]


class _WorkItemInfoResults(BaseModel):
    """Type to read work item detail results."""

    value: list[WorkItemInfo]


def iter_work_item_details(
    project_api_call: ApiCall,
    work_item_id_list: list[WorkItemId],
    work_item_field_list: list[WorkItemField] | None = None,
) -> Iterator[WorkItemInfo]:
    """Iterate over the work items."""
    request_json: dict[str, Any] = {
        "ids": work_item_id_list,
    }
    if work_item_field_list:
        request_json["fields"] = work_item_field_list
    else:
        request_json["$expand"] = "relations"
    response = project_api_call.post(
        "wit",
        "workitemsbatch",
        version="7.1-preview.1",
        json=request_json,
    )
    results = _WorkItemInfoResults.model_validate(response)
    yield from results.value


def create_work_item(
    project_api_call: ApiCall,
    fields: dict[WorkItemField, Any],
    relations: list[WorkItemRelation] | None = None,
) -> WorkItemInfo:
    """Create work items."""
    ticket_type: str | None = fields.pop("System.WorkItemType", None)
    if ticket_type is None:
        err_msg = f"Work item type must be specified! {fields!r}"
        raise RuntimeError(err_msg)
    json_patch_list = [
        JsonPatchAdd(path=f"/fields/{key}", value=value)
        for key, value in fields.items()
    ]
    for link in relations or []:
        link_dict = link.model_dump(mode="json", exclude_defaults=True)
        json_patch_add = JsonPatchAdd(path="/relations/-", value=link_dict)
        json_patch_list.append(json_patch_add)

    response = project_api_call.post(
        "wit",
        "workitems",
        f"${ticket_type}",
        version="7.1",
        json=[json_patch.model_dump(mode="json") for json_patch in json_patch_list],
    )
    return WorkItemInfo.model_validate(response)


class SprintIterationAttributes(BaseModel):
    """Type to store sprint attribute information."""

    start_date: datetime = Field(alias="startDate")
    finish_date: datetime = Field(alias="finishDate")
    timeframe: str = Field(alias="timeFrame")


class SprintIterationInfo(BaseModel):
    """Type to store sprint information."""

    id: SprintIterationId
    name: str
    path: SprintIterationPath
    attributes: SprintIterationAttributes


class _SprintIterationInfoResults(BaseModel):
    count: int
    value: list[SprintIterationInfo]


def iter_sprint_iterations(
    team_api_call_api_call: ApiCall,
    timeframe_filter: str | None = None,
) -> Iterator[SprintIterationInfo]:
    """Iterate over the sprint iterations."""
    parameters: dict[str, int | str] = {}
    if timeframe_filter:
        parameters["$timeframe"] = timeframe_filter
    response = team_api_call_api_call.get(
        "work",
        "teamsettings",
        "iterations",
        version="7.1",
        parameters=parameters,
    )
    results = _SprintIterationInfoResults.model_validate(response)
    yield from results.value


def test() -> None:
    """Function to test the functions."""
    test_api_call, test_config = get_test_api_call()
    for iteration in iter_sprint_iterations(test_api_call):
        print(iteration)
    for iteration in iter_sprint_iterations(test_api_call, timeframe_filter="current"):
        print(iteration)
    for work_item in iter_work_item_details(test_api_call, [test_config["ticket_id"]]):
        print(work_item)
    create_work_item(
        test_api_call,
        test_config["fields"],
        [
            WorkItemRelation(
                rel="System.LinkTypes.Hierarchy-Reverse",
                url=test_config["parent_work_item_url"],
            ),
        ],
    )


if __name__ == "__main__":
    test()
