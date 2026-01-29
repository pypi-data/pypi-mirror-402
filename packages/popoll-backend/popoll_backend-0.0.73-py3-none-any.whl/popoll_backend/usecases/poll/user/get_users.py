import sqlite3
from typing import List

from popoll_backend.db.model.user import User
from popoll_backend.db.query.user_queries import UserQueries
from popoll_backend.usecases.poll import PollQuery

class GetUsers(PollQuery):
    
    def __init__(self, poll: str):
        super().__init__(poll)
    
    def process(self, cursor: sqlite3.Cursor) -> List[User]:
        return UserQueries().get_all(cursor)
