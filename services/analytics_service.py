from __future__ import annotations
from repositories.database import connect, init_db


def event_analytics(event_id:int)->dict:
    init_db()
    with connect() as conn:
        total=conn.execute('SELECT COUNT(*) c FROM guests WHERE event_id=?',(event_id,)).fetchone()['c']
        rsvp={r['status']:r['c'] for r in conn.execute('SELECT status, COUNT(*) c FROM guest_rsvp WHERE event_id=? GROUP BY status',(event_id,)).fetchall()}
        messages={r['status']:r['c'] for r in conn.execute('SELECT status, COUNT(*) c FROM messages WHERE event_id=? GROUP BY status',(event_id,)).fetchall()}
        groups=[dict(r) for r in conn.execute('SELECT COALESCE(group_name,\'Sem grupo\') group_name, COUNT(*) total FROM guests WHERE event_id=? GROUP BY group_name ORDER BY total DESC LIMIT 20',(event_id,)).fetchall()]
        tables=[dict(r) for r in conn.execute("SELECT COALESCE(final_table, corrected_table, current_table, 'Sem mesa') table_name, COUNT(*) occupied FROM guests WHERE event_id=? GROUP BY table_name ORDER BY occupied DESC",(event_id,)).fetchall()]
        exp=conn.execute("SELECT SUM(amount) total, SUM(CASE WHEN status='paid' THEN amount ELSE 0 END) paid FROM expenses WHERE event_id=?",(event_id,)).fetchone()
    confirmed=rsvp.get('confirmed',0)
    return {
        'total_guests':total,
        'confirmed':confirmed,
        'pending':rsvp.get('pending', max(total-confirmed-rsvp.get('declined',0),0)),
        'declined':rsvp.get('declined',0),
        'confirmation_rate': round((confirmed/total)*100,2) if total else 0,
        'campaign_response_rate': round(((messages.get('sent',0))/(sum(messages.values()) or 1))*100,2),
        'message_errors': messages.get('error',0),
        'guests_by_group': groups,
        'table_occupancy': tables,
        'cost_per_confirmed': round((float(exp['total'] or 0)/(confirmed or 1)),2),
        'financial': {'contracted': float(exp['total'] or 0), 'paid': float(exp['paid'] or 0)},
    }


def campaign_analytics(event_id:int)->dict:
    init_db()
    with connect() as conn:
        campaigns=[dict(r) for r in conn.execute('SELECT * FROM whatsapp_campaigns WHERE event_id=? ORDER BY id DESC',(event_id,)).fetchall()]
        recipients=[dict(r) for r in conn.execute('SELECT status, COUNT(*) c FROM whatsapp_campaign_recipients WHERE event_id=? GROUP BY status',(event_id,)).fetchall()]
        logs=[dict(r) for r in conn.execute('SELECT status, COUNT(*) c FROM message_logs WHERE event_id=? GROUP BY status',(event_id,)).fetchall()]
    return {'campaigns':campaigns,'recipients_by_status':recipients,'logs_by_status':logs}
