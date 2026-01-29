import sqlite3
from typing import List

from popoll_backend.db.model.instrument import Instrument
from popoll_backend.db.query.instrument_queries import InstrumentQueries
from popoll_backend.usecases.poll import PollQuery


class GetInstrumentsAll(PollQuery):
    
    instruments: List[Instrument]
    
    def __init__(self, poll: str):
        super().__init__(poll)

    def process(self, cursor: sqlite3.Cursor) -> List[Instrument]:
        return InstrumentQueries().getAll(cursor)
