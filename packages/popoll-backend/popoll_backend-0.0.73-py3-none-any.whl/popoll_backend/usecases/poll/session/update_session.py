import sqlite3

from popoll_backend.db.model.session import Session
from popoll_backend.db.query.session_queries import SessionQueries
from popoll_backend.usecases.poll import PollQuery


class UpdateSession(PollQuery):
    
    session_id: int
    
    def __init__(self, poll: str, session_id: str, user_id: int):
        super().__init__(poll)
        self.session_id = session_id
        self.user_id = user_id

    def process(self, cursor: sqlite3.Cursor) -> Session:
        return SessionQueries().update(cursor, self.session_id, self.user_id)
