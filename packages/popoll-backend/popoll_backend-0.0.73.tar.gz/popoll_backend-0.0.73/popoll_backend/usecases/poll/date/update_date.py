import datetime
import sqlite3
from typing import Optional

from popoll_backend.db.model.date import Date
from popoll_backend.db.query.date_queries import DateQueries
from popoll_backend.usecases.poll import PollQuery

class UpdateDate(PollQuery):
    
    id: int
    title: str
    date: datetime.date
    time: Optional[datetime.time]
    end_time: Optional[datetime.time]
    is_frozen: bool
    
    def __init__(self, poll: str, id: int, title: str, date: datetime.date, time: Optional[datetime.time], end_time: Optional[datetime.time], is_frozen: bool):
        super().__init__(poll)
        self.id = id
        self.title = title
        self.date = date
        self.time = time
        self.end_time = end_time
        self.is_frozen = is_frozen
        
    def process(self, cursor: sqlite3.Cursor) -> Date:
        return DateQueries().update(cursor, self.id, self.title, self.date, self.time, self.end_time, self.is_frozen)
