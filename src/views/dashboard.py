import streamlit as st
from components.financial_flow import render_financial_flow
from components.taxometer import render_taxometer
from components.consumption_dashboard import render_consumption_dashboard
from components.public_lighting import render_public_lighting

def render_dashboard_tab(df_faturas, df_medicao):
    with st.container(border=True):
        st.markdown("### 🎛️ Filtros de Análise")

        # Filtro de Ano
        anos = sorted(list(set([str(x).split("/")[-1] for x in df_faturas["Referência"].unique() if "/" in str(x)])))
        c_ano, c_mes = st.columns([1, 4])

        with c_ano:
            ano_sel = st.selectbox("📅 Ano", anos, index=len(anos)-1) if anos else None

        # Aplica Filtro
        df_fin_view = df_faturas[df_faturas["Referência"].str.contains(str(ano_sel))] if ano_sel else df_faturas
        df_med_view = df_medicao[df_medicao["Referência"].str.contains(str(ano_sel))] if ano_sel and not df_medicao.empty else df_medicao

        with c_mes:
            if not df_fin_view.empty:
                meses_disp = df_fin_view["Referência"].unique()
                meses_sel = st.multiselect("📆 Meses", meses_disp, placeholder="Visualizar ano completo")
                if meses_sel:
                    df_fin_view = df_fin_view[df_fin_view["Referência"].isin(meses_sel)]
                    if not df_med_view.empty:
                        df_med_view = df_med_view[df_med_view["Referência"].isin(meses_sel)]

    # KPIs
    total_gasto = df_fin_view["Valor (R$)"].sum()
    total_kwh = df_med_view["Consumo kWh"].sum() if not df_med_view.empty and "Consumo kWh" in df_med_view.columns else 0
    preco_medio = (total_gasto / total_kwh) if total_kwh > 0 else 0
    qtd_faturas = df_fin_view["Referência"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    with k1.container(border=True): st.metric("💸 Total Pago", f"R$ {total_gasto:,.2f}")
    with k2.container(border=True): st.metric("⚡ Consumo Total", f"{total_kwh:,.0f} kWh")
    with k3.container(border=True): st.metric("📊 Custo Real Médio", f"R$ {preco_medio:.2f} / kWh")
    with k4.container(border=True): st.metric("📅 Faturas Analisadas", qtd_faturas)

    st.markdown(" ")

    # Gráficos
    with st.container(border=True):
        st.subheader("📉 Fluxo Financeiro")
        st.caption("Evolução dos pagamentos e identificação de maiores gastos.")
        render_financial_flow(df_fin_view)

    st.markdown(" ")
    with st.container(border=True):
        st.subheader("⚖️ Taxômetro (Raio-X)")
        st.caption("Quanto da sua conta é Energia vs. Impostos/Taxas.")
        render_taxometer(df_fin_view)

    st.markdown(" ")
    with st.container(border=True):
        st.subheader("⚡ Eficiência Energética")
        st.caption("Análise de consumo físico (kWh) e geração solar (se houver).")
        render_consumption_dashboard(df_med_view, df_fin_view)

    st.markdown(" ")
    with st.container(border=True):
        st.subheader("🔦 Auditoria de Iluminação Pública")
        st.caption("Verificação automática das alíquotas cobradas vs. Lei Municipal.")
        render_public_lighting(df_fin_view, df_med_view)

    # Download Button
    st.markdown(" ")
    with st.container():
        c_spacer, c_btn = st.columns([3, 1])
        with c_btn:
            csv = df_fin_view.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Baixar Dados (CSV)", data=csv, file_name=f"auditoria_enel_{ano_sel}.csv", mime="text/csv", width="stretch")
