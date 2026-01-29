import sqlite3
from typing import Optional

import flask

from popoll_backend.db.model.answer import Answer
from popoll_backend.db.query.answer_queries import AnswerQueries
from popoll_backend.usecases.poll import PollQuery
from popoll_backend.usecases.poll.date import is_answer_frozen

class UpdateAnswer(PollQuery):
    
    id: int
    response: bool
    
    
    def __init__(self, poll:str, id: int, response: Optional[bool]):
        super().__init__(poll)
        self.id = id
        self.response = response
    
    def process(self, cursor: sqlite3.Cursor) -> Answer:
        if is_answer_frozen(cursor, self.id):
            flask.abort(403, 'Date is frozen. Cannot modify')
        return AnswerQueries().update(cursor, self.id, self.response)
