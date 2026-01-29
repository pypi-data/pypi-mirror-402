import sqlite3

from popoll_backend.db.model.option import Option
from popoll_backend.db.query.option_queries import OptionQueries
from popoll_backend.usecases.poll import PollQuery


class UpdatePoll(PollQuery):
    
    name: str
    color: str
    
    def __init__(self, poll: str, name: str, color: str):
        super().__init__(poll)
        self.name = name
        self.color = color
        
    def process(self, cursor: sqlite3.Cursor) -> Option:
        return OptionQueries().update(cursor, self.name, self.color)
