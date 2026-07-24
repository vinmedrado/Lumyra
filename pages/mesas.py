import streamlit as st
from components.layout import header
from pages.common import active_event_id, active_event_label, guests_df
from repositories.database import list_tables
from services.table_validation_service import export_table_map_csv, get_table_occupancy, guests_without_table, separated_groups, tables_over_capacity


def render():
    event_id=active_event_id(); header('Mapa de Mesas', f'Validação operacional: {active_event_label()}')
    occ=get_table_occupancy(event_id)
    if occ.empty: st.info('Cadastre mesas para visualizar ocupação.')
    else:
        st.subheader('Ocupação por mesa')
        for r in occ.itertuples():
            pct=min(float(r.percentual or 0)/100, 1.0) if r.capacidade else 0
            label=f"{r.mesa}: {r.ocupacao}/{r.capacidade or 'sem capacidade'}"
            st.progress(pct, text=label + (" · acima da capacidade" if r.status=='acima_capacidade' else ""))
    st.download_button('Exportar mapa CSV', export_table_map_csv(event_id), 'mapa_mesas.csv', 'text/csv')
    tab1,tab2,tab3,tab4=st.tabs(['Convidados por mesa','Sem mesa','Acima da capacidade','Grupos separados'])
    df=guests_df()
    with tab1:
        if df.empty: st.info('Sem convidados.')
        else:
            for mesa, g in df.fillna('').groupby('mesa_final'):
                with st.expander(str(mesa or 'Sem mesa')):
                    st.dataframe(g[[c for c in ['nome_original','grupo','telefone'] if c in g.columns]], use_container_width=True, hide_index=True)
    with tab2:
        sm=guests_without_table(event_id); st.dataframe(sm, use_container_width=True, hide_index=True) if not sm.empty else st.success('Nenhum convidado sem mesa.')
    with tab3:
        over=tables_over_capacity(event_id); st.dataframe(over, use_container_width=True, hide_index=True) if not over.empty else st.success('Nenhuma mesa acima da capacidade.')
    with tab4:
        sep=separated_groups(event_id); st.dataframe(sep, use_container_width=True, hide_index=True) if not sep.empty else st.success('Nenhum grupo separado em mesas diferentes.')
