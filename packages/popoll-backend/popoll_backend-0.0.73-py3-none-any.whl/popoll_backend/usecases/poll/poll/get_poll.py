import sqlite3

from popoll_backend.db.model.option import Option
from popoll_backend.db.query.option_queries import OptionQueries
from popoll_backend.usecases.poll import PollQuery


class GetPoll(PollQuery):
    
    def __init__(self, poll: str):
        super().__init__(poll)

    def process(self, cursor: sqlite3.Cursor) -> Option:
        return OptionQueries().get(cursor)
