"""Tests for database manager (upsert logic)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd

from database.manager import _upsert_dataframe


class TestUpsertDataframe:
    def test_insert_new_file(self, tmp_dir):
        """Creates a new parquet file when it doesn't exist."""
        path = os.path.join(tmp_dir, "test.parquet")
        df = pd.DataFrame({"mes_referencia": ["01/2025"], "valor_total": [100.0]})

        result = _upsert_dataframe(df, path)

        assert result is True
        loaded = pd.read_parquet(path)
        assert len(loaded) == 1
        assert loaded.iloc[0]["valor_total"] == 100.0

    def test_upsert_replaces_existing(self, tmp_dir):
        """Replaces rows with matching keys."""
        path = os.path.join(tmp_dir, "test.parquet")

        # Insert initial data
        df_old = pd.DataFrame({"mes_referencia": ["01/2025"], "valor_total": [100.0]})
        df_old.to_parquet(path, index=False)

        # Upsert with same key, different value
        df_new = pd.DataFrame({"mes_referencia": ["01/2025"], "valor_total": [150.0]})
        result = _upsert_dataframe(df_new, path)

        assert result is True
        loaded = pd.read_parquet(path)
        assert len(loaded) == 1
        assert loaded.iloc[0]["valor_total"] == 150.0

    def test_upsert_appends_new_key(self, tmp_dir):
        """Appends rows with new keys without removing existing ones."""
        path = os.path.join(tmp_dir, "test.parquet")

        df_old = pd.DataFrame({"mes_referencia": ["01/2025"], "valor_total": [100.0]})
        df_old.to_parquet(path, index=False)

        df_new = pd.DataFrame({"mes_referencia": ["02/2025"], "valor_total": [200.0]})
        result = _upsert_dataframe(df_new, path)

        assert result is True
        loaded = pd.read_parquet(path)
        assert len(loaded) == 2

    def test_empty_df_returns_false(self, tmp_dir):
        """Empty DataFrame should not be saved."""
        path = os.path.join(tmp_dir, "test.parquet")
        result = _upsert_dataframe(pd.DataFrame(), path)
        assert result is False

    def test_multi_key_upsert(self, tmp_dir):
        """Upsert with composite key [mes_referencia, numero_cliente]."""
        path = os.path.join(tmp_dir, "test.parquet")

        df_old = pd.DataFrame({
            "mes_referencia": ["01/2025", "01/2025"],
            "numero_cliente": ["AAA", "BBB"],
            "valor_total": [100.0, 200.0],
        })
        df_old.to_parquet(path, index=False)

        # Update only client AAA
        df_new = pd.DataFrame({
            "mes_referencia": ["01/2025"],
            "numero_cliente": ["AAA"],
            "valor_total": [999.0],
        })
        result = _upsert_dataframe(df_new, path, keys=["mes_referencia", "numero_cliente"])

        assert result is True
        loaded = pd.read_parquet(path)
        assert len(loaded) == 2
        aaa_row = loaded[loaded["numero_cliente"] == "AAA"]
        assert aaa_row.iloc[0]["valor_total"] == 999.0
        bbb_row = loaded[loaded["numero_cliente"] == "BBB"]
        assert bbb_row.iloc[0]["valor_total"] == 200.0
