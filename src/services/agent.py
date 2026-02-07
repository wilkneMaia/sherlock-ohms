import streamlit as st
from pathlib import Path
from agno.agent import Agent
from agno.models.google import Gemini
from google import genai

# Importa do pacote de banco de dados (funciona pois src está no path)
from database import query_energy_data, plot_energy_chart

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Identifica onde este arquivo está (src/services)
CURRENT_DIR = Path(__file__).parent
# Aponta para 'src/prompts' (sobe um nível para sair de services)
PROMPTS_DIR = CURRENT_DIR.parent / "prompts"

def load_prompt(filename: str) -> str:
    """
    Lê o arquivo de prompt do disco e armazena em cache para performance.
    """
    try:
        file_path = PROMPTS_DIR / filename
        if not file_path.exists():
            print(f"❌ [ERRO] Arquivo de prompt não encontrado: {file_path.resolve()}")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"❌ [ERRO] Falha ao ler prompt: {e}")
        return None

def get_available_models(api_key: str):
    """Lista modelos disponíveis priorizando o Flash."""
    try:
        client = genai.Client(api_key=api_key)
        all_models = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "generateContent" in m.supported_actions and "gemini" in name:
                all_models.append(name)

        priority_order = ["gemini-1.5-flash", "gemini-flash-latest"]
        sorted_models = []
        for p in priority_order:
            if p in all_models:
                sorted_models.append(p)
                all_models.remove(p)
        sorted_models.extend(sorted(all_models, reverse=True))
        return sorted_models
    except:
        return ["gemini-1.5-flash"]

def get_agent(model_id: str, api_key: str, debug_mode: bool = False):
    if not api_key:
        return None

    base_instructions_text = load_prompt("energy_agent.md")

    # Fallback de segurança: Se o arquivo não carregar, usa um prompt mínimo na memória
    if not base_instructions_text:
        st.warning(f"⚠️ Aviso: O arquivo de prompt 'energy_agent.md' não foi encontrado em `{PROMPTS_DIR}`. Usando modo de segurança.")
        base_instructions_text = """
        Você é Sherlock Ohms, um auditor de energia.
        Se o usuário perguntar "Qual seu protocolo?", responda EXATAMENTE:
        "🕵️‍♂️ **Protocolo de Segurança:** O arquivo de definições original não foi carregado. Operando com diretrizes básicas."
        """

    instructions = [base_instructions_text]

    if debug_mode:
        instructions.append(
            "\n--- MODO DEBUG ---"
            "\nApós a resposta/gráfico, mostre o SQL executado em um bloco markdown:\n```sql\nSELECT...\n```"
        )

    return Agent(
        name="Sherlock Ohms Agent",
        model=Gemini(id=model_id, api_key=api_key),
        description="Especialista em auditoria de faturas.",
        instructions=instructions,
        tools=[query_energy_data, plot_energy_chart],
        markdown=True,
    )
