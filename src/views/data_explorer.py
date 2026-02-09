import streamlit as st
import pandas as pd

def render_data_explorer_tab(df_faturas, df_medicao):
    st.markdown("### 📂 Arquivo de Evidências")
    st.caption("A barra **Verde** indica economia (valores negativos) e a **Vermelha** indica gastos (positivos).")

    tipo_dados = st.radio("Selecione a Tabela:", ["💰 Itens Financeiros", "⚡ Dados de Medição"], horizontal=True)

    if tipo_dados == "💰 Itens Financeiros":
        df_view = df_faturas.copy()

        # Garante numérico e renomeia para ficar bonito na tabela
        cols_numeric = ["valor_total", "pis_cofins", "base_calculo_icms", "valor_icms", "quantidade"]
        for col in cols_numeric:
            if col in df_view.columns:
                df_view[col] = pd.to_numeric(df_view[col], errors='coerce').fillna(0)

        c1, c2 = st.columns([1, 2])
        c1.metric("Registros", len(df_view))
        c2.metric("Total", f"R$ {df_view['valor_total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # Mantemos o padrão snake_case, alterando apenas mes_referencia para mes_ano conforme solicitado
        df_view.rename(columns={
            "mes_referencia": "mes_ano"
        }, inplace=True)

        # Definimos limites explícitos para garantir que o gráfico de barras apareça
        # e o zero fique corretamente posicionado (mesmo se só houver positivos ou negativos)
        min_val = df_view["valor_total"].min()
        max_val = df_view["valor_total"].max()
        if min_val > 0: min_val = 0
        if max_val < 0: max_val = 0

        # Configuração de formatação (Pt-BR)
        format_dict = {
            "valor_total": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "pis_cofins": lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "base_calculo_icms": lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "valor_icms": lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "quantidade": lambda x: f"{x:,.0f}".replace(",", ".")
        }

        styler = (
            df_view.style.format({k: v for k, v in format_dict.items() if k in df_view.columns})
            .bar(subset=["valor_total"], align=0, vmin=min_val, vmax=max_val, color=["#2ECC71", "#EF553B"])
        )

        st.dataframe(styler, width="stretch", height=500, hide_index=True)
        filename = "financeiro.csv"

    else:
        df_view = df_medicao.copy()
        c1, c2 = st.columns([1, 2])
        c1.metric("Leituras", len(df_view))
        if "consumo_kwh" in df_view.columns:
            c2.metric("Consumo Total", f"{df_view['consumo_kwh'].sum():,.0f}".replace(",", ".") + " kWh")

        df_view.rename(columns={
            "mes_referencia": "mes_ano"
        }, inplace=True)

        column_config = {
            "mes_ano": st.column_config.TextColumn("mes_ano", width="small"),
            "consumo_kwh": st.column_config.NumberColumn("consumo_kwh", format="%d kWh"),
        }
        st.dataframe(df_view, width="stretch", column_config=column_config, height=500, hide_index=True)
        filename = "medicao.csv"

    csv = df_view.to_csv(index=False).encode('utf-8')
    st.download_button(f"📥 Baixar CSV", data=csv, file_name=filename, mime="text/csv")
