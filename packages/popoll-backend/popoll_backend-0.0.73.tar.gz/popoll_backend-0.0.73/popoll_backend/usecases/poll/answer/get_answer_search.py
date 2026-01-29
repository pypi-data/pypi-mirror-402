import sqlite3

import flask

from popoll_backend.db.model.answer import Answer
from popoll_backend.db.query.answer_queries import AnswerQueries
from popoll_backend.usecases.poll import PollQuery

class GetAnswerSearch(PollQuery):
    
    userId: int
    dateId: int
    
    def __init__(self, poll: str, userId: int, dateId: int):
        super().__init__(poll)
        self.userId = userId
        self.dateId = dateId

    def process(self, cursor: sqlite3.Cursor) -> Answer:
        return AnswerQueries().get_search(cursor, self.userId, self.dateId)
