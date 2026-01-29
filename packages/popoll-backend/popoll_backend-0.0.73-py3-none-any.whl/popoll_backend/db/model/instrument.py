from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Optional, cast

from popoll_backend.db.model import field

FIELDS = ['id', 'name', 'rank']

@dataclass
class Instrument:
    
    id: int
    name: str
    rank: int

    @classmethod
    def create_table(cls):
        return """CREATE TABLE IF NOT EXISTS instruments (
            id integer PRIMARY KEY,
            name text NOT NULL UNIQUE,
            rank number NOT NULL UNIQUE
        );
        """
        
    @classmethod
    def toResource(cls, row: sqlite3.Row, prefix: Optional[str]=None) -> Instrument:
        return Instrument(
            id=field(row, 'id', prefix),
            name=field(row, 'name', prefix),
            rank=field(row, 'rank', prefix)
        )
    
    def __hash__(self) -> int:
        return self.id
    
    def __eq__(self, other) -> bool:
        return isinstance(other, Instrument) and self.id == cast(Instrument, other).id