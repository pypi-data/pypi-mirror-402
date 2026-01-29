import sqlite3
from typing import List

from popoll_backend.db.model.date import Date
from popoll_backend.db.query.date_queries import DateQueries
from popoll_backend.usecases.poll import PollQuery


class GetDates(PollQuery):
    
    dates: List[Date]
    
    def __init__(self, poll: str):
        super().__init__(poll)

    def process(self, cursor: sqlite3.Cursor) -> List[Date]:
        return DateQueries().get_all(cursor)
