import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class GlobalsSession(BaseModel):
    number: int
    lanemin: int
    lanemax: int
    course: int
    time: Optional[str] = None
    date: Optional[datetime.date] = None
    name: Optional[str] = None

    @field_validator(
        "number",
        "lanemin",
        "lanemax",
        "course",
        mode="before",
    )
    @classmethod
    def parse_ints(cls, v):
        if v in ("", None):
            return None
        return int(v)

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if not v:
            return None
        return datetime.date.fromisoformat(v)


class Globals(BaseModel):
    buildnr: int
    nation: str | None = None

    name: str
    city: str | None = None

    course: int | None = None
    number: int | None = None

    ismulticourse: bool
    sessions: List[GlobalsSession]

    @field_validator("course", "number", mode="before")
    @classmethod
    def parse_ints(cls, v):
        if v in ("", None):
            return None
        return int(v)


GlobalsResponse = Globals
