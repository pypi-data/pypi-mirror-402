import sqlite3

from popoll_backend.db.model.instrument import Instrument
from popoll_backend.db.query.instrument_queries import InstrumentQueries
from popoll_backend.usecases.poll import PollQuery

class GetInstrument(PollQuery):
    
    id: int
    
    def __init__(self, poll: str, id: int):
        super().__init__(poll)
        self.id = id
    
    def process(self, cursor: sqlite3.Cursor) -> Instrument:
        return InstrumentQueries().get(cursor, self.id)
