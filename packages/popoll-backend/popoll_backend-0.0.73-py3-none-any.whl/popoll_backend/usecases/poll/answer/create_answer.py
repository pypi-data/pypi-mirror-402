import sqlite3

import flask

from popoll_backend.db.model.answer import Answer
from popoll_backend.db.query.answer_queries import AnswerQueries
from popoll_backend.usecases.poll import PollQuery
from popoll_backend.usecases.poll.date import is_date_frozen


class CreateAnswer(PollQuery):
    
    user_id: int
    date_id: int
    
    id: int
    
    def __init__(self, poll:str, user_id: int, date_id: int):
        super().__init__(poll)
        self.user_id = user_id
        self.date_id = date_id
    
    def process(self, cursor: sqlite3.Cursor) -> Answer:
        if is_date_frozen(cursor, self.date_id):
            flask.abort(403, 'Date is frozen. Cannot modify')
        return AnswerQueries().create(cursor, self.user_id, self.date_id, True)
    
    def error(self, e: sqlite3.Error):
        if isinstance(e, sqlite3.IntegrityError):
            if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                flask.abort(409, f'Answer for this user already exists. PUT should be triggered instead.')
