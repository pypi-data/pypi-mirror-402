from __future__ import annotations

from dataclasses import dataclass

import sqlite3
from typing import Optional

from popoll_backend.db import insert
from popoll_backend.db.model import field

FIELDS = ['id', 'user_id', 'instrument_id', 'is_main']
@dataclass
class UserInstruments:
    
    id: int
    user_id: int
    instrument_id: int
    is_main: bool
    
    @classmethod
    def create_table(cls):
        return """ CREATE TABLE IF NOT EXISTS user_instruments (
            id integer PRIMARY KEY,
            user_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            instrument_id integer NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
            is_main boolean NOT NULL,
            UNIQUE(user_id, instrument_id)
        ); """

    @classmethod
    def toResource(cls, row: sqlite3.Row, prefix: Optional[str]=None) -> UserInstruments:
        return UserInstruments(
            id=field(row, 'id', prefix),
            user_id=field(row, 'user_id', prefix),
            instrument_id=field(row, 'instrument_id', prefix),
            is_main=bool(field(row, 'is_main', prefix))
        )
        
    @classmethod
    def create(cls, cursor: sqlite3.Cursor, user_id: int, instrument_id: int, is_main: bool) -> UserInstruments:
        return insert(UserInstruments, cursor, 'INSERT INTO user_instruments(user_id, instrument_id, is_main) VALUES(?, ?, ?) RETURNING id, user_id, instrument_id, is_main', (user_id, instrument_id, is_main))
    
    @classmethod
    def delete(cls, cursor: sqlite3.Cursor, id: int) -> None:
        cursor.execute('DELETE FROM user_instruments WHERE id=?', (id,))
        return