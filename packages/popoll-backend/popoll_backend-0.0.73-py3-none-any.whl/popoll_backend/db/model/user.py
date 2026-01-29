from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Optional, cast

from popoll_backend.db.model import field

FIELDS = ['id', 'name']

@dataclass
class User:
    
    id: int
    name: str
    
    @classmethod
    def create_table(cls):
        return """ CREATE TABLE IF NOT EXISTS users (
            id integer PRIMARY KEY AUTOINCREMENT,
            name text NOT NULL UNIQUE COLLATE NOCASE
        ); """
        
    @classmethod
    def toResource(cls, row: sqlite3.Row, prefix: Optional[str]=None) -> User:
        return User(
            id=field(row, 'id', prefix),
            name=field(row, 'name', prefix)
        )
        
    def __hash__(self) -> int:
        return self.id
    
    def __eq__(self, other) -> bool:
        return isinstance(other, User) and self.id == cast(User, other).id