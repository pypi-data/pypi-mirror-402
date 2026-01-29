import sqlite3

from popoll_backend.db.model.session import Session
from popoll_backend.db.query.session_queries import SessionQueries
from popoll_backend.usecases.poll import PollQuery

class GetSession(PollQuery):
    
    id: int
    
    def __init__(self, poll: str, id: str):
        super().__init__(poll)
        self.id = id

    def process(self, cursor: sqlite3.Cursor) -> Session:
        return SessionQueries().get(cursor, self.id)
