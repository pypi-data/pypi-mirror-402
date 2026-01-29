from __future__ import annotations

import sqlite3

from popoll_backend.db import getOne, insert, update
from popoll_backend.db.model.option import Option

class OptionQueries:
        
    def create(self, cursor: sqlite3.Cursor, name: str, color: str) -> Option:
        return insert(Option, cursor, 'INSERT INTO options(name, color) values(?, ?) RETURNING name, color', (name, color))
    
    def get(self, cursor: sqlite3.Cursor) -> Option:
        return getOne(Option, cursor, 'SELECT name, color FROM options')
    
    def update(self, cursor: sqlite3.Cursor, name: str, color: str) -> Option:
        return update(Option, cursor, 'UPDATE options SET name=?, color=? RETURNING name, color', (name, color))