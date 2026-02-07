import streamlit as st
from agent import get_agent, get_available_models

def render_investigation_tab(df_faturas):
    # --- 1. CONFIGURAÇÃO (API Key e Modelo) ---
    st.markdown("### 🕵️‍♂️ Configuração da Investigação")

    if "api_key" not in st.session_state: st.session_state.api_key = ""
    if "selected_model" not in st.session_state: st.session_state.selected_model = "gemini-1.5-flash"
    if "messages" not in st.session_state: st.session_state.messages = []

    config_expanded = not bool(st.session_state.api_key)

    with st.expander("🔑 Credenciais e Modelo do Agente", expanded=config_expanded):
        col_key, col_model = st.columns([2, 1])
        with col_key:
            input_key = st.text_input("Google API Key", type="password", value=st.session_state.api_key)
            if input_key: st.session_state.api_key = input_key
        with col_model:
            if st.session_state.api_key:
                try:
                    modelos = get_available_models(st.session_state.api_key)
                    st.session_state.selected_model = st.selectbox("Agente", modelos, index=0)
                except:
                    st.session_state.selected_model = st.selectbox("Modelo", ["gemini-1.5-flash"])
            else:
                st.selectbox("Modelo", ["Insira a chave primeiro"], disabled=True)

    # --- 2. CONTEXTO ---
    with st.expander("📚 O que o Detetive sabe? (Amostra de dados)"):
        st.dataframe(df_faturas.head(3), width="stretch", hide_index=True)

    st.divider()

    # --- 3. CHAT ---
    if not st.session_state.api_key:
        st.info("🔒 Insira sua **Google API Key** acima para começar.")
        return

    col_title, col_actions = st.columns([2, 1])
    with col_title: st.markdown(f"#### 💬 Detetive: `{st.session_state.selected_model}`")
    with col_actions:
        c1, c2 = st.columns(2)
        if c1.button("🗑️ Limpar", width="stretch"):
            st.session_state.messages = []
            st.rerun()

        chat_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        c2.download_button("💾 Salvar", data=chat_text, file_name="chat.txt", width="stretch")

    # Histórico e Input
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Pergunte sobre seus gastos..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                agent = get_agent(st.session_state.selected_model, st.session_state.api_key)
                resp_box = st.empty()
                full_resp = ""
                for chunk in agent.run(prompt, stream=True):
                    if chunk.content:
                        full_resp += chunk.content
                        resp_box.markdown(full_resp + "▌")
                resp_box.markdown(full_resp)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
            except Exception as e:
                st.error(f"Erro: {e}")
