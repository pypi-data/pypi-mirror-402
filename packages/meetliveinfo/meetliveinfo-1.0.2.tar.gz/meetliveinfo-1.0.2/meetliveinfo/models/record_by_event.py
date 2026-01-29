
from typing import Dict, Optional, List
from pydantic import BaseModel


class RecordList(BaseModel):
    lenex: str
    name: str
    code: str


class RecordByEventMeet(BaseModel):
    nation: str
    name: str
    date: str
    city: str


class RecordByEventItem(BaseModel):
    firstname: str
    lastname: str
    name: str

    clubname: str
    clubcode: str

    agetext: str
    swimtime: str
    splits: Optional[Dict[str, str]] = None

    meet: RecordByEventMeet
    recordlist: RecordList

    @property
    def is_placeholder(self) -> bool:
        return (
            self.clubname == "???"
            or not self.name
            or not self.swimtime
            or self.agetext == "99"
        )


RecordsByEventResponse = List[RecordByEventItem]
