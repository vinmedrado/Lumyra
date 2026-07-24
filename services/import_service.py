from __future__ import annotations
import io, re
from typing import Any
import pandas as pd
from repositories.database import connect, init_db
from services.phone_utils import normalize_phone

NAME_KEYS = ('nome','name','convidado','guest')
PHONE_KEYS = ('telefone','phone','celular','whatsapp','mobile')
GROUP_KEYS = ('grupo','group','familia','família')
INVITATION_KEYS = ('convite','nomeconvite','nome_do_convite','invitation','invitationlabel')
INVITATION_TYPE_KEYS = ('tipoconvite','tipo_convite','invitationtype')

def _pick_column(cols:list[str], keys:tuple[str,...])->str|None:
    norm={c: re.sub(r'[^a-z0-9]+','', c.lower()) for c in cols}
    for c,n in norm.items():
        if any(k.replace('í','i').replace('ê','e') in n for k in keys):
            return c
    return None

def _read_vcf(raw:bytes)->pd.DataFrame:
    text=raw.decode('utf-8', errors='ignore')
    items=[]; current={}
    for line in text.splitlines():
        if line.startswith('BEGIN:VCARD'): current={}
        elif line.startswith('FN:'): current['name']=line[3:].strip()
        elif line.upper().startswith('TEL'):
            current['phone']=line.split(':',1)[-1].strip()
        elif line.startswith('END:VCARD') and current.get('name'):
            items.append(current)
    return pd.DataFrame(items)

def preview_guest_file(raw:bytes, filename:str)->tuple[list[dict[str,Any]], dict[str,Any]]:
    lower=filename.lower()
    if lower.endswith('.vcf'):
        df=_read_vcf(raw)
    elif lower.endswith(('.xlsx','.xls')):
        df=pd.read_excel(io.BytesIO(raw))
    else:
        try: df=pd.read_csv(io.BytesIO(raw))
        except Exception: df=pd.read_csv(io.BytesIO(raw), sep=';')
    df=df.fillna('')
    cols=list(map(str, df.columns))
    name_col=_pick_column(cols, NAME_KEYS) or (cols[0] if cols else 'name')
    phone_col=_pick_column(cols, PHONE_KEYS)
    group_col=_pick_column(cols, GROUP_KEYS)
    invitation_col=_pick_column(cols, INVITATION_KEYS)
    invitation_type_col=_pick_column(cols, INVITATION_TYPE_KEYS)
    rows=[]; seen=set(); invalid=dupes=0
    for _,r in df.iterrows():
        name=str(r.get(name_col,'')).strip()
        phone=normalize_phone(str(r.get(phone_col,''))) if phone_col else ''
        group=str(r.get(group_col,'')) if group_col else ''
        invitation_label=str(r.get(invitation_col,'')) if invitation_col else (group or name)
        raw_type=str(r.get(invitation_type_col,'')) if invitation_type_col else ''
        invitation_type='family' if (raw_type.lower() in {'familia','família','family','grupo','group'} or (group and group != name)) else 'individual'
        valid=bool(name)
        key=(name.lower(), phone)
        if key in seen: dupes+=1
        seen.add(key)
        if not valid: invalid+=1
        rows.append({'name':name,'phone':phone,'group_name':group,'invitation_type':invitation_type,'invitation_label':invitation_label,'is_valid':valid,'is_duplicate_in_file': key in seen})
    report={'total':len(rows),'valid':sum(1 for r in rows if r['is_valid']),'invalid':invalid,'duplicates_in_file':dupes,'detected_columns':{'name':name_col,'phone':phone_col,'group':group_col,'invitation_label':invitation_col,'invitation_type':invitation_type_col}}
    return rows, report

def import_guest_rows(event_id:int, tenant_id:int, rows:list[dict[str,Any]], merge:bool=True)->dict[str,int]:
    init_db(); imported=updated=skipped=0
    with connect() as conn:
        for row in rows:
            name=(row.get('name') or '').strip()
            if not name: skipped+=1; continue
            phone=normalize_phone(row.get('phone') or '')
            existing=None
            if phone:
                existing=conn.execute('SELECT id FROM guests WHERE event_id=? AND phone=?', (event_id, phone)).fetchone()
            if existing and merge:
                conn.execute('UPDATE guests SET name=?, group_name=COALESCE(NULLIF(?,\'\'), group_name), tenant_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (name, row.get('group_name') or '', tenant_id, existing['id']))
                updated+=1
            else:
                conn.execute('INSERT INTO guests(event_id, tenant_id, name, phone, group_name, invitation_type, invitation_label) VALUES (?, ?, ?, ?, ?, ?, ?)', (event_id, tenant_id, name, phone, row.get('group_name') or '', row.get('invitation_type') or ('family' if row.get('group_name') else 'individual'), row.get('invitation_label') or row.get('group_name') or name))
                imported+=1
    return {'imported':imported,'updated':updated,'skipped':skipped}
