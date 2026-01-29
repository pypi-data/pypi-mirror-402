from __future__ import annotations

import datetime
import sqlite3
from typing import List, Optional

from popoll_backend.db import getOne, getSome, insert, update
from popoll_backend.db.model import date, field, fields
from popoll_backend.db.model import user
from popoll_backend.db.model import answer
from popoll_backend.db.model import instrument
from popoll_backend.db.model import user_instruments
from popoll_backend.db.model.answer import Answer
from popoll_backend.db.model.date import Date
from popoll_backend.db.model.instrument import Instrument
from popoll_backend.db.model.user import User
from popoll_backend.db.model.user_instruments import UserInstruments
from popoll_backend.model.output import EMPTY
from popoll_backend.usecases.poll.date.date_details import DateDetails

def isOlder(actualDate: datetime.date, compare: datetime.date=datetime.date.today()):
    return actualDate < compare

class DateQueries:
    
    def create(self, cursor: sqlite3.Cursor, title: str, date: datetime.date, time: Optional[datetime.time], end_time: Optional[datetime.time], is_frozen: bool) -> Date:
        return insert(Date, cursor, 'INSERT INTO dates(title, date, time, end_time, is_frozen) VALUES (?, ?, ?, ?, ?) RETURNING id, title, date, time, end_time, is_frozen', (title, date, time, end_time, is_frozen))
    
    def get(self, cursor: sqlite3.Cursor, id: int) -> Date:
        return getOne(Date, cursor, 'SELECT id, title, date, time, end_time, is_frozen FROM dates WHERE id=? LIMIT 1', (id,))
    
    def get_all(self, cursor: sqlite3.Cursor) -> List[Date]:
        return getSome(Date, cursor, 'SELECT id, title, date, time, end_time, is_frozen FROM dates ORDER BY date, time')
    
    def get_date_details(self, cursor: sqlite3.Cursor, id: int) -> DateDetails:        
        rows = cursor.execute(f"""
            SELECT 
                {fields(date.FIELDS, 'd')},
                {fields(user.FIELDS, 'u')},
                {fields(answer.FIELDS, 'a')},
                {fields(instrument.FIELDS, 'i')},
                {fields(user_instruments.FIELDS, 'ui')}
            FROM users as u
            LEFT JOIN dates as d
            LEFT JOIN answers as a
                ON a.date_id = d.id
                AND a.user_id = u.id
            INNER JOIN user_instruments as ui
                ON u.id = ui.user_id
            INNER JOIN instruments as i
                ON i.id = ui.instrument_id
            WHERE d.id = ?
            """, (id,)).fetchall()
        return DateDetails(
            date = Date.toResource(rows[0], 'd'),
            answers = [Answer.toResource(row, 'a') for row in rows],
            users = list(set([User.toResource(row, 'u') for row in rows])),
            instruments = list(set([Instrument.toResource(row, 'i') for row in rows])),
            user_instruments = [UserInstruments.toResource(row, 'ui') for row in rows]
        )
        
    def update(self, cursor: sqlite3.Cursor, id: int, title: str, date: datetime.date, time: Optional[datetime.time], end_time: Optional[datetime.time], is_frozen: bool) -> Date:
        return update(Date, cursor, 'UPDATE dates SET title=?, date=?, time=?, end_time=?, is_frozen=? WHERE id=? RETURNING id, title, date, time, end_time, is_frozen', (title, date, time, end_time, is_frozen, id,))
        
    def delete(self, cursor: sqlite3.Cursor, id: int) -> None:
        cursor.execute('DELETE FROM dates WHERE id=?', (id,))
        return
    
    def delete_old_dates(self, cursor: sqlite3.Cursor, dateBefore: datetime.date) -> None:
        cursor.execute('DELETE FROM dates WHERE date < ?', (dateBefore,))