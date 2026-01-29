from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, field_validator


# =========================
# Leaf models
# =========================

class TeamMedals(BaseModel):
    name: str
    code: str
    place: int

    medals: List[int]        # [gold, silver, bronze]
    medalswomen: List[int]   # [gold, silver, bronze]
    medalsmen: List[int]     # [gold, silver, bronze]

    @field_validator("place", mode="before")
    @classmethod
    def parse_place(cls, v):
        return int(v)


class MedalCategory(BaseModel):
    name: str
    teams: List[TeamMedals]


# =========================
# Root response
# =========================

class MedalsResponse(BaseModel):
    buildnr: int
    lastupdate: datetime
    categories: List[MedalCategory]

    @field_validator("buildnr", mode="before")
    @classmethod
    def parse_buildnr(cls, v):
        return int(v)

    @field_validator("lastupdate", mode="before")
    @classmethod
    def parse_lastupdate(cls, v):
        return datetime.fromisoformat(v)
