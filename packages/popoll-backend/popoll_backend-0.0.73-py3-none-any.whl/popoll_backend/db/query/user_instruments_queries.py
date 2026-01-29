from __future__ import annotations

import sqlite3

from popoll_backend.db import insert
from popoll_backend.db.model.user_instruments import UserInstruments

class UserInstrumentsQueries:
        
    def create(self, cursor: sqlite3.Cursor, user_id: int, instrument_id: int, is_main: bool) -> UserInstruments:
        return insert(UserInstruments, cursor, 'INSERT INTO user_instruments(user_id, instrument_id, is_main) VALUES(?, ?, ?) RETURNING id, user_id, instrument_id, is_main', (user_id, instrument_id, is_main))
    
    def delete(self, cursor: sqlite3.Cursor, id: int) -> None:
        cursor.execute('DELETE FROM user_instruments WHERE id=?', (id,))
        return
    
    def delete_user(self, cursor: sqlite3.Cursor, user_id: int) -> None:
        cursor.execute('DELETE FROM user_instruments WHERE user_id=?', (user_id,))
        return