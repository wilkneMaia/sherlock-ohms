# src/database/__init__.py

# Isso expõe as funções do manager.py quando alguém faz "from database import ..."
from .manager import (
    load_all_data,
    save_data,
    query_energy_data,
    plot_energy_chart
)
