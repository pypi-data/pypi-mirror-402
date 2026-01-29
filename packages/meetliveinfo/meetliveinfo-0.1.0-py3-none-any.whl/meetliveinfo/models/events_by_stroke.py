# models/events_by_stroke.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

# Переиспользуем HeatInfo и EventHeat


class HeatInfo(BaseModel):
    key: str
    time: Optional[str] = None
    code: Optional[str] = None


class EventHeat(BaseModel):
    heatinfo: HeatInfo
    status: Optional[int] = None
    id: Optional[str] = None
    time: Optional[str] = None
    code: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        if v in (None, ""):
            return None
        return int(v)


class Event(BaseModel):
    id: Optional[str] = None
    status: Optional[int] = None
    heats: List[EventHeat] = []

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        if v in (None, ""):
            return None
        return int(v)


class EventGroup(BaseModel):
    gender: Optional[int] = None
    stroke: Optional[int] = None
    events: List[Event] = []

    @field_validator("gender", "stroke", mode="before")
    @classmethod
    def parse_int_fields(cls, v):
        if v in (None, ""):
            return None
        return int(v)


class EventsByStrokeResponse(BaseModel):
    buildnr: Optional[int] = None
    lastupdate: Optional[datetime] = None
    eventgroups: List[EventGroup] = []

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
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)
