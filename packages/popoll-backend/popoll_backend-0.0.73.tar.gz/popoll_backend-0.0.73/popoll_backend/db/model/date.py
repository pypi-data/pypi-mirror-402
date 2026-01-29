from __future__ import annotations

from dataclasses import dataclass
import datetime
import sqlite3
from typing import Optional

from popoll_backend.db.model import field

def isOlder(actualDate: datetime.date, compare: datetime.date=datetime.date.today()):
    return actualDate < compare

FIELDS = ['id', 'title', 'date', 'time', 'end_time', 'is_frozen']

@dataclass
class Date:
        
    id: int
    title: str
    date: datetime.date
    time: Optional[datetime.time]
    end_time: Optional[datetime.time]
    is_frozen: bool
    is_old: bool
    

    @classmethod
    def create_table(cls):
        return """ CREATE TABLE IF NOT EXISTS dates (
            id integer PRIMARY KEY AUTOINCREMENT,
            title text NOT NULL,
            date text NOT NULL,
            time text,
            end_time text,
            is_frozen boolean NOT NULL
        ); """
    
    @classmethod    
    def toResource(cls, row: sqlite3.Row, prefix: Optional[str]=None) -> Date:
        date = datetime.date.fromisoformat(field(row, 'date', prefix))
        return Date(
            id=field(row, 'id', prefix),
            title=field(row, 'title', prefix),
            date=date,
            time=datetime.time.fromisoformat(field(row, 'time', prefix)) if field(row, 'time', prefix) else None,
            end_time=datetime.time.fromisoformat(field(row, 'end_time', prefix)) if field(row, 'end_time', prefix) else None,
            is_frozen=bool(field(row, 'is_frozen', prefix)),
            is_old=isOlder(date)
        )
