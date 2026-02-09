from pathlib import Path
import streamlit as st
from database import load_all_data, save_data

# Importa as views modularizadas
from services.extractor import extract_data_from_pdf
from views.dashboard import render_dashboard_tab
from views.investigation import render_investigation_tab
from views.data_explorer import render_data_explorer_tab
from views.help import render_help_tab

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Sherlock Ohms", page_icon="🕵️‍♂️", layout="wide")
st.markdown("<style>.main-header {font-size: 2.5rem; font-weight: 700; color: #4285f4;}</style>", unsafe_allow_html=True)

# Carrega dados antes da sidebar para permitir verificação de duplicidade
df_faturas, df_medicao = load_all_data()

# --- SIDEBAR (Upload) ---
with st.sidebar:
    current_dir = Path(__file__).parent
    # Tenta encontrar o arquivo em src/assets ou na raiz/assets
    logo_path = current_dir / "assets" / "logo_pandas_orms.png"

    if not logo_path.exists():
        # Fallback: Tenta na raiz do projeto se não achar em src/
        logo_path = current_dir.parent / "assets" / "logo_pandas_orms.png"

    if logo_path.exists():
        st.image(str(logo_path), width=90)
    else:
        st.image("https://img.icons8.com/color/96/sherlock-holmes.png", width=80)
    st.markdown("## Sherlock Ohms")
    st.caption("Investigação Elementar de Energia")
    st.divider()

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    uploaded_file = st.file_uploader("Importar Fatura (PDF)", type=["pdf"], key=f"uploader_{st.session_state.uploader_key}")
    password = st.text_input("Senha (se houver)", type="password")

    if uploaded_file and st.button("🔍 Processar", type="primary"):
        with st.spinner("Lendo arquivo..."):
            temp_path = f"data/temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f: f.write(uploaded_file.getbuffer())

            df_fin, df_med = extract_data_from_pdf(temp_path, password)
            if not df_fin.empty:
                # Verifica duplicidade antes de salvar
                new_ref = df_fin.iloc[0]["mes_referencia"]
                is_duplicate = False

                if not df_faturas.empty:
                    # Verifica nas colunas possíveis (compatibilidade com dados antigos)
                    for col in ["mes_referencia", "Referência", "referencia"]:
                        if col in df_faturas.columns:
                            if new_ref in df_faturas[col].astype(str).values:
                                is_duplicate = True
                                break

                if is_duplicate:
                    st.warning(f"⚠️ A fatura de **{new_ref}** já foi importada anteriormente. O sistema evitou a duplicação.")
                else:
                    save_data(df_fin, df_med)
                    st.success("Salvo!")
                    st.session_state.uploader_key += 1
                    st.rerun()
            else:
                st.error("Erro na leitura.")

# --- MAIN ---
st.markdown('<div class="main-header">Painel de Investigação</div>', unsafe_allow_html=True)

if df_faturas.empty:
    st.info("👋 Bem-vindo! Comece importando uma fatura no menu lateral.")
    st.stop()

# Abas
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🕵️‍♂️ Detetive IA", "📋 Dados Brutos", "❓ Ajuda"])

with tab1: render_dashboard_tab(df_faturas, df_medicao)
with tab2: render_investigation_tab(df_faturas)
with tab3: render_data_explorer_tab(df_faturas, df_medicao)
with tab4: render_help_tab()
