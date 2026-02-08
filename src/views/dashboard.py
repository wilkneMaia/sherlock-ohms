import streamlit as st
from components.financial_flow import render_financial_flow
from components.taxometer import render_taxometer
from components.consumption_dashboard import render_consumption_dashboard
from components.public_lighting import render_public_lighting

def render_dashboard_tab(df_faturas, df_medicao):
    # Normalização de colunas para corrigir erros de importação (acentos/espaços)
    def _normalizar_cols(df):
        if df is None or df.empty: return df
        new_cols = []
        for col in df.columns:
            c = str(col).lower().strip()
            c = c.replace('á', 'a').replace('ã', 'a').replace('â', 'a')
            c = c.replace('é', 'e').replace('ê', 'e')
            c = c.replace('í', 'i').replace('ó', 'o').replace('õ', 'o')
            c = c.replace('ú', 'u').replace('ç', 'c')
            new_cols.append(c.replace(" ", "_"))
        df.columns = new_cols
        return df

    df_faturas = _normalizar_cols(df_faturas)
    df_medicao = _normalizar_cols(df_medicao)

    # Garante que a coluna de referência seja encontrada mesmo se o nome variar na extração
    if "referencia" in df_faturas.columns:
        df_faturas.rename(columns={"referencia": "mes_referencia"}, inplace=True)
    if "referencia" in df_medicao.columns:
        df_medicao.rename(columns={"referencia": "mes_referencia"}, inplace=True)

    # Normaliza coluna de valor financeiro para o padrão esperado pelo dashboard
    if "valor_(r$)" in df_faturas.columns:
        df_faturas.rename(columns={"valor_(r$)": "valor_total"}, inplace=True)

    # Normaliza coluna de descrição dos itens (ex: Itens de Fatura -> descricao)
    if "itens_de_fatura" in df_faturas.columns:
        df_faturas.rename(columns={"itens_de_fatura": "descricao"}, inplace=True)

    # Normaliza colunas de impostos para o Taxômetro
    if "icms" in df_faturas.columns:
        df_faturas.rename(columns={"icms": "valor_icms"}, inplace=True)
    if "pis/cofins" in df_faturas.columns:
        df_faturas.rename(columns={"pis/cofins": "pis_cofins"}, inplace=True)

    # Normaliza colunas da medição para evitar erros no dashboard de consumo
    if "consumo" in df_medicao.columns:
        df_medicao.rename(columns={"consumo": "consumo_kwh"}, inplace=True)

    # Normaliza coluna de segmento para identificar Injeção Solar (P.Horário/Segmento -> segmento)
    for col in ["p.horario/segmento", "p_horario_segmento", "p.horario_segmento"]:
        if col in df_medicao.columns:
            df_medicao.rename(columns={col: "segmento"}, inplace=True)
            break

    # Garante que a coluna 'numero_dias' exista (usada para média diária)
    for col in ["nº_dias", "n_dias", "dias", "no_dias"]:
        if col in df_medicao.columns:
            df_medicao.rename(columns={col: "numero_dias"}, inplace=True)
            break
    if "numero_dias" not in df_medicao.columns and not df_medicao.empty:
        df_medicao["numero_dias"] = 30

    if "mes_referencia" not in df_faturas.columns:
        st.error(f"Erro de Dados: A coluna 'mes_referencia' não foi encontrada. Colunas disponíveis: {list(df_faturas.columns)}")
        st.stop()

    if "valor_total" not in df_faturas.columns:
        st.error(f"Erro de Dados: A coluna 'valor_total' não foi encontrada. Colunas disponíveis: {list(df_faturas.columns)}")
        st.stop()

    if "descricao" not in df_faturas.columns:
        st.error(f"Erro de Dados: A coluna 'descricao' não foi encontrada. Colunas disponíveis: {list(df_faturas.columns)}")
        st.stop()

    with st.container(border=True):
        st.markdown("### 🎛️ Filtros de Análise")

        # Filtro de Ano
        anos = sorted(list(set([str(x).split("/")[-1] for x in df_faturas["mes_referencia"].unique() if "/" in str(x)])))
        c_ano, c_mes = st.columns([1, 4])

        with c_ano:
            ano_sel = st.selectbox("📅 Ano", anos, index=len(anos)-1) if anos else None

        # Aplica Filtro
        df_fin_view = df_faturas[df_faturas["mes_referencia"].str.contains(str(ano_sel))] if ano_sel else df_faturas
        df_med_view = df_medicao[df_medicao["mes_referencia"].str.contains(str(ano_sel))] if ano_sel and not df_medicao.empty else df_medicao

        with c_mes:
            if not df_fin_view.empty:
                meses_disp = df_fin_view["mes_referencia"].unique()
                meses_sel = st.multiselect("📆 Meses", meses_disp, placeholder="Visualizar ano completo")
                if meses_sel:
                    df_fin_view = df_fin_view[df_fin_view["mes_referencia"].isin(meses_sel)]
                    if not df_med_view.empty:
                        df_med_view = df_med_view[df_med_view["mes_referencia"].isin(meses_sel)]

    # KPIs
    total_gasto = df_fin_view["valor_total"].sum()
    total_kwh = df_med_view["consumo_kwh"].sum() if not df_med_view.empty and "consumo_kwh" in df_med_view.columns else 0
    preco_medio = (total_gasto / total_kwh) if total_kwh > 0 else 0
    qtd_faturas = df_fin_view["mes_referencia"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    with k1.container(border=True): st.metric("💸 Total Pago", f"R$ {total_gasto:,.2f}", help="Soma do valor total pago em todas as faturas do período selecionado.")
    with k2.container(border=True): st.metric("⚡ Consumo Total", f"{total_kwh:,.0f} kWh", help="Soma do consumo de energia ativa medido (kWh).")
    with k3.container(border=True): st.metric("📊 Custo Real Médio", f"R$ {preco_medio:.2f} / kWh", help="Custo efetivo por unidade de energia (Total Pago / Consumo Total). Inclui impostos e taxas.")
    with k4.container(border=True): st.metric("📅 Faturas Analisadas", qtd_faturas, help="Quantidade de faturas encontradas com os filtros atuais.")

    st.markdown(" ")

    # Navegação por Abas para melhor organização visual
    tab_fin, tab_tax, tab_cons, tab_ilum = st.tabs([
        "📉 Fluxo Financeiro",
        "⚖️ Taxômetro",
        "⚡ Eficiência & Consumo",
        "🔦 Iluminação Pública"
    ])

    with tab_fin:
        render_financial_flow(df_fin_view)

    with tab_tax:
        render_taxometer(df_fin_view)

    with tab_cons:
        render_consumption_dashboard(df_med_view, df_fin_view)

    with tab_ilum:
        render_public_lighting(df_fin_view, df_med_view)

    # Download Button
    st.markdown(" ")
    with st.container():
        c_spacer, c_btn = st.columns([3, 1])
        with c_btn:
            csv = df_fin_view.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Baixar Dados (CSV)", data=csv, file_name=f"auditoria_enel_{ano_sel}.csv", mime="text/csv", width="stretch")
