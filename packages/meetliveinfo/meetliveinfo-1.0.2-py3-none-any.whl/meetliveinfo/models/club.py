from typing import List, Optional
from pydantic import BaseModel, field_validator


class Club(BaseModel):
    id: int

    name: str
    shortname: Optional[str] = None
    code: Optional[str] = None
    longcode: Optional[str] = None

    nation: Optional[str] = None
    region: Optional[str] = None

    # =========================
    # Validators
    # =========================

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v):
        if v in ("", None):
            raise ValueError("club id is missing")
        return int(v)

    @field_validator(
        "shortname",
        "code",
        "longcode",
        "nation",
        "region",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


ClubsResponse = List[Club]
