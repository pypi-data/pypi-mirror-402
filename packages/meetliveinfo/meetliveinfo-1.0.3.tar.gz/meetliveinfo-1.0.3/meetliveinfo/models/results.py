from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, field_validator

from meetliveinfo.models.enums import Gender, HeatStatus


# =========================
# Nested models
# =========================

class HeatInfo(BaseModel):
    key: Optional[str] = None
    time: Optional[str] = None
    code: Optional[str] = None


# =========================
# Result
# =========================

class Result(BaseModel):
    id: Optional[int] = None
    athleteid: Optional[int] = None
    uniqueid: Optional[int] = None
    heatid: Optional[int] = None
    clubid: Optional[int] = None

    gender: Optional[Gender] = None
    nation: Optional[str] = None

    nametext: Optional[str] = None
    agetext: Optional[str] = None
    info: Optional[str] = None

    clubname: Optional[str] = None
    clubtext: Optional[str] = None
    clubcode: Optional[str] = None

    lane: Optional[int] = None
    place: Optional[int] = None
    medal: Optional[int] = None

    entrytime: Optional[str] = None
    swimtime: Optional[str] = None
    diff: Optional[str] = None
    points: Optional[str] = None

    heatinfo: Optional[HeatInfo] = None
    splits: Optional[Dict[str, str]] = None
    qualcode: Optional[str] = None

    # =========================
    # Validators
    # =========================

    @field_validator(
        "id",
        "athleteid",
        "uniqueid",
        "heatid",
        "clubid",
        "lane",
        "place",
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
        if v in ("", None):
            return None
        return Gender(int(v))


# =========================
# Age group
# =========================

class AgeGroup(BaseModel):
    id: int
    results: List[Result]

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v):
        return int(v)


# =========================
# Root response
# =========================

class ResultsResponse(BaseModel):
    id: int
    buildnr: int
    status: HeatStatus
    lastupdate: datetime
    agegroups: List[AgeGroup]

    @field_validator("id", "buildnr", mode="before")
    @classmethod
    def parse_ints(cls, v):
        return int(v)

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        return HeatStatus(int(v))
