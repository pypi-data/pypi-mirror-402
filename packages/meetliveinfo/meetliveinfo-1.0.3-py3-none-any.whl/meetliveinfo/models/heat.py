from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from meetliveinfo.models.enums import Gender, HeatStatus


class BaseAthlete(BaseModel):
    id: int
    uniqueid: int
    lane: int
    clubid: int
    clubtext: str
    clubcode: str
    entrytime: str
    agetext: str
    nametext: str

    # Эти поля не всегда есть в entries → не делаем обязательными в базовой модели
    gender: Optional[Gender] = None
    athleteid: Optional[int] = None
    clubname: Optional[str] = None

    @field_validator("gender", mode="before")
    @classmethod
    def parse_gender(cls, v):
        if v is None or v == "":
            return None
        return Gender(int(v))

    @field_validator("athleteid", "id", "uniqueid", "lane", "clubid", mode="before")
    @classmethod
    def parse_int_fields(cls, v):
        if v is None or v == "":
            return None
        return int(v)


class Result(BaseAthlete):
    heatplace: int
    swimtime: str
    points: Optional[int] = None
    splits: Optional[Dict[str, str]] = None
    qualcode: Optional[str] = None
    info: Optional[str] = None
    diff: Optional[str] = None
    place: Optional[int] = None


class Entry(BaseAthlete):
    """entries бывают без gender/athleteid/clubname — поэтому они Optional в BaseAthlete."""
    pass


class HeatResultResponse(BaseModel):
    eventid: int
    id: int
    status: HeatStatus
    time: Optional[str] = None
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
