from pydantic import BaseModel, field_validator
from typing import List

from datetime import datetime


class TeamPointsResult(BaseModel):
    points: int
    name: str
    code: str
    place: int

    @field_validator("points", "place", mode="before")
    @classmethod
    def parse_ints(cls, v):
        return int(v)


class PointScoreCategory(BaseModel):
    name: str
    teams: List[TeamPointsResult]


class PointScoreDetailsResponse(BaseModel):
    buildnr: int
    id: int
    name: str
    lastupdate: datetime

    categories: List[PointScoreCategory]

    @field_validator("buildnr", "id", mode="before")
    @classmethod
    def parse_root_ints(cls, v):
        return int(v)

    @field_validator("lastupdate", mode="before")
    @classmethod
    def parse_lastupdate(cls, v):
        return datetime.fromisoformat(v)


class PointScore(BaseModel):
    id: int
    name: str

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v):
        return int(v)


PointScoresResponse = List[PointScore]
