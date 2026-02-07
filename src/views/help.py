import streamlit as st
import os

def render_help_tab():
    st.markdown("### ❓ Central de Ajuda & Manutenção")
    col_guia, col_extras = st.columns([2, 1])

    with col_guia:
        with st.container(border=True):
            st.markdown("#### 🚀 Guia Rápido")
            st.markdown("1. **Importação:** Baixe o PDF e envie na barra lateral.\n2. **Senha:** 5 primeiros dígitos do CPF.")

        with st.container(border=True):
            st.markdown("#### 📖 Glossário")
            with st.expander("⚡ TUSD e TE"): st.write("Custos de distribuição (frete) e energia (produto).")
            with st.expander("💡 CIP (Iluminação)"): st.write("Taxa municipal para iluminação de ruas.")

    with col_extras:
        with st.container(border=True):
            st.subheader("🛠️ Manutenção")
            if st.button("🗑️ Resetar Banco de Dados", type="primary", use_container_width=True):
                if os.path.exists("data/database/faturas.parquet"): os.remove("data/database/faturas.parquet")
                if os.path.exists("data/database/medicao.parquet"): os.remove("data/database/medicao.parquet")
                st.toast("Banco limpo!", icon="🧹")
                st.rerun()
