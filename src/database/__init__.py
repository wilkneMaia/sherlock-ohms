# src/database/__init__.py

# Isso expõe as funções do manager.py quando alguém faz "from database import ..."
from .manager import (
    invoice_already_imported,
    load_all_data,
    plot_energy_chart,
    query_energy_data,
    save_data,
)
