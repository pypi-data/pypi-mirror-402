import sqlite3
from typing import List

from popoll_backend.db import getSome, insert, update
from popoll_backend.db.model import answer, date, field, fields, user
from popoll_backend.db.model import instrument
from popoll_backend.db.model import user_instruments
from popoll_backend.db.model.instrument import Instrument
from popoll_backend.db.model.user import User
from popoll_backend.db.model.date import Date
from popoll_backend.db.model.answer import Answer
from popoll_backend.db.model.user_instruments import UserInstruments
from popoll_backend.usecases.poll.user.dates_user import DatesUser
from popoll_backend.usecases.poll.user.user_with_instruments import UserWithInstruments


class UserQueries:

    def create(self, cursor: sqlite3.Cursor, name: str) -> User:
        return insert(User, cursor, 'INSERT INTO users(name) VALUES(?) RETURNING id, name', (name,))

    def getUserWithInstruments(self, cursor: sqlite3.Cursor, id: int) -> UserWithInstruments:        
        rows = cursor.execute(f"""
            SELECT 
                {fields(user.FIELDS, 'u')},
                {fields(instrument.FIELDS, 'i')},
                {fields(user_instruments.FIELDS, 'ui')}
            FROM users as u 
            INNER JOIN user_instruments as ui
                ON u.id = ui.user_id
            INNER JOIN instruments as i
                ON ui.instrument_id = i.id
                AND ui.user_id = u.id
            WHERE u.id = ?
            ORDER BY i.rank
            """, (id,)).fetchall()
        return UserWithInstruments(
            User.toResource(rows[0], 'u'),
            [Instrument.toResource(row, 'i') for row in rows],
            [UserInstruments.toResource(row, 'ui') for row in rows]
        )
        
    def get_all(self, cursor: sqlite3.Cursor) -> List[User]:
        return getSome(User, cursor, 'SELECT id, name FROM users ORDER BY name COLLATE NOCASE')
    
    def update(self, cursor: sqlite3.Cursor, id: int, name: str) -> User:
        return update(User, cursor, 'UPDATE users SET name=? WHERE id=? RETURNING id, name', (name, id))
        
    def delete(self, cursor: sqlite3.Cursor, id: int) -> None:
        cursor.execute('DELETE FROM users WHERE id=?', (id,))
        return
    
    def get_dates_user(self, cursor: sqlite3.Cursor, user_id: int) -> DatesUser:
        rows = cursor.execute(f"""SELECT
                {fields(user.FIELDS, 'u')},
                {fields(date.FIELDS, 'd')},
                {fields(answer.FIELDS, 'a')}
            FROM users as u
            LEFT JOIN dates as d
            LEFT JOIN answers as a
                ON a.date_id = d.id
                AND a.user_id = u.id
            WHERE u.id = ?
            ORDER BY d.date, d.time
            """, (user_id,)).fetchall()
        return DatesUser(
            user = User.toResource(rows[0], 'u'),
            answers = [Answer.toResource(row, 'a') for row in rows if field(row, 'id', 'a') != None],
            dates = [Date.toResource(row, 'd') for row in rows] if field(rows[0], 'id', 'd') != None else []
        )