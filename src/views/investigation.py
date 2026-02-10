import streamlit as st

from services.agent import get_agent, get_available_models

# --- Quick Actions (Sugestões de perguntas) ---
QUICK_ACTIONS = [
    "Qual o mês mais caro?",
    "Mostre a evolução do consumo",
    "Quais os maiores itens da fatura?",
    "Compare os últimos 3 meses",
]


def render_investigation_tab(df_faturas):
    # --- 1. CONFIGURAÇÃO (API Key e Modelo) ---
    st.markdown("### 🕵️‍♂️ Configuração da Investigação")

    if "api_key" not in st.session_state: st.session_state.api_key = ""
    if "selected_model" not in st.session_state: st.session_state.selected_model = "gemini-1.5-flash"
    if "messages" not in st.session_state: st.session_state.messages = []
    if "quick_action_prompt" not in st.session_state: st.session_state.quick_action_prompt = None

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
            st.session_state.quick_action_prompt = None
            st.rerun()

        chat_text = "\n\n".join([f"**{m['role'].upper()}**: {m['content']}" for m in st.session_state.messages])
        c2.download_button("💾 Salvar", data=chat_text, file_name="investigacao.md", width="stretch")

    # Definição de ícones
    ai_avatar = "🕵️‍♂️"
    user_avatar = "👤"

    # Container principal do chat para manter a ordem visual correta
    chat_container = st.container()

    # Histórico
    with chat_container:
        for msg in st.session_state.messages:
            avatar = user_avatar if msg["role"] == "user" else ai_avatar
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Mensagem de boas-vindas + Quick Actions
    welcome_ph = st.empty()
    if not st.session_state.messages:
        with welcome_ph.container():
            st.markdown(
                """
                <div style='text-align: center; color: #888; margin-top: 40px; margin-bottom: 20px;'>
                    <h4>👋 Olá! Sou seu Detetive Financeiro.</h4>
                    <p>Estou pronto para analisar suas faturas. Escolha uma pergunta rápida ou digite a sua!</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Quick Action Buttons
            cols = st.columns(len(QUICK_ACTIONS))
            for i, action in enumerate(QUICK_ACTIONS):
                with cols[i]:
                    if st.button(action, key=f"qa_{i}", use_container_width=True):
                        st.session_state.quick_action_prompt = action
                        st.rerun()

    # Determina o prompt (digitado ou quick action)
    typed_prompt = st.chat_input("Pergunte sobre seus gastos...")
    prompt = typed_prompt or st.session_state.quick_action_prompt

    if prompt:
        # Limpa o quick action após usar
        st.session_state.quick_action_prompt = None
        welcome_ph.empty()
        st.session_state.messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("user", avatar=user_avatar):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar=ai_avatar):
                with st.spinner("🔍 Analisando evidências..."):
                    try:
                        agent = get_agent(st.session_state.selected_model, st.session_state.api_key)

                        # Constrói prompt com contexto das últimas mensagens para manter a memória da conversa
                        history = st.session_state.messages[:-1][-6:] # Pega os últimos 3 turnos (excluindo a pergunta atual)
                        if history:
                            context_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
                            final_prompt = (
                                f"Histórico da conversa:\n{context_str}\n\n"
                                f"Pergunta atual: {prompt}\n"
                                f"Responda à pergunta atual considerando o contexto acima se necessário."
                            )
                        else:
                            final_prompt = prompt

                        resp_box = st.empty()
                        full_resp = ""
                        for chunk in agent.run(final_prompt, stream=True):
                            if chunk.content:
                                full_resp += chunk.content
                                resp_box.markdown(full_resp + "▌")
                        resp_box.markdown(full_resp)
                        st.session_state.messages.append({"role": "assistant", "content": full_resp})
                    except Exception as e:
                        st.error(f"❌ Ocorreu um erro na investigação: {e}")
