import sqlite3
from typing import Any, List, Type

import flask


def _execute(cursor: sqlite3.Cursor, query: str, params: Any=None) -> sqlite3.Cursor:
    return cursor.execute(query, params) if params else cursor.execute(query)

def insert(type: Type, cursor: sqlite3.Cursor, query: str, params: Any=None) -> Any:
    return type.toResource(_execute(cursor, query, params).fetchone())

def getOne(type: Type, cursor: sqlite3.Cursor, query: str, params: Any=None) -> type:
    row = _execute(cursor, query, params).fetchone()
    if row == None or len(row) == 0:
        flask.abort(404, f'{type} with id=[{id}] not found')
    return type.toResource(row)

def getSome(type: Type, cursor: sqlite3.Cursor, query: str, params: Any=None) -> List[type]:
    rows = _execute(cursor, query, params).fetchall()
    # if rows == None or len(rows) == 0:
    #     flask.abort(404, f'{type} with id=[{id}] not found')
    return [type.toResource(row) for row in rows]

def update(type: Type, cursor: sqlite3.Cursor, query: str, params: Any=None) -> type:
    return type.toResource(_execute(cursor, query, params).fetchone())
