from __future__ import annotations

import datetime
import sqlite3

from popoll_backend.db import getOne, insert, update
from popoll_backend.db.model.session import Session

class SessionQueries:
    
    def create(self, cursor: sqlite3.Cursor, session_id: str, user_id: int) -> Session:
        return insert(Session, cursor, 'INSERT INTO sessions(session_id, user_id, datetime) VALUES(?, ?, ?) RETURNING id, session_id, user_id, datetime', (session_id, user_id, datetime.datetime.now().isoformat(sep='T', timespec='auto')))
    
    def get(self, cursor: sqlite3.Cursor, session_id: str) -> Session:
        return getOne(Session, cursor, 'SELECT id, session_id, user_id FROM sessions WHERE session_id=?', (session_id,))
    
    def update(self, cursor: sqlite3.Cursor, session_id: str, user_id: int) -> Session:
        return update(Session, cursor, 'UPDATE sessions SET session_id=?, user_id=? WHERE session_id=? RETURNING id, session_id, user_id, datetime', (session_id, user_id, session_id))