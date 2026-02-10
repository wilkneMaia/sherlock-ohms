import streamlit as st

from database import load_all_data
from views.data_explorer import render_data_explorer_tab

df_faturas, df_medicao = load_all_data()
st.session_state["df_faturas"] = df_faturas
st.session_state["df_medicao"] = df_medicao

if df_faturas.empty:
    st.info("👋 Bem-vindo! Comece importando uma fatura no menu lateral.")
    st.stop()

render_data_explorer_tab(df_faturas, df_medicao)
