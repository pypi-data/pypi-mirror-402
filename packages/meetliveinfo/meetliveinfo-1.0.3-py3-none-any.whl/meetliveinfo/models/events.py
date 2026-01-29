import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from meetliveinfo.models.enums import Gender, HeatStatus, Round, Stroke


class EventAgeGroup(BaseModel):
    key: str
    min_age: Optional[int] = Field(None, alias="min")
    max_age: Optional[int] = Field(None, alias="max")

    @field_validator("min_age", "max_age", mode="before")
    @classmethod
    def parse_int(cls, v):
        if v in (None, "", "-1"):
            return None
        return int(v)


class HeatInfo(BaseModel):
    key: str
    code: str


class EventHeat(BaseModel):
    heatinfo: HeatInfo
    status: HeatStatus
    id: int
    code: int

    @field_validator("id", "code", mode="before")
    @classmethod
    def parse_int(cls, v):
        if v in (None, ""):
            return None
        return int(v)

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        return HeatStatus(int(v))


class Event(BaseModel):
    id: int
    eid: str
    number: Optional[int] = None

    gender: int
    stroke: Optional[Stroke] = None
    round: Round

    distance: Optional[str] = None
    isrelay: Optional[bool] = None

    agegroup: Optional[EventAgeGroup] = None
    agegroups: List[int] = []

    heats: List[EventHeat] = []

    date: Optional[datetime.date] = None
    time: Optional[str] = None

    @field_validator("id", "number", "gender", mode="before")
    @classmethod
    def parse_int(cls, v):
        if v in (None, ""):
            return None
        return int(v)

    # @field_validator("gender", mode="before")
    # @classmethod
    # def parse_gender(cls, v):
    #     return Gender(int(v))

    @field_validator("stroke", mode="before")
    @classmethod
    def parse_stroke(cls, v):
        if v in (None, ''):
            return None
        return Stroke(int(v))

    @field_validator("round", mode="before")
    @classmethod
    def parse_round(cls, v):
        return Round(int(v))

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if not v:
            return None
        if isinstance(v, datetime.date):
            return v
        return datetime.date.fromisoformat(v)


class EventsResponse(BaseModel):
    buildnr: Optional[int] = None
    lastupdate: Optional[datetime.datetime] = None
    events: List[Event] = []

    @field_validator("buildnr", mode="before")
    @classmethod
    def parse_buildnr(cls, v):
        if v in (None, ""):
            return None
        return int(v)

    @field_validator("lastupdate", mode="before")
    @classmethod
    def parse_lastupdate(cls, v):
        if not v:
            return None
        if isinstance(v, datetime.datetime):
            return v
        return datetime.datetime.fromisoformat(v)
