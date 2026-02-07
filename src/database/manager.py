import pandas as pd
import os
import streamlit as st
import duckdb

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Ajusta para pegar a raiz do projeto corretamente baseada na localização deste arquivo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FOLDER = os.path.join(BASE_DIR, "data", "database")
FILE_FATURAS = os.path.join(DB_FOLDER, "faturas.parquet")
FILE_MEDICAO = os.path.join(DB_FOLDER, "medicao.parquet")

def init_db():
    """Garante que a pasta e os arquivos existam."""
    os.makedirs(DB_FOLDER, exist_ok=True)

    if not os.path.exists(FILE_FATURAS):
        pd.DataFrame().to_parquet(FILE_FATURAS)

    if not os.path.exists(FILE_MEDICAO):
        pd.DataFrame().to_parquet(FILE_MEDICAO)

def _upsert_dataframe(df_new, file_path, keys=["Referência"]):
    if df_new.empty:
        return False

    if not os.path.exists(file_path):
        df_new.to_parquet(file_path, index=False)
        return True

    try:
        df_old = pd.read_parquet(file_path)
        if df_old.empty:
            df_new.to_parquet(file_path, index=False)
            return True

        missing_keys = [k for k in keys if k not in df_old.columns]
        if missing_keys:
            df_final = pd.concat([df_old, df_new], ignore_index=True)
            df_final.to_parquet(file_path, index=False)
            return True

        refs_to_update = df_new[keys].drop_duplicates()
        df_merged = df_old.merge(refs_to_update, on=keys, how="left", indicator=True)
        df_kept = df_old[df_merged["_merge"] == "left_only"]
        df_final = pd.concat([df_kept, df_new], ignore_index=True)

        df_final.to_parquet(file_path, index=False)
        return True

    except Exception as e:
        print(f"❌ Erro ao salvar parquet: {e}")
        return False

def save_data(df_financeiro, df_medicao):
    """Salva os dados no banco."""
    init_db()
    success_fin = True
    success_med = True

    keys_fin = ["Referência"]
    if "Nº do Cliente" in df_financeiro.columns:
        keys_fin.append("Nº do Cliente")

    if not df_financeiro.empty:
        success_fin = _upsert_dataframe(df_financeiro, FILE_FATURAS, keys=keys_fin)

    keys_med = ["Referência"]
    if "Nº do Cliente" in df_medicao.columns:
        keys_med.append("Nº do Cliente")

    if not df_medicao.empty:
        success_med = _upsert_dataframe(df_medicao, FILE_MEDICAO, keys=keys_med)

    return success_fin and success_med

def load_all_data():
    """
    Carrega os dados dos arquivos Parquet para memória.
    Renomeado para 'load_all_data' para manter compatibilidade com app.py
    """
    init_db()
    try:
        df_fat = pd.read_parquet(FILE_FATURAS)
        df_med = pd.read_parquet(FILE_MEDICAO)
        return df_fat, df_med
    except Exception as e:
        st.error(f"Erro ao ler banco de dados: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ==============================================================================
# PARTE NOVA: FERRAMENTAS DO AGENTE (DuckDB/SQL)
# ==============================================================================

def _get_connection():
    """Cria conexão DuckDB em memória com os dados atuais."""
    df_fat, df_med = load_all_data()

    if df_fat.empty and df_med.empty:
        return None

    con = duckdb.connect(database=':memory:')

    if not df_fat.empty:
        con.register('faturas', df_fat)

    if not df_med.empty:
        con.register('medicao', df_med)

    return con

def query_energy_data(query: str) -> str:
    """Executa consultas SQL para o Agente."""
    con = _get_connection()
    if not con:
        return "Erro: Nenhum dado carregado."

    try:
        result = con.execute(query).fetchdf()
        return result.to_markdown(index=False)
    except Exception as e:
        return f"Erro ao executar SQL: {e}"

def plot_energy_chart(query: str, chart_type: str = "bar") -> str:
    """Gera gráficos baseados em SQL."""
    con = _get_connection()
    if not con:
        return "Erro: Nenhum dado carregado."

    try:
        df_result = con.execute(query).fetchdf()

        if df_result.empty:
            return "A consulta não retornou dados."

        df_result.set_index(df_result.columns[0], inplace=True)

        st.markdown(f"### 📊 Visualização ({chart_type})")

        if chart_type == "line":
            st.line_chart(df_result)
        elif chart_type == "area":
            st.area_chart(df_result)
        else:
            st.bar_chart(df_result)

        return "Gráfico gerado com sucesso."

    except Exception as e:
        return f"Erro ao plotar gráfico: {e}"
