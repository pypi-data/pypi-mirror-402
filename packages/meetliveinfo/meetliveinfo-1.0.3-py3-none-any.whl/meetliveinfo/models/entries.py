from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from meetliveinfo.models.enums import Gender, HeatStatus


class Record(BaseModel):
    agegroup: str
    clubcode: Optional[str] = None
    swimtime: Optional[str] = None
    date: datetime
    city: str
    recordname: str
    nametext: str
    recordcode: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)


class Entry(BaseModel):
    id: int
    gender: int
    nation: Optional[str] = None
    clubtext: Optional[str] = None
    clubname: Optional[str] = None
    clubcode: Optional[str] = None
    athleteid: Optional[int] = None
    entrytime: Optional[str] = None
    agetext: Optional[str] = None
    uniqueid: Optional[int] = None
    clubid: Optional[int] = None
    nametext: Optional[str] = None
    place: Optional[int] = None

    @field_validator("id",  "athleteid", "gender",
                     "uniqueid", "clubid", "place",
                     mode="before")
    @classmethod
    def parse_int_fields(cls, v):
        if v in (None, ""):
            return None
        return int(v)


class EntriesResponse(BaseModel):
    buildnr: int
    canedit: bool
    status: HeatStatus
    lastupdate: datetime
    id: int
    records: List[Record] = Field(default_factory=list)
    entries: List[Entry] = Field(default_factory=list)

    @field_validator("lastupdate", mode="before")
    @classmethod
    def parse_lastupdate(cls, v):
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        return HeatStatus(int(v))
