import sqlite3

from popoll_backend.usecases.poll.poll.poll import Poll
from popoll_backend.usecases.all import Query


class GetAllSession(Query):
    
    id: str
    
    def __init__(self, id: str):
        self.id = id
        
    def process(self, db: str, cursor: sqlite3.Cursor) -> None:
        if cursor.execute('SELECT COUNT(*) FROM sessions WHERE session_id=?', (self.id,)).fetchone()[0] > 0:
            return Poll(db, cursor.execute('SELECT name FROM options').fetchone()[0])
        else:
            return None
    