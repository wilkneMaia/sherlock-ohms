import streamlit as st
import pandas as pd

def render_data_explorer_tab(df_faturas, df_medicao):
    st.markdown("### 📂 Arquivo de Evidências")
    st.caption("A barra **Verde** indica economia (valores negativos) e a **Vermelha** indica gastos (positivos).")

    tipo_dados = st.radio("Selecione a Tabela:", ["💰 Itens Financeiros", "⚡ Dados de Medição"], horizontal=True)

    if tipo_dados == "💰 Itens Financeiros":
        df_view = df_faturas.copy()

        # Garante numérico e renomeia para ficar bonito na tabela
        df_view["Valor (R$)"] = pd.to_numeric(df_view["Valor (R$)"], errors='coerce').fillna(0)
        df_view.rename(columns={"Valor (R$)": "Valor"}, inplace=True)

        c1, c2 = st.columns([1, 2])
        c1.metric("Registros", len(df_view))
        c2.metric("Total", f"R$ {df_view['Valor'].sum():,.2f}")

        # Renomeamos colunas diretamente para evitar conflito entre column_config e Styler
        df_view.rename(columns={
            "Referência": "Mês/Ano",
            "Itens de Fatura": "Descrição",
            "Nº do Cliente": "Instalação"
        }, inplace=True)

        # Definimos limites explícitos para garantir que o gráfico de barras apareça
        # e o zero fique corretamente posicionado (mesmo se só houver positivos ou negativos)
        min_val = df_view["Valor"].min()
        max_val = df_view["Valor"].max()
        if min_val > 0: min_val = 0
        if max_val < 0: max_val = 0

        styler = (
            df_view.style.format({"Valor": "R$ {:,.2f}"})
            .bar(subset=["Valor"], align=0, vmin=min_val, vmax=max_val, color=["#2ECC71", "#EF553B"])
        )

        st.dataframe(styler, width="stretch", height=500, hide_index=True)
        filename = "financeiro.csv"

    else:
        df_view = df_medicao.copy()
        c1, c2 = st.columns([1, 2])
        c1.metric("Leituras", len(df_view))
        if "Consumo kWh" in df_view.columns:
            c2.metric("Consumo Total", f"{df_view['Consumo kWh'].sum():,.0f} kWh")

        column_config = {
            "Referência": st.column_config.TextColumn("Mês/Ano", width="small"),
            "Consumo kWh": st.column_config.NumberColumn("Consumo", format="%d kWh"),
        }
        st.dataframe(df_view, width="stretch", column_config=column_config, height=500, hide_index=True)
        filename = "medicao.csv"

    csv = df_view.to_csv(index=False).encode('utf-8')
    st.download_button(f"📥 Baixar CSV", data=csv, file_name=filename, mime="text/csv")
