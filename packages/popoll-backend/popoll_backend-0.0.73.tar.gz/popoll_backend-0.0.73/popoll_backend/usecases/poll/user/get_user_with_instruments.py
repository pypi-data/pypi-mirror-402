import sqlite3

from popoll_backend.db.query.user_queries import UserQueries
from popoll_backend.usecases.poll import PollQuery
from popoll_backend.usecases.poll.user.user_with_instruments import UserWithInstruments

class GetUserWithInstruments(PollQuery):
    
    id: int
    
    def __init__(self, poll: str, id: int):
        super().__init__(poll)
        self.id = id
    
    def process(self, cursor: sqlite3.Cursor) -> UserWithInstruments:
        return UserQueries().getUserWithInstruments(cursor, self.id)
