import sqlite3
from typing import Any, List, Optional

def field(row: sqlite3.Row, column: str, prefix: Optional[str]=None) -> Any:
    if prefix != None:
        return row[f'{prefix}.{column}']
    else:
        return row[column]
    
def fields(fields: List[str], prefix: Optional[str]=None):
    if prefix != None:
        return ', '.join([f'{prefix}.{field} AS "{prefix}.{field}"' for field in fields])
    else:
        return ', '.join(fields)