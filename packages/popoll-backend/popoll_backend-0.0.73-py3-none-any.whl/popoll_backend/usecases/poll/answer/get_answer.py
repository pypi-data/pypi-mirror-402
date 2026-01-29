import sqlite3

from popoll_backend.db.model.answer import Answer
from popoll_backend.db.query.answer_queries import AnswerQueries
from popoll_backend.usecases.poll import PollQuery


class GetAnswer(PollQuery):
    
    id: int
    
    def __init__(self, poll: str, id: int):
        super().__init__(poll)
        self.id = id

    def process(self, cursor: sqlite3.Cursor) -> Answer:
        return AnswerQueries().get(cursor, self.id)
