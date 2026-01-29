from __future__ import annotations

import sqlite3
from typing import List
from popoll_backend.db import getOne, getSome, insert
from popoll_backend.db.model.instrument import Instrument

class InstrumentQueries:
        
    def create(self, cursor: sqlite3.Cursor, name: str, rank: int) -> Instrument:
        return insert(Instrument, cursor, 'INSERT OR IGNORE INTO instruments(name, rank) VALUES(?, ?) RETURNING id, name, rank', (name, rank))

    def get(self, cursor: sqlite3.Cursor, id: int) -> Instrument:
        return getOne(Instrument, cursor, 'SELECT id, name, rank FROM instruments WHERE id=? LIMIT 1', (id,))
    
    def getUsed(self, cursor: sqlite3.Cursor) -> List[Instrument]:
        return getSome(Instrument, cursor, """
                       SELECT i.id, i.name, i.rank 
                       FROM instruments as i
                       WHERE i.id in (
                           SELECT DISTINCT(ui.instrument_id) FROM user_instruments as ui
                       );
                       """)
    
    def getAll(self, cursor: sqlite3.Cursor) -> List[Instrument]:
        return getSome(Instrument, cursor, 'SELECT id, name, rank FROM instruments ORDER BY rank')