from typing import Dict, List, Optional
from typing import List
from pydantic import BaseModel, field_validator


class RecordItem(BaseModel):
    id: int
    name: str
    lenex: str

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v):
        return int(v)


RecordListResponse = List[RecordItem]


class RecordMeet(BaseModel):
    nation: str
    name: str
    date: str
    city: str


class RecordEntry(BaseModel):
    firstname: str
    lastname: str
    name: str

    clubname: str
    clubcode: str

    agetext: str
    swimtime: str

    splits: Optional[Dict[str, str]] = None
    meet: RecordMeet

    @property
    def is_placeholder(self) -> bool:
        """
        Заглушка вида:
        - clubname == '???'
        - пустые имя / время
        - agetext == '99'
        """
        return (
            self.clubname == "???"
            or not self.name
            or not self.swimtime
            or self.agetext == "99"
        )


class RecordsResponse(BaseModel):
    id: int
    name: str
    lenex: str
    records: List[RecordEntry]

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v):
        return int(v)

    def valid_records(self) -> List[RecordEntry]:
        """
        Возвращает только реальные записи без заглушек
        """
        return [r for r in self.records if not r.is_placeholder]
