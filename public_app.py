from __future__ import annotations
from html import escape
from urllib.parse import parse_qs
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from repositories.database import init_db
from services.guest_portal_service import get_guest_portal_context, submit_guest_response
from services.form_service import ensure_default_form, get_guest_answers, list_fields, save_response

init_db(); app = FastAPI(title='Lumyra Guest Portal')

def page(title:str, body:str)->HTMLResponse:
    return HTMLResponse(f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>{escape(title)}</title><style>
    body{{margin:0;font-family:Inter,Arial,sans-serif;background:radial-gradient(circle at 20% 0%,rgba(139,92,246,.20),transparent 28%),linear-gradient(135deg,#F7F8FB,#FFF8E8);color:#181210}}.wrap{{max-width:900px;margin:0 auto;padding:18px}}.card{{background:white;border:1px solid #e6ddf8;border-radius:28px;padding:28px;box-shadow:0 24px 70px rgba(80,52,30,.12)}}h1{{font-size:clamp(30px,7vw,48px);line-height:1;margin:0 0 12px}}label{{display:block;font-weight:900;margin:16px 0 7px}}input,select,textarea{{width:100%;padding:15px;border:1px solid #d7c7b7;border-radius:16px;font-size:16px}}textarea{{min-height:90px}}button{{margin-top:22px;width:100%;padding:17px;border:0;border-radius:18px;background:#4B1D95;color:white;font-weight:950;font-size:17px}}.muted{{color:#667085;line-height:1.58}}.ok{{color:#107c41}}.err{{color:#b42318}}.box{{border:1px solid #f1dfcd;border-radius:18px;padding:14px;background:#F1ECFF;margin:14px 0}}
    </style></head><body><div class='wrap'><div class='card'>{body}</div></div></body></html>""")

def selected(value, current): return ' selected' if str(value)==str(current) else ''

def guest_form(token:str):
    ctx=get_guest_portal_context(token)
    if not ctx.get('ok'): return page('Link indisponível', f"<h1>Link indisponível</h1><p class='err'>{escape(ctx.get('error','Erro'))}</p>")
    link=ctx['link']; prev=ctx.get('previous_response') or {}; answers=prev.get('dynamic_answers') or {}
    guest_name=escape(str(link.get('guest_name') or link.get('name') or 'Convidado(a)')); event_name=escape(str(link.get('event_name') or 'Evento'))
    form_id=ensure_default_form(int(link['event_id'])); fields=list_fields(form_id, active_only=True)
    dynamic=''
    for field in fields.to_dict('records') if not fields.empty else []:
        fid=int(field['id']); label=escape(str(field.get('label') or 'Campo')); req=' required' if int(field.get('required') or 0) else ''; name=f'field_{fid}'; value=escape(str(answers.get(fid,'') or '')); ftype=field.get('type')
        if ftype=='boolean': dynamic += f"<label>{label}</label><select name='{name}'{req}><option value='Não'{selected('Não',value)}>Não</option><option value='Sim'{selected('Sim',value)}>Sim</option></select>"
        elif ftype=='select':
            opts=''.join([f"<option value='{escape(o.strip())}'{selected(o.strip(),value)}>{escape(o.strip())}</option>" for o in str(field.get('options') or '').split(',') if o.strip()]) or "<option value=''>Selecione</option>"
            dynamic += f"<label>{label}</label><select name='{name}'{req}>{opts}</select>"
        else: dynamic += f"<label>{label}</label><input name='{name}' value='{value}' placeholder='Digite sua resposta'{req}/>"
    body=f"""<h1>{event_name}</h1><p class='muted'>Olá, <b>{guest_name}</b>. Confirme presença e atualize suas informações.</p><div class='box'>Status atual: <b>{escape(str(prev.get('confirm_presence') or 'pendente'))}</b></div><form method='post'>
    <label>Você confirma presença?</label><select name='confirm_presence' required><option value='confirmed'{selected('confirmed',prev.get('confirm_presence'))}>Sim, confirmo presença</option><option value='declined'{selected('declined',prev.get('confirm_presence'))}>Não poderei comparecer</option><option value='maybe'{selected('maybe',prev.get('confirm_presence'))}>Talvez / ainda vou confirmar</option></select>
    <label>Telefone / WhatsApp</label><input name='phone' value='{escape(str(prev.get('phone') or link.get('guest_phone') or ''))}' />
    <label>Quantidade de acompanhantes</label><input type='number' min='0' name='companions_count' value='{escape(str(prev.get('companions_count') or 0))}' />
    <label>Vai precisar de ônibus?</label><select name='needs_bus'><option value='0'{selected(0,prev.get('needs_bus'))}>Não</option><option value='1'{selected(1,prev.get('needs_bus'))}>Sim</option></select>
    <label>Ponto de embarque</label><input name='bus_pickup_point' value='{escape(str(prev.get('bus_pickup_point') or ''))}' />
    <label>Restrições alimentares</label><textarea name='dietary_restrictions'>{escape(str(prev.get('dietary_restrictions') or ''))}</textarea>{dynamic}
    <label>Observações</label><textarea name='notes'>{escape(str(prev.get('notes') or ''))}</textarea><button type='submit'>Enviar confirmação</button></form>"""
    return page('Portal do Convidado', body)
app.get('/guest/{token}', response_class=HTMLResponse)(guest_form)

@app.post('/guest/{token}', response_class=HTMLResponse)
async def submit_form(token:str, request:Request):
    raw=(await request.body()).decode('utf-8', errors='ignore'); parsed={k:v[-1] if v else '' for k,v in parse_qs(raw).items()}
    result=submit_guest_response(token, parsed)
    if not result.get('ok'): return page('Não foi possível salvar', f"<h1>Não foi possível salvar</h1><p class='err'>{escape(result.get('error','Erro'))}</p>")
    guest_id=int(result['guest_id']); answers={int(k.replace('field_','')):v for k,v in parsed.items() if k.startswith('field_') and k.replace('field_','').isdigit()}
    if answers: save_response(guest_id, answers)
    rows=''.join(f"<li><b>{escape(k)}</b>: {escape(str(v))}</li>" for k,v in parsed.items() if not k.startswith('field_'))
    return page('Resposta recebida', f"<h1 class='ok'>Resposta recebida!</h1><p class='muted'>Suas informações foram salvas. Você pode voltar por este mesmo link enquanto o evento estiver aberto.</p><div class='box'><b>Resumo enviado</b><ul>{rows}</ul></div>")
