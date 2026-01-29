import os
import sqlite3
from typing import Any, Optional

import flask
from popoll_backend.model.output import EMPTY
from popoll_backend.usecases.poll import PollQuery
from popoll_backend.utils import toJSON


class DeletePoll(PollQuery):
    
    def __init__(self, poll: str):
        super().__init__(poll)
    
    def run(self, cursor: Optional[sqlite3.Cursor]=None) -> Any:
        try:
            os.remove(f'{self.poll}.db')
            return toJSON(EMPTY)
        except FileNotFoundError:
            flask.abort(406, 'Poll does not exist')