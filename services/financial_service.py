from __future__ import annotations
import pandas as pd
from repositories.database import connect, init_db

VENDOR_CATEGORIES = ["buffet", "decoracao", "musica", "foto_video", "espaco", "transporte", "vestuario", "papelaria", "outro"]
EXPENSE_STATUSES = ["pending", "paid", "overdue", "canceled"]

def add_vendor(event_id:int, name:str, category:str="outro", phone:str="", notes:str="") -> int:
    init_db(); category = category if category in VENDOR_CATEGORIES else "outro"
    with connect() as conn:
        cur=conn.execute("INSERT INTO vendors(event_id,name,category,phone,notes) VALUES(?,?,?,?,?)", (int(event_id),name.strip(),category,phone.strip(),notes.strip()))
        return int(cur.lastrowid)

def update_vendor(event_id:int, vendor_id:int, name:str, category:str="outro", phone:str="", notes:str="") -> None:
    init_db(); category = category if category in VENDOR_CATEGORIES else "outro"
    with connect() as conn:
        conn.execute("UPDATE vendors SET name=?, category=?, phone=?, notes=? WHERE id=? AND event_id=?", (name.strip(), category, phone.strip(), notes.strip(), int(vendor_id), int(event_id)))

def delete_vendor(event_id:int, vendor_id:int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("UPDATE expenses SET vendor_id=NULL WHERE vendor_id=? AND event_id=?", (int(vendor_id), int(event_id)))
        conn.execute("DELETE FROM vendors WHERE id=? AND event_id=?", (int(vendor_id), int(event_id)))

def list_vendors(event_id:int)->pd.DataFrame:
    init_db()
    with connect() as conn:
        rows=conn.execute("SELECT * FROM vendors WHERE event_id=? ORDER BY category, name",(int(event_id),)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def add_expense(event_id:int, vendor_id:int|None, description:str, amount:float, status:str="pending", due_date:str="", paid_at:str="", receipt_path:str="") -> int:
    init_db(); status = status if status in EXPENSE_STATUSES else "pending"
    with connect() as conn:
        cur=conn.execute("""INSERT INTO expenses(event_id,vendor_id,description,amount,status,due_date,paid_at,receipt_path)
                          VALUES(?,?,?,?,?,?,?,?)""",(int(event_id),vendor_id,description.strip(),float(amount or 0),status,due_date,paid_at,receipt_path))
        return int(cur.lastrowid)

def update_expense(event_id:int, expense_id:int, vendor_id:int|None, description:str, amount:float, status:str="pending", due_date:str="", paid_at:str="", receipt_path:str="") -> None:
    init_db(); status = status if status in EXPENSE_STATUSES else "pending"
    with connect() as conn:
        conn.execute("""UPDATE expenses SET vendor_id=?, description=?, amount=?, status=?, due_date=?, paid_at=?, receipt_path=?, updated_at=CURRENT_TIMESTAMP
                       WHERE id=? AND event_id=?""", (vendor_id, description.strip(), float(amount or 0), status, due_date, paid_at, receipt_path, int(expense_id), int(event_id)))

def delete_expense(event_id:int, expense_id:int) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM payments WHERE expense_id=?", (int(expense_id),))
        conn.execute("DELETE FROM expenses WHERE id=? AND event_id=?", (int(expense_id), int(event_id)))

def list_expenses(event_id:int, vendor_id:int|None=None, category:str|None=None, status:str|None=None)->pd.DataFrame:
    init_db()
    sql="""SELECT e.*, v.name AS vendor_name, v.category AS vendor_category, v.phone AS vendor_phone
           FROM expenses e LEFT JOIN vendors v ON v.id=e.vendor_id WHERE e.event_id=?"""
    params=[int(event_id)]
    if vendor_id:
        sql += " AND e.vendor_id=?"; params.append(int(vendor_id))
    if category and category != "Todos":
        sql += " AND COALESCE(v.category,'outro')=?"; params.append(category)
    if status and status != "Todos":
        sql += " AND e.status=?"; params.append(status)
    sql += " ORDER BY e.due_date IS NULL, e.due_date, e.id DESC"
    with connect() as conn:
        rows=conn.execute(sql,tuple(params)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def register_payment(event_id:int, expense_id:int, amount:float, paid_at:str) -> None:
    init_db()
    with connect() as conn:
        conn.execute("INSERT INTO payments(expense_id, amount, paid_at) VALUES(?,?,?)", (int(expense_id), float(amount or 0), paid_at))
        conn.execute("UPDATE expenses SET status='paid', paid_at=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND event_id=?", (paid_at, int(expense_id), int(event_id)))

def summary(event_id:int, total_guests:int=0, confirmed_guests:int=0)->dict:
    df=list_expenses(event_id)
    if df.empty:
        total=paid=pending=overdue=0.0
    else:
        total=float(df[df['status']!='canceled']['amount'].fillna(0).sum())
        paid=float(df[df['status']=='paid']['amount'].fillna(0).sum())
        pending=float(df[df['status']=='pending']['amount'].fillna(0).sum())
        overdue=float(df[df['status']=='overdue']['amount'].fillna(0).sum())
    return {"total_contratado":total,"total_gasto":total,"total_pago":paid,"total_pendente":pending,"total_vencido":overdue,"custo_por_convidado": total/max(1,int(total_guests or 0)),"custo_por_confirmado": total/max(1,int(confirmed_guests or 0))}

def export_expenses_csv(event_id:int, **filters) -> str:
    df=list_expenses(event_id, **filters)
    return df.to_csv(index=False, encoding='utf-8-sig') if not df.empty else ''
