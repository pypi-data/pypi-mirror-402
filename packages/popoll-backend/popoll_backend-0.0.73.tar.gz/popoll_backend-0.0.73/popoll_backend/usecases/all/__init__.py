import glob
import sqlite3
from popoll_backend.model.output import EMPTY, Empty
from popoll_backend.usecases import _Query
from popoll_backend.utils import toJSON


class Query(_Query):
    
    def run(self) -> Empty:
        answers = []
        for db in sorted(glob.glob('*.db')):
            # We do not want to break in case a db is incorrect
            try:
                with sqlite3.connect(db) as connection:
                    cursor: sqlite3.Cursor = connection.cursor()
                    answers.append(self.process(db[0:-3], cursor))
            except Exception as e:
                print(e)
        return toJSON(list(filter(lambda t: not t is None, answers)))
    
    def process(self, db: str, cursor: sqlite3.Cursor) -> None:
        raise NotImplementedError()