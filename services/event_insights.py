from __future__ import annotations
from datetime import datetime, date
from repositories.database import get_event, get_rsvp, list_messages, load_guests_df
from services.financial_service import list_expenses
from services.document_service import list_documents
from services.guest_portal_service import responses_dashboard
from services.table_validation_service import guests_without_table, tables_over_capacity, separated_groups


def _ins(severity,title,message,action,related_page,count):
    return {"severity":severity,"title":title,"message":message,"action":action,"recommendation":action,"related_page":related_page,"count":int(count),"action_type":"open_page"}


def analyze_event(event_id:int) -> list[dict]:
    insights=[]
    guests=load_guests_df(event_id)
    total=0 if guests.empty else len(guests)
    no_table=guests_without_table(event_id)
    over=tables_over_capacity(event_id)
    sep=separated_groups(event_id)
    if len(no_table): insights.append(_ins('critical','Convidados sem mesa',f'{len(no_table)} convidado(s) ainda não têm mesa definida.','Definir mesa para os convidados pendentes.','Mesas',len(no_table)))
    if len(over): insights.append(_ins('critical','Mesa acima da capacidade',f'{len(over)} mesa(s) ultrapassaram a capacidade cadastrada.','Rebalancear ocupação das mesas.','Mesas',len(over)))
    if len(sep): insights.append(_ins('critical','Famílias/grupos separados',f'{len(sep)} grupo(s) aparecem em mesas diferentes.','Revisar agrupamento familiar.','Mesas',len(sep)))
    msgs_error=list_messages(event_id,'error')
    if not msgs_error.empty: insights.append(_ins('critical','Mensagens com erro',f'{len(msgs_error)} mensagem(ns) falharam no envio.','Reenfileirar mensagens com erro e revisar telefones.','Mensagens',len(msgs_error)))
    rsvp=get_rsvp(event_id)
    pending = 0 if rsvp.empty else int((rsvp['status']=='pending').sum())
    if pending: insights.append(_ins('warning','RSVP pendente',f'{pending} convidado(s) ainda não responderam.','Enviar lembrete com link do portal.','RSVP',pending))
    if not guests.empty and 'telefone' in guests:
        no_phone=int(guests['telefone'].fillna('').astype(str).str.strip().eq('').sum())
        if no_phone: insights.append(_ins('warning','Convidados sem telefone',f'{no_phone} convidado(s) estão sem WhatsApp cadastrado.','Completar contatos antes de disparos em massa.','Convidados',no_phone))
    resp=responses_dashboard(event_id)
    if not resp.empty and 'needs_bus' in resp:
        bus_no_point=resp[(resp['needs_bus'].fillna(0).astype(int)==1) & resp.get('bus_pickup_point','').fillna('').astype(str).str.strip().eq('')]
        if len(bus_no_point): insights.append(_ins('warning','Transporte sem ponto',f'{len(bus_no_point)} convidado(s) pediram transporte sem ponto de embarque.','Solicitar ponto de embarque.','Portal do Convidado',len(bus_no_point)))
    exp=list_expenses(event_id)
    if not exp.empty:
        overdue=exp[exp['status']=='overdue']
        if len(overdue): insights.append(_ins('warning','Pagamentos vencidos',f'{len(overdue)} despesa(s) estão vencidas.','Regularizar ou cancelar despesas vencidas.','Financeiro',len(overdue)))
    docs=list_documents(event_id)
    if not docs.empty: insights.append(_ins('info','Documentos organizados',f'{len(docs)} documento(s) disponíveis na central.','Manter contratos e listas atualizados.','Documentos',len(docs)))
    confirmed = 0 if rsvp.empty else int((rsvp['status']=='confirmed').sum())
    if total and confirmed/max(total,1) >= .7: insights.append(_ins('info','Progresso bom',f'{confirmed} de {total} convidados confirmaram presença.','Continuar acompanhando pendências.','Dashboard',confirmed))
    if not insights:
        insights.append(_ins('info','Evento em preparação','Nenhum alerta crítico encontrado no momento.','Continue alimentando convidados, mesas e fornecedores.','Dashboard',0))
    return insights

def executive_state_label(insights:list[dict]) -> tuple[str,str]:
    if any(i['severity']=='critical' for i in insights): return 'Atenção operacional','Existem pontos críticos que precisam de ação da assessoria.'
    if any(i['severity']=='warning' for i in insights): return 'Evento sob controle','Há pendências moderadas para acompanhar.'
    return 'Evento saudável','Os principais indicadores estão evoluindo bem.'

# Alias para workers/API de produção
def generate_insights(event_id: int) -> list[dict]:
    return analyze_event(event_id)
