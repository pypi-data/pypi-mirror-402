import sqlite3

from popoll_backend.db.model.date import Date
from popoll_backend.db.query.date_queries import DateQueries
from popoll_backend.usecases.poll import PollQuery

class GetDate(PollQuery):
    
    id: int
    
    def __init__(self, poll: str, id: int):
        super().__init__(poll)
        self.id = id

    def process(self, cursor: sqlite3.Cursor) -> Date:
        return DateQueries().get(cursor, self.id)
