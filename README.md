# 🕵️‍♂️ Sherlock Ohms

> **Investigação Elementar de Energia** — Auditoria inteligente de faturas de energia elétrica (Enel-CE).

## 📋 Sobre

Sherlock Ohms é uma aplicação web que analisa faturas de energia elétrica da **Enel Ceará**, extraindo dados financeiros e de medição de PDFs. Com dashboards interativos e um agente de IA integrado, o sistema ajuda consumidores a entender, auditar e otimizar seus gastos com energia.

## ⚡ Funcionalidades

- **📊 Dashboard Interativo** — KPIs, gráficos de evolução, fluxo financeiro, taxômetro de impostos e análise de iluminação pública
- **🕵️ Detetive IA** — Agente com Google Gemini que responde perguntas sobre suas faturas via SQL
- **📄 Extração de PDF** — Parser inteligente que suporta faturas Enel-CE de 2025 e 2026, incluindo PDFs protegidos por senha
- **📋 Dados Brutos** — Explorador de dados com tabelas interativas e exportação CSV
- **⚖️ Auditoria CIP** — Verificação automática da taxa de iluminação pública contra a legislação municipal (Lei 757/03)
- **🏠 Multi-cliente** — Suporte a múltiplas unidades consumidoras com filtro no dashboard

## 🛠️ Tech Stack

| Camada | Tecnologia |
|---|---|
| Frontend | [Streamlit](https://streamlit.io) |
| Visualização | [Plotly](https://plotly.com/python/) |
| Extração PDF | [pdfplumber](https://github.com/jsvine/pdfplumber) + [pikepdf](https://github.com/pikepdf/pikepdf) |
| Banco de Dados | [DuckDB](https://duckdb.org) + [Apache Parquet](https://parquet.apache.org) |
| Agente IA | [Agno](https://github.com/agno-agi/agno) + [Google Gemini](https://ai.google.dev/) |
| Gerenciador | [uv](https://docs.astral.sh/uv/) |

## 🚀 Instalação

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)

### Setup

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/sherlock-ohms.git
cd sherlock-ohms

# Instale as dependências
uv sync

# Execute a aplicação
uv run streamlit run src/app.py
```

A aplicação estará disponível em `http://localhost:8501`.

## 📁 Estrutura do Projeto

```
sherlock-ohms/
├── src/
│   ├── app.py                  # Entrada principal (Streamlit)
│   ├── pages/                  # Roteamento de páginas
│   │   ├── dashboard.py
│   │   ├── detective.py
│   │   ├── raw_data.py
│   │   └── help.py
│   ├── views/                  # Lógica de renderização das views
│   │   ├── dashboard.py
│   │   ├── investigation.py
│   │   ├── data_explorer.py
│   │   └── help.py
│   ├── components/             # Componentes visuais reutilizáveis
│   │   ├── consumption_dashboard.py
│   │   ├── financial_flow.py
│   │   ├── public_lighting.py
│   │   └── taxometer.py
│   ├── services/               # Lógica de negócio
│   │   ├── extractor.py        # Parser de faturas PDF
│   │   ├── agent.py            # Configuração do agente IA
│   │   ├── llm_client.py       # Adaptadores multi-provider LLM
│   │   ├── unlocker.py         # Desbloqueio de PDFs protegidos
│   │   └── logger.py           # Logging de chamadas LLM
│   ├── database/               # Camada de persistência
│   │   └── manager.py          # CRUD com Parquet + DuckDB
│   ├── config/
│   │   └── tax_rules.py        # Tabelas de legislação (CIP)
│   └── prompts/
│       └── energy_agent.md     # System prompt do agente
├── assets/                     # Imagens e recursos estáticos
├── data/                       # Dados persistidos (gitignored)
├── pyproject.toml
└── README.md
```

## 📖 Como Usar

1. **Importar Fatura** — Clique em "Importar Fatura (PDF)" na barra lateral e envie o PDF da sua conta de energia Enel-CE
2. **Senha** — Se o PDF for protegido, use os 5 primeiros dígitos do CPF do titular
3. **Analisar** — Navegue pelas abas do Dashboard para ver gráficos e KPIs
4. **Investigar** — Acesse o "Detetive IA", insira sua Google API Key e faça perguntas sobre seus gastos

## 🧪 Desenvolvimento

```bash
# Lint
uv run task lint

# Formatação
uv run task format

# Testes
uv run task test
```

## 📄 Licença

Este projeto é de uso pessoal/educacional.
