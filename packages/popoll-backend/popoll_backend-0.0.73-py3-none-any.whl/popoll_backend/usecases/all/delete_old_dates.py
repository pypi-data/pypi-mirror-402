import datetime
import sqlite3

from popoll_backend.db.query.date_queries import DateQueries
from popoll_backend.usecases.all import Query

def dateBefore(day=datetime.date.today(), years: int=0, days: int=0):
    today = day.isoformat()
    beforeYears = today[0:3] + str(int(today[3])-years) + today[4:] # big hack to replace year in string to get rid of bissectil years
    return (datetime.date.fromisoformat(beforeYears) - datetime.timedelta(days=days))

def dateAfter(day=datetime.date.today(), years: int=0, days: int=0):
    today = day.isoformat()
    afterYears = today[0:3] + str(int(today[3])+years) + today[4:] # big hack to replace year in string to get rid of bissectil years
    return (datetime.date.fromisoformat(afterYears) + datetime.timedelta(days=days))

NEXT_DAY = dateAfter(days=1).isoformat()

class DeleteOldDates(Query):
    
    past = dateBefore(years=1)
    
    def process(self, db: str, cursor: sqlite3.Cursor) -> None:
        DateQueries().delete_old_dates(cursor, dateBefore(years=1))
