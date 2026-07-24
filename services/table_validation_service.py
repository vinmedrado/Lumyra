from __future__ import annotations
import pandas as pd
from repositories.database import list_tables, load_guests_df

def get_table_occupancy(event_id:int) -> pd.DataFrame:
    guests=load_guests_df(event_id); tables=list_tables(event_id)
    if tables.empty:
        return pd.DataFrame(columns=['mesa','capacidade','ocupacao','percentual','status'])
    counts = guests.groupby('mesa_final').size().to_dict() if not guests.empty and 'mesa_final' in guests else {}
    rows=[]
    for _, t in tables.fillna('').iterrows():
        cap = int(t.get('capacity') or 0)
        occ = int(counts.get(str(t.get('name')),0))
        pct = (occ/cap*100) if cap else 0
        status = 'acima_capacidade' if cap and occ>cap else ('cheia' if cap and occ==cap else 'ok')
        rows.append({'mesa':t.get('name'),'capacidade':cap,'ocupacao':occ,'percentual':pct,'status':status})
    return pd.DataFrame(rows)

def guests_without_table(event_id:int)->pd.DataFrame:
    df=load_guests_df(event_id)
    if df.empty: return pd.DataFrame()
    return df[df['mesa_final'].fillna('').astype(str).str.strip().eq('')]

def tables_over_capacity(event_id:int)->pd.DataFrame:
    occ=get_table_occupancy(event_id)
    return occ[occ['status']=='acima_capacidade'] if not occ.empty else occ

def separated_groups(event_id:int)->pd.DataFrame:
    df=load_guests_df(event_id)
    if df.empty or 'grupo' not in df: return pd.DataFrame(columns=['grupo','mesas','sugestao'])
    valid=df[df['grupo'].fillna('').astype(str).str.strip().ne('') & df['mesa_final'].fillna('').astype(str).str.strip().ne('')]
    rows=[]
    for grupo, g in valid.groupby('grupo'):
        mesas=sorted(set(g['mesa_final'].astype(str)))
        if len(mesas)>1:
            rows.append({'grupo':grupo,'mesas':', '.join(mesas),'sugestao':f'Agrupar família/grupo {grupo} em uma única mesa ou mesas próximas.'})
    return pd.DataFrame(rows)

def export_table_map_csv(event_id:int)->str:
    df=load_guests_df(event_id)
    cols=[c for c in ['id','nome_original','grupo','mesa_final','telefone'] if c in df.columns]
    return df[cols].to_csv(index=False, encoding='utf-8-sig') if not df.empty else ''

def count_critical_table_conflicts(event_id:int)->int:
    return len(guests_without_table(event_id)) + len(tables_over_capacity(event_id)) + len(separated_groups(event_id))
