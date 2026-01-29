import sqlite3
from typing import List

from popoll_backend.db.model.answer import Answer
from popoll_backend.db.model.date import Date
from popoll_backend.db.model.instrument import Instrument
from popoll_backend.db.model.option import Option
from popoll_backend.db.model.session import Session
from popoll_backend.db.model.user import User
from popoll_backend.db.model.user_instruments import UserInstruments
from popoll_backend.db.query.instrument_queries import InstrumentQueries
from popoll_backend.db.query.option_queries import OptionQueries
from popoll_backend.model.output import EMPTY, Empty
from popoll_backend.usecases.poll import PollQuery


class CreatePoll(PollQuery):
    
    fail_if_db_exists: bool = True
    fail_if_db_not_exists: bool = False
    
    name: str
    instruments: List[str]
    color: str
    
    def __init__(self, poll:str, name: str, instruments: List[str], color: str):
        super().__init__(poll)
        self.name = name
        self.instruments = instruments
        self.color = color
    
    def process(self, cursor: sqlite3.Cursor) -> Empty:
        cursor.execute(Option.create_table())
        OptionQueries().create(cursor, self.name, self.color)
        cursor.execute(Date.create_table())
        cursor.execute(Instrument.create_table())
        
        instrumentQueries: InstrumentQueries = InstrumentQueries()
        instrumentQueries.create(cursor, 'Tamborim', 1)
        instrumentQueries.create(cursor, 'Agogo', 2)
        instrumentQueries.create(cursor, 'Chocalho', 3)
        instrumentQueries.create(cursor, 'Repinique', 4)
        instrumentQueries.create(cursor, 'Caixa', 5)
        instrumentQueries.create(cursor, 'Primeira', 6)
        instrumentQueries.create(cursor, 'Segunda', 7)
        instrumentQueries.create(cursor, 'Terceira', 8)
        instrumentQueries.create(cursor, 'Timbal', 9)
        cursor.execute(User.create_table())
        cursor.execute(Answer.create_table())
        cursor.execute(UserInstruments.create_table())
        cursor.execute(Session.create_table())
        return EMPTY