import streamlit as st
from database import load_all_data, save_data
from etl import extract_data_from_pdf

# Importa as views modularizadas
from views.dashboard import render_dashboard_tab
from views.investigation import render_investigation_tab
from views.data_explorer import render_data_explorer_tab
from views.help import render_help_tab

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Sherlock Ohms", page_icon="🕵️‍♂️", layout="wide")
st.markdown("<style>.main-header {font-size: 2.5rem; font-weight: 700; color: #4285f4;}</style>", unsafe_allow_html=True)

# --- SIDEBAR (Upload) ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/sherlock-holmes.png", width=80)
    st.markdown("## Sherlock Ohms")
    st.caption("Investigação Elementar de Energia")
    st.divider()

    uploaded_file = st.file_uploader("Importar Fatura (PDF)", type=["pdf"])
    password = st.text_input("Senha (se houver)", type="password")

    if uploaded_file and st.button("🔍 Processar", type="primary"):
        with st.spinner("Lendo arquivo..."):
            temp_path = f"data/temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f: f.write(uploaded_file.getbuffer())

            df_fin, df_med = extract_data_from_pdf(temp_path, password)
            if not df_fin.empty:
                save_data(df_fin, df_med)
                st.success("Salvo!")
                st.rerun()
            else:
                st.error("Erro na leitura.")

# --- MAIN ---
st.markdown('<div class="main-header">Painel de Investigação</div>', unsafe_allow_html=True)
df_faturas, df_medicao = load_all_data()

if df_faturas.empty:
    st.info("👋 Bem-vindo! Comece importando uma fatura no menu lateral.")
    st.stop()

# Abas
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🕵️‍♂️ Detetive IA", "📋 Dados Brutos", "❓ Ajuda"])

with tab1: render_dashboard_tab(df_faturas, df_medicao)
with tab2: render_investigation_tab(df_faturas)
with tab3: render_data_explorer_tab(df_faturas, df_medicao)
with tab4: render_help_tab()
