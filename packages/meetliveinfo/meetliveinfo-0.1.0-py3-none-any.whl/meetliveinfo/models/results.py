from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from meetliveinfo.models.enums import Gender


# =========================
# Nested models
# =========================

class HeatInfo(BaseModel):
    key: str
    time: str
    code: str


class ResultEntry(BaseModel):
    id: int
    uniqueid: int

    athleteid: int
    heatid: int
    clubid: int

    gender: Gender
    nation: Optional[str] = None

    nametext: str
    agetext: str

    lane: int
    place: int

    swimtime: str
    entrytime: Optional[str] = None
    diff: Optional[str] = None

    points: Optional[int] = None
    medal: Optional[int] = None

    info: Optional[str] = None
    qualcode: Optional[str] = None

    clubname: Optional[str] = None
    clubcode: Optional[str] = None
    clubtext: Optional[str] = None

    heatinfo: HeatInfo
    splits: Dict[str, str] = Field(default_factory=dict)

    # =========================
    # Validators
    # =========================

    @field_validator(
        "id",
        "uniqueid",
        "athleteid",
        "heatid",
        "clubid",
        "lane",
        "place",
        "points",
        "medal",
        mode="before",
    )
    @classmethod
    def parse_ints(cls, v):
        if v in ("", None):
            return None
        return int(v)

    @field_validator("gender", mode="before")
    @classmethod
    def parse_gender(cls, v):
        return Gender(int(v))


class AgeGroupResults(BaseModel):
    id: int
    results: List[ResultEntry]

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v):
        return int(v)


# =========================
# Root response
# =========================

class ResultsResponse(BaseModel):
    buildnr: int
    status: int
    lastupdate: datetime

    id: int
    agegroups: List[AgeGroupResults]

    @field_validator("id", "buildnr", "status", mode="before")
    @classmethod
    def parse_ints(cls, v):
        return int(v)

    @field_validator("lastupdate", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        return datetime.fromisoformat(v)
