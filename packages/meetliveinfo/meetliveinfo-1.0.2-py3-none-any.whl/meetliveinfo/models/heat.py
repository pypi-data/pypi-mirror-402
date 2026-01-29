from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from meetliveinfo.models.enums import Gender, HeatStatus


class BaseAthlete(BaseModel):
    id: int
    gender: Gender
    athleteid: int
    uniqueid: int
    lane: int
    clubid: int
    clubtext: str
    clubname: str
    clubcode: str
    entrytime: str
    agetext: str
    nametext: str

    @field_validator("gender", mode="before")
    @classmethod
    def parse_gender(cls, v):
        return Gender(int(v))


class Result(BaseAthlete):
    heatplace: int
    swimtime: str
    points: int
    splits: Optional[Dict[str, str]] = None
    qualcode: Optional[str] = None
    info: Optional[str] = None
    diff: Optional[str] = None
    place: Optional[int] = None


class Entry(BaseAthlete):
    pass


class HeatResultResponse(BaseModel):
    eventid: int
    id: int
    status: HeatStatus
    time: str
    code: str
    heatinfo: Dict[str, str]
    results: List[Result] = Field(default_factory=list)
    entries: List[Entry] = Field(default_factory=list)

    @field_validator("eventid", "id", mode="before")
    @classmethod
    def parse_int_fields(cls, v):
        return int(v)

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        return HeatStatus(int(v))
