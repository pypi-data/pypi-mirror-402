"""Module to interact with Azure DevOps projects."""
# Copyright (c) 2023, Fred Stober
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, Field

ProjectName: TypeAlias = str
ProjectId: TypeAlias = UUID


class ProjectInfo(BaseModel):
    """Type to store project details."""

    id: ProjectId
    name: ProjectName
    description: str
    state: Literal["wellFormed"]
    revision: int
    visibility: Literal["private"]
    last_update_time: datetime = Field(alias="lastUpdateTime")
