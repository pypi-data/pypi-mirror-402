import sqlite3
import flask


def is_date_frozen(cursor: sqlite3.Cursor, date_id: int) -> bool:
    res = cursor.execute('SELECT is_frozen FROM dates WHERE id=?', (date_id,)).fetchone()
    if res != None and len(res) > 0:
        return res[0]
    else:
        flask.abort(400, 'Not found')

def is_answer_frozen(cursor: sqlite3.Cursor, answer_id: int) -> bool:
    res = cursor.execute('SELECT is_frozen FROM dates WHERE id = (SELECT date_id FROM answers WHERE id=?)', (answer_id,)).fetchone()
    if res != None and len(res) > 0:
        return res[0]
    else:
        flask.abort(400, 'Not found')
    