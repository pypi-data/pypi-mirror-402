from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

from meetliveinfo.models.enums import HeatStatus


class HeatInfo(BaseModel):
    key: str
    time: Optional[str] = None
    code: Optional[str] = None


class SessionEventHeat(BaseModel):
    heatinfo: HeatInfo
    status: HeatStatus
    id: Optional[str] = None
    time: Optional[str] = None
    code: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        return HeatStatus(int(v))


class SessionEvent(BaseModel):
    id: Optional[str] = None
    status: HeatStatus
    heats: List[SessionEventHeat] = []

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        return HeatStatus(int(v))


class Session(BaseModel):
    day: Optional[int] = None
    events: List[SessionEvent] = []

    @field_validator("day", mode="before")
    @classmethod
    def parse_day(cls, v):
        if v in (None, ""):
            return None
        return int(v)


class EventsBySessionResponse(BaseModel):
    buildnr: Optional[int] = None
    lastupdate: Optional[datetime] = None
    sessions: List[Session] = []

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
