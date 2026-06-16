import os
from pathlib import Path

import streamlit as st

from database import invoice_already_imported, load_all_data, save_data
from services.extractor import extract_data_from_pdf

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Sherlock Ohms", page_icon="🕵️‍♂️", layout="wide")
st.markdown("<style>.main-header {font-size: 2.5rem; font-weight: 700; color: #4285f4;}</style>", unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
pages = {
    "Sherlock Ohms": [
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True),
        st.Page("pages/detective.py", title="Detetive IA", icon="🕵️"),
        st.Page("pages/raw_data.py", title="Dados Brutos", icon="📋"),
        st.Page("pages/help.py", title="Ajuda", icon="❓"),
    ],
}

nav = st.navigation(pages)

# --- SIDEBAR (Upload) ---
with st.sidebar:
    current_dir = Path(__file__).parent
    logo_path = current_dir / "assets" / "logo_pandas_orms.png"

    if not logo_path.exists():
        logo_path = current_dir.parent / "assets" / "logo_pandas_orms.png"

    if logo_path.exists():
        st.image(str(logo_path), width=90)
    else:
        st.image("https://img.icons8.com/color/96/sherlock-holmes.png", width=80)
    st.caption("Investigação Elementar de Energia")
    st.divider()

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    uploaded_file = st.file_uploader("Importar Fatura (PDF)", type=["pdf"], key=f"uploader_{st.session_state.uploader_key}")
    password = st.text_input("Senha (se houver)", type="password")

    if uploaded_file and st.button("🔍 Processar", type="primary"):
        with st.spinner("Lendo arquivo..."):
            safe_name = Path(uploaded_file.name).name
            temp_path = f"data/temp_{safe_name}"
            with open(temp_path, "wb") as f: f.write(uploaded_file.getbuffer())

            try:
                df_fin, df_med = extract_data_from_pdf(temp_path, password)
                if not df_fin.empty:
                    df_faturas, df_medicao = load_all_data()
                    new_ref = df_fin.iloc[0]["mes_referencia"]
                    is_duplicate = invoice_already_imported(df_faturas, df_fin)

                    if is_duplicate:
                        st.warning(f"⚠️ A fatura de **{new_ref}** já foi importada anteriormente. O sistema evitou a duplicação.")
                    else:
                        save_data(df_fin, df_med)
                        st.success("Salvo!")
                        st.session_state.uploader_key += 1
                        st.rerun()
                else:
                    st.error("Erro na leitura.")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

# --- EXECUTA A PÁGINA SELECIONADA ---
nav.run()
