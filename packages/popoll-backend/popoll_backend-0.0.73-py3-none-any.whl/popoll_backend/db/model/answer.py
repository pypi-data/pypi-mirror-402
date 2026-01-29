from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Optional

from popoll_backend.db.model import field

FIELDS = ['id', 'user_id', 'date_id', 'response']

@dataclass
class Answer:
    
    id: int
    user_id: int
    date_id: int
    response: bool

    @classmethod
    def create_table(cls):
        return """ CREATE TABLE IF NOT EXISTS answers (
            id integer PRIMARY KEY AUTOINCREMENT,
            user_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date_id integer NOT NULL REFERENCES dates(id) ON DELETE CASCADE,
            response boolean NOT NULL,
            UNIQUE(user_id, date_id)
        ); """
     
    @classmethod   
    def toResource(cls, row: sqlite3.Row, prefix: Optional[str]=None) -> Answer:
        return Answer(
            id=field(row, 'id', prefix),
            user_id=field(row, 'user_id', prefix),
            date_id=field(row, 'date_id', prefix),
            response=bool(field(row, 'response', prefix))
        )
