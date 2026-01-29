import sqlite3
from popoll_backend.db.query.user_queries import UserQueries
from popoll_backend.model.output import EMPTY, Empty
from popoll_backend.usecases.poll import PollQuery


class DeleteUser(PollQuery):
    
    id: int
    
    def __init__(self, poll: str, id: int):
        super().__init__(poll)
        self.id = id
    
    def process(self, cursor: sqlite3.Cursor) -> Empty:
        UserQueries().delete(cursor, self.id)
        return EMPTY
