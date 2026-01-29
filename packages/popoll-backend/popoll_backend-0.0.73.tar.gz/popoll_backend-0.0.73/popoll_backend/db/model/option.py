from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Optional

from popoll_backend.db.model import field

FIELDS = ['name', 'color']
@dataclass
class Option:
    
    name: str
    color: str
    
    @classmethod
    def create_table(cls):
        return """ CREATE TABLE IF NOT EXISTS options (
            name text,
            color text 
        ); """
        
    @classmethod
    def toResource(cls, row: sqlite3.Row, prefix: Optional[str]=None) -> Option:
        return Option(
            name=field(row, 'name', prefix),
            color=field(row, 'color', prefix)
        )