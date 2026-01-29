import os
import sqlite3
from typing import Any, Optional
import flask

from popoll_backend.usecases import _Query
from popoll_backend.utils import toJSON


class PollQuery(_Query):
    
    fail_if_db_exists: bool = False
    fail_if_db_not_exists: bool = True
    
    def __init__(self, poll: str):
        self.poll = poll
        self.db_file = f'{poll}.db'
        if self.fail_if_db_exists and os.path.exists(self.db_file):
            flask.abort(409, f'The poll [{poll}] already exists.')
        if self.fail_if_db_not_exists and not os.path.exists(self.db_file):
            flask.abort(400, f'The poll [{poll}] does not exist.')
    
    def run(self, cursor: Optional[sqlite3.Cursor]=None) -> Any:
        if cursor:
            return self._run(cursor)
        else:
            with sqlite3.connect(self.db_file) as connection:
                connection.row_factory = sqlite3.Row
                _cursor: sqlite3.Cursor = connection.cursor()
                _cursor.execute("PRAGMA foreign_keys = ON")
                # _cursor.execute("ATTACH DATABASE 'instruments.db' AS instruments;")
                return toJSON(self._run(_cursor))
                # return self._run(_cursor)
            
    def _run(self, cursor: sqlite3.Cursor) -> Any:
        try:
            return self.process(cursor)
        except sqlite3.Error as e:
            print(e)
            self.error(e)
            if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
                flask.abort(400, f'ForeignKey error. You refer to a not existing resource')
            if e.sqlite_errorcode == sqlite3.SQLITE_ERROR:
                flask.abort(500, 'Unknown DB error')
            flask.abort(500, 'Unknown server error')
    
    def process(self, cursor: sqlite3.Cursor) -> None:
        raise NotImplementedError()
    
    def buildResponse(self, cursor: sqlite3.Cursor) -> Any:
        raise NotImplementedError()
    
    def error(self, e: sqlite3.Error) -> None:
        pass