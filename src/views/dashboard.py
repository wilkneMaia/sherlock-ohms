import pandas as pd
import streamlit as st

from components.consumption_dashboard import render_consumption_dashboard
from components.financial_flow import render_financial_flow
from components.public_lighting import render_public_lighting
from components.taxometer import render_taxometer


def _format_brl(value):
    """Formata valor para R$ no padrão brasileiro."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_dashboard_tab(df_faturas, df_medicao):
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

        # --- Filtro de Unidade Consumidora (Cliente) ---
        clientes = []
        if "numero_cliente" in df_faturas.columns:
            clientes = sorted(df_faturas["numero_cliente"].dropna().unique().tolist())

        if len(clientes) > 1:
            c_cliente, c_ano, c_mes = st.columns([1, 1, 3])
            with c_cliente:
                cliente_sel = st.selectbox("🏠 Unidade", clientes, index=0)
            df_faturas = df_faturas[df_faturas["numero_cliente"] == cliente_sel]
            if not df_medicao.empty and "numero_cliente" in df_medicao.columns:
                df_medicao = df_medicao[df_medicao["numero_cliente"] == cliente_sel]
        else:
            c_ano, c_mes = st.columns([1, 4])

        # Filtro de Ano
        anos = sorted(list(set([str(x).split("/")[-1] for x in df_faturas["mes_referencia"].unique() if "/" in str(x)])))

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

    # --- KPIs ---
    total_gasto = df_fin_view["valor_total"].sum()

    # Filtra apenas consumo (exclui injeção "INJ") para calcular consumo real
    if not df_med_view.empty and "consumo_kwh" in df_med_view.columns:
        df_consumo = df_med_view[~df_med_view["segmento"].str.contains("INJ", case=False, na=False)] if "segmento" in df_med_view.columns else df_med_view
        total_kwh = df_consumo["consumo_kwh"].sum()
    else:
        total_kwh = 0
    preco_medio = (total_gasto / total_kwh) if total_kwh > 0 else 0
    qtd_faturas = df_fin_view["mes_referencia"].nunique()

    # --- Variação Mês-a-Mês (Δ%) ---
    delta_gasto_str = None
    delta_kwh_str = None

    df_mensal = df_fin_view.groupby("mes_referencia")["valor_total"].sum().reset_index()
    # Tenta ordenar cronologicamente
    try:
        df_mensal["_ordem"] = pd.to_datetime(df_mensal["mes_referencia"], format="%m/%Y")
        df_mensal = df_mensal.sort_values("_ordem")
    except Exception:
        pass

    if len(df_mensal) >= 2:
        ultimo_val = df_mensal.iloc[-1]["valor_total"]
        penultimo_val = df_mensal.iloc[-2]["valor_total"]
        if penultimo_val != 0:
            pct_change = ((ultimo_val - penultimo_val) / abs(penultimo_val)) * 100
            delta_gasto_str = f"{pct_change:+.1f}% vs mês anterior".replace(".", ",")

    # Variação de consumo
    if not df_med_view.empty and "consumo_kwh" in df_med_view.columns:
        df_consumo_filt = df_med_view.copy()
        if "segmento" in df_consumo_filt.columns:
            df_consumo_filt = df_consumo_filt[~df_consumo_filt["segmento"].str.contains("INJ", case=False, na=False)]
        df_kwh_mensal = df_consumo_filt.groupby("mes_referencia")["consumo_kwh"].sum().reset_index()
        try:
            df_kwh_mensal["_ordem"] = pd.to_datetime(df_kwh_mensal["mes_referencia"], format="%m/%Y")
            df_kwh_mensal = df_kwh_mensal.sort_values("_ordem")
        except Exception:
            pass

        if len(df_kwh_mensal) >= 2:
            ultimo_kwh = df_kwh_mensal.iloc[-1]["consumo_kwh"]
            penultimo_kwh = df_kwh_mensal.iloc[-2]["consumo_kwh"]
            if penultimo_kwh != 0:
                pct_kwh = ((ultimo_kwh - penultimo_kwh) / abs(penultimo_kwh)) * 100
                delta_kwh_str = f"{pct_kwh:+.1f}% vs mês anterior".replace(".", ",")

    k1, k2, k3, k4 = st.columns(4)
    with k1.container(border=True):
        st.metric("💸 Total Pago", _format_brl(total_gasto), delta=delta_gasto_str, delta_color="inverse", help="Soma do valor total pago em todas as faturas do período selecionado.")
    with k2.container(border=True):
        st.metric("⚡ Consumo Total", f"{total_kwh:,.0f}".replace(",", ".") + " kWh", delta=delta_kwh_str, delta_color="inverse", help="Soma do consumo de energia ativa medido (kWh).")
    with k3.container(border=True):
        st.metric("📊 Custo Real Médio", _format_brl(preco_medio) + " / kWh", help="Custo efetivo por unidade de energia (Total Pago / Consumo Total). Inclui impostos e taxas.")
    with k4.container(border=True):
        st.metric("📅 Faturas Analisadas", qtd_faturas, help="Quantidade de faturas encontradas com os filtros atuais.")

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
