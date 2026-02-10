"""Tests for standardize_frame function."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd

from services.extractor import standardize_frame


class TestStandardizeFrame:
    def test_column_rename(self):
        df = pd.DataFrame({"Itens de Fatura": ["Energia"], "Valor (R$)": [100.0]})
        mapping = {"Itens de Fatura": "descricao", "Valor (R$)": "valor_total"}
        result = standardize_frame(df, mapping)
        assert "descricao" in result.columns
        assert "valor_total" in result.columns

    def test_accent_removal(self):
        df = pd.DataFrame({"Preço Unitário": [0.55]})
        result = standardize_frame(df, {})
        assert "preco_unitario" in result.columns

    def test_snake_case(self):
        df = pd.DataFrame({"Base Calc ICMS": [100.0]})
        result = standardize_frame(df, {})
        assert "base_calc_icms" in result.columns

    def test_empty_df(self):
        df = pd.DataFrame()
        result = standardize_frame(df, {})
        assert result.empty

    def test_preserves_data(self):
        df = pd.DataFrame({"Valor (R$)": [10.5, 20.3]})
        mapping = {"Valor (R$)": "valor_total"}
        result = standardize_frame(df, mapping)
        assert list(result["valor_total"]) == [10.5, 20.3]
