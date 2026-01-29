# models/events_by_stroke.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

from meetliveinfo.models.enums import Gender, HeatStatus, Stroke

# Переиспользуем HeatInfo и EventHeat


class HeatInfo(BaseModel):
    key: str
    time: Optional[str] = None
    code: Optional[str] = None


class EventHeat(BaseModel):
    heatinfo: HeatInfo
    status: HeatStatus
    id: Optional[str] = None
    time: Optional[str] = None
    code: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        return HeatStatus(int(v))


class Event(BaseModel):
    id: Optional[str] = None
    status: HeatStatus
    heats: List[EventHeat] = []

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        return HeatStatus(int(v))


class EventGroup(BaseModel):
    gender: Gender
    stroke: Stroke
    events: List[Event] = []

    @field_validator("stroke", mode="before")
    @classmethod
    def parse_stroke(cls, v):
        return Stroke(int(v))

    @field_validator("gender", mode="before")
    @classmethod
    def parse_gender(cls, v):
        return Gender(int(v))


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
