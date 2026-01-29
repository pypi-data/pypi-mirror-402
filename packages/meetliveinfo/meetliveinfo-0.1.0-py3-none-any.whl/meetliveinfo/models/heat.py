from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class BaseAthlete(BaseModel):
    id: int
    gender: int
    athleteid: int
    uniqueid: int
    lane: int
    clubid: int
    clubtext: str
    clubname: str
    clubcode: str
    entrytime: float
    agetext: str
    nametext: str


class Result(BaseAthlete):
    heatplace: int
    swimtime: float
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
    status: int
    time: str
    code: str
    heatinfo: Dict[str, str]
    results: List[Result] = Field(default_factory=list)
    entries: List[Entry] = Field(default_factory=list)

    @field_validator("eventid", "id", "status", mode="before")
    @classmethod
    def parse_int_fields(cls, v):
        return int(v)
