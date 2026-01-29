from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from meetliveinfo.models.enums import Gender


class Athlete(BaseModel):
    id: int
    gender: Gender

    firstname: str
    lastname: str
    nameprefix: Optional[str] = None
    fullname: Optional[str] = None

    nation: Optional[str] = None
    birthdate: Optional[date] = None
    license: Optional[str] = None

    club_id: Optional[int] = Field(None, alias="clubid")

    # =========================
    # Validators
    # =========================

    @field_validator("id", "club_id", mode="before")
    @classmethod
    def parse_ints(cls, v):
        if v in ("", None):
            return None
        return int(v)

    @field_validator("gender", mode="before")
    @classmethod
    def parse_gender(cls, v):
        return Gender(int(v))

    @field_validator("birthdate", mode="before")
    @classmethod
    def parse_birthdate(cls, v):
        if not v:
            return None
        return date.fromisoformat(v)


AthletesResponse = List[Athlete]
