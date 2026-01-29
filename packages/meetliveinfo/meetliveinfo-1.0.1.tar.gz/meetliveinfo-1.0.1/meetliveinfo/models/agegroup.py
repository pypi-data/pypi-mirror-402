from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class AgeGroup(BaseModel):
    id: int
    key: str
    min_age: Optional[int] = Field(None, alias="min")
    max_age: Optional[int] = Field(None, alias="max")


class AgeGroupsResponse(BaseModel):
    buildnr: int
    lastupdate: datetime
    agegroups: list[AgeGroup]
