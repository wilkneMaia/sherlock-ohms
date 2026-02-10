# 🕵️‍♂️ Sherlock Ohms

> **Investigação Elementar de Energia** — Auditoria inteligente de faturas de energia elétrica (Enel-CE).

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## 📋 Sobre

**Sherlock Ohms** é uma aplicação web moderna que transforma faturas de energia elétrica complexas em insights acionáveis. Projetado especificamente para faturas da **Enel Ceará**, o sistema extrai automaticamente dados de PDFs (incluindo protegidos por senha), armazena em um banco de dados local de alta performance e oferece dashboards interativos para análise de consumo e custos.

Além da visualização de dados, o Sherlock Ohms conta com um **Agente de IA (Powered by Google Gemini)** que atua como um detetive particular, respondendo perguntas em linguagem natural sobre suas faturas e gerando consultas SQL complexas sob demanda.

---

## ⚡ Funcionalidades Principais

### 📊 Análise e Visualização
- **Dashboard Interativo**: Acompanhe a evolução do consumo (kWh), custos (R$) e indicadores mês a mês.
- **Fluxo Financeiro**: Visualize para onde vai seu dinheiro (Geração, Distribuição, Impostos).
- **Taxômetro**: Entenda o peso dos impostos (ICMS, PIS/COFINS) na sua conta.
- **Análise de Iluminação Pública**: Monitore a taxa de iluminação pública (CIP) e compare com a legislação municipal.

### 🤖 Inteligência Artificial
- **Detetive IA**: Converse com seus dados. Pergunte "Qual foi o mês com maior consumo em 2024?" ou "Quanto gastei de ICMS no total?" e obtenha respostas precisas baseadas em seus dados reais.
- **Transparência**: O agente explica o raciocínio e mostra as queries SQL geradas.

### �️ Gestão de Dados
- **Extração Inteligente de PDF**: Suporte nativo para faturas Enel-CE (modelos 2025/2026).
- **Suporte a PDFs Protegidos**: Desbloqueio automático com senha (CPF).
- **Multi-cliente**: Gerencie múltiplas unidades consumidoras (UCs) em um único lugar.
- **Banco de Dados Local**: Seus dados ficam na sua máquina, armazenados em arquivos Parquet otimizados via DuckDB.

---

## 🚀 Como Começar

### Pré-requisitos
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Recomendado para gerenciamento rápido de pacotes)

### Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-usuario/sherlock-ohms.git
   cd sherlock-ohms
   ```

2. **Instale as dependências**
   O projeto utiliza `uv` para gerenciamento de dependências.
   ```bash
   uv sync
   ```

3. **Configure as Variáveis de Ambiente**
   Crie um arquivo `.env` na raiz do projeto com sua chave da API do Google Gemini (necessário para o Detetive IA):
   ```bash
   GOOGLE_API_KEY="sua-chave-aqui"
   ```

4. **Execute a Aplicação**
   ```bash
   uv run streamlit run src/app.py
   ```
   Acesse no navegador: `http://localhost:8501`

---

## 📖 Guia de Uso

1. **Importar Fatura**:
   - No menu lateral, faça upload do PDF da sua conta de energia.
   - Se o PDF tiver senha, insira os 5 primeiros dígitos do CPF do titular no campo indicado.
   - O sistema detectará duplicatas automaticamente.

2. **Dashboard**:
   - Navegue pelas abas para ver diferentes perspectivas dos seus dados (Geral, Financeiro, Impostos).

3. **Detetive IA**:
   - Vá até a página "Detetive IA".
   - Faça perguntas como: *"Compare o consumo de Janeiro/2024 com Janeiro/2025"* ou *"Qual a média de gastos nos últimos 6 meses?"*.

---

## 🛠️ Tecnologias

O Sherlock Ohms é construído com uma stack moderna e eficiente focada em ciência de dados e performance:

| Categoria | Tecnologias |
|-----------|-------------|
| **Frontend** | [Streamlit](https://streamlit.io) |
| **Visualização** | [Plotly](https://plotly.com/python/) |
| **Processamento PDF** | [pdfplumber](https://github.com/jsvine/pdfplumber), [pikepdf](https://github.com/pikepdf/pikepdf) |
| **Banco de Dados** | [DuckDB](https://duckdb.org) (SQL OLAP), [Apache Parquet](https://parquet.apache.org) |
| **IA & Agentes** | [Agno](https://github.com/agno-agi/agno), [Google Gemini](https://ai.google.dev/) |
| **Core & Tooling** | Python 3.12+, [uv](https://docs.astral.sh/uv/), [Ruff](https://docs.astral.sh/ruff/) |

---

## 📁 Estrutura do Projeto

```
sherlock-ohms/
├── src/
│   ├── app.py                  # Ponto de entrada (Streamlit)
│   ├── pages/                  # Páginas da aplicação
│   ├── components/             # Componentes UI reutilizáveis (Charts, KPIs)
│   ├── services/               # Lógica de negócio (Extractors, AI Agent)
│   ├── database/               # Gerenciamento de dados (DuckDB/Parquet)
│   ├── config/                 # Configurações e regras de negócio
│   └── prompts/                # Prompts do sistema para o Agente IA
├── assets/                     # Recursos estáticos (imagens, logos)
├── data/                       # Armazenamento de dados locais (gitignored)
├── tests/                      # Testes automatizados
├── pyproject.toml              # Configuração do projeto e dependências
└── README.md                   # Documentação
```

---

## 🧪 Desenvolvimento

Para contribuir ou modificar o projeto, utilize os comandos configurados no `taskipy`:

```bash
# Rodar linting (verificação de estilo)
uv run task lint

# Formatar código automaticamente
uv run task format

# Rodar testes automatizados
uv run task test
```

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Sinta-se livre para usar, modificar e distribuir.

---

<p align="center">
  <sub>Desenvolvido com ⚡ por Sherlock Ohms Team</sub>
</p>
