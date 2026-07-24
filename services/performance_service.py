from __future__ import annotations
from functools import lru_cache
from repositories.database import connect, init_db

@lru_cache(maxsize=128)
def cached_event_counts(event_id:int)->dict:
    init_db()
    with connect() as conn:
        guests=conn.execute('SELECT COUNT(*) c FROM guests WHERE event_id=?',(event_id,)).fetchone()['c']
        messages=conn.execute('SELECT COUNT(*) c FROM messages WHERE event_id=?',(event_id,)).fetchone()['c']
    return {'guests':guests,'messages':messages}

def paginate_query(sql:str, params:tuple=(), limit:int=100, offset:int=0)->list[dict]:
    init_db()
    with connect() as conn:
        return [dict(r) for r in conn.execute(f'{sql} LIMIT ? OFFSET ?', (*params, min(limit,500), offset)).fetchall()]
