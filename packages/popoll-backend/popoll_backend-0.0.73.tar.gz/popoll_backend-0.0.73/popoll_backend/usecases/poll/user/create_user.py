import flask
import sqlite3
from typing import List

from popoll_backend.db.query.user_instruments_queries import UserInstrumentsQueries
from popoll_backend.db.query.user_queries import UserQueries
from popoll_backend.usecases.poll import PollQuery
from popoll_backend.usecases.poll.user.user_with_instruments import UserWithInstruments

class CreateUser(PollQuery):
    
    name: str
    main_instrument: int
    instruments: List[int]
    
    def __init__(self, poll: str, name: str, main_instrument: int, instruments: List[int]):
        super().__init__(poll)
        self.name = name
        self.main_instrument = main_instrument
        self.instruments = instruments
    
    def process(self, cursor: sqlite3.Cursor) -> UserWithInstruments:
        userQueries: UserQueries = UserQueries()
        user = userQueries.create(cursor, self.name)
        rows = [(self.main_instrument, True)] + [(instru, False) for instru in self.instruments if not instru == self.main_instrument]
        for row in rows:
            UserInstrumentsQueries().create(cursor, user.id, row[0], row[1])
        return userQueries.getUserWithInstruments(cursor, user.id)

    def error(self, e: sqlite3.Error):
        if isinstance(e, sqlite3.IntegrityError):
            if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                flask.abort(409, f'User with name {self.name} already exists.')