from __future__ import annotations

import sqlite3
from typing import List

from popoll_backend.db import getOne, getSome, insert, update
from popoll_backend.db.model.answer import Answer

class AnswerQueries:

    def create(self, cursor: sqlite3.Cursor, user_id: int, date_id: int, response: bool) -> Answer:
        return insert(Answer, cursor, 'INSERT INTO answers(user_id, date_id, response) VALUES(?, ?, ?) RETURNING id, user_id, date_id, response', (user_id, date_id, response))
    
    def get(self, cursor: sqlite3.Cursor, id: int) -> Answer:
        return getOne(Answer, cursor, 'SELECT id, user_id, date_id, response FROM answers WHERE id=? LIMIT 1', (id,))
    
    def get_search(self, cursor: sqlite3.Cursor, user_id: int, date_id: int) -> Answer:
        return getOne(Answer, cursor, 'SELECT id, user_id, date_id, response FROM answers WHERE user_id=? AND date_id=? LIMIT 1', (user_id, date_id))
    
    def get_for_user(self, cursor: sqlite3.Cursor, user_id: int) -> List[Answer]:
        return getSome(Answer, cursor, 'SELECT id, user_id, date_id, response FROM answers WHERE user_id=?', (user_id,))
    
    def get_for_date(self, cursor: sqlite3.Cursor, date_id: int) -> List[Answer]:
        return getSome(Answer, cursor, 'SELECT id, user_id, date_id, response FROM answers WHERE date_id=?', (date_id,))
        
    def update(self, cursor: sqlite3.Cursor, id: int, response: bool) -> Answer:
        return update(Answer, cursor, 'UPDATE answers SET response=? WHERE id=? RETURNING id, user_id, date_id, response', (response, id))
    
    def delete(self, cursor: sqlite3.Cursor, id: int) -> None:
        cursor.execute('DELETE FROM answers WHERE id=?', (id,))
        return