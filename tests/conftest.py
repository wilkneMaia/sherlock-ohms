"""Shared pytest fixtures."""

import os
import tempfile

import pandas as pd
import pytest


@pytest.fixture
def tmp_dir():
    """Provides a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_faturas_df():
    """Sample financial DataFrame matching the real schema."""
    return pd.DataFrame(
        {
            "mes_referencia": ["01/2025", "02/2025", "01/2025"],
            "numero_cliente": ["12345678", "12345678", "12345678"],
            "descricao": ["Energia Ativa Fornecida", "Energia Ativa Fornecida", "CIP Municipal"],
            "unidade": ["kWh", "kWh", ""],
            "quantidade": [477.0, 510.0, 0.0],
            "preco_unitario": [0.55, 0.55, 0.0],
            "valor_total": [262.35, 280.50, 23.01],
        }
    )


@pytest.fixture
def sample_medicao_df():
    """Sample measurement DataFrame matching the real schema."""
    return pd.DataFrame(
        {
            "mes_referencia": ["01/2025", "02/2025"],
            "numero_cliente": ["12345678", "12345678"],
            "numero_medidor": ["ABC123", "ABC123"],
            "segmento": ["Consumo Ativo", "Consumo Ativo"],
            "consumo_kwh": [477.0, 510.0],
            "numero_dias": [30, 31],
        }
    )
