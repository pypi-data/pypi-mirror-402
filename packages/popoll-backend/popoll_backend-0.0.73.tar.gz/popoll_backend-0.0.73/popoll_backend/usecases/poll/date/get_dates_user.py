import sqlite3

from popoll_backend.db.query.user_queries import UserQueries
from popoll_backend.usecases.poll import PollQuery
from popoll_backend.usecases.poll.user.dates_user import DatesUser

class GetDatesUser(PollQuery):
    
    id: int
    
    def __init__(self, poll: str, id: int):
        super().__init__(poll)
        self.id = id
    
    def process(self, cursor: sqlite3.Cursor) -> DatesUser:
        return UserQueries().get_dates_user(cursor, self.id)
