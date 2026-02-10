"""Tests for extractor helper functions."""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.extractor import (
    clean_cmyk_artifacts,
    clean_line,
    normalize_negative_value,
    process_values,
)

# ==============================================================================
# normalize_negative_value
# ==============================================================================


class TestNormalizeNegativeValue:
    def test_positive_value(self):
        assert normalize_negative_value("19,52") == "19.52"

    def test_negative_suffix(self):
        assert normalize_negative_value("19,52-") == "-19.52"

    def test_negative_prefix(self):
        assert normalize_negative_value("-19,52") == "-19.52"

    def test_integer(self):
        assert normalize_negative_value("100") == "100"

    def test_empty_string(self):
        assert normalize_negative_value("") == ""

    def test_none(self):
        assert normalize_negative_value(None) is None

    def test_non_string_input(self):
        assert normalize_negative_value(42) == "42"

    def test_whitespace(self):
        assert normalize_negative_value("  19,52  ") == "19.52"


# ==============================================================================
# clean_line
# ==============================================================================


class TestCleanLine:
    def test_standard_with_unit(self):
        result = clean_line("Energia Ativa Fornecida kWh 477,00 0,55 262,35")
        assert result is not None
        assert result["type"] == "standard"
        assert result["description"] == "Energia Ativa Fornecida"
        assert result["unit"] == "kWh"

    def test_simple_value_only(self):
        result = clean_line("CIP Municipal 23,01")
        assert result is not None
        assert result["type"] == "simple"
        assert result["description"] == "CIP Municipal"
        assert result["unit"] == ""

    def test_noise_only(self):
        result = clean_line("DADOS DE MEDIÇÃO")
        assert result is None

    def test_empty(self):
        result = clean_line("")
        assert result is None

    def test_history_cleanup(self):
        """Lines ending with month/year history should be cleaned."""
        result = clean_line("Energia Ativa kWh 477,00 0,55 262,35 JAN/2025 480")
        assert result is not None
        assert result["type"] == "standard"


# ==============================================================================
# process_values
# ==============================================================================


class TestProcessValues:
    def test_standard_full_8_tokens(self):
        result = process_values("477,00 0,55 262,35 5,20 262,35 20,00 52,47 0,45", "standard")
        assert result["quantidade"] == "477.00"
        assert result["preco_unitario"] == "0.55"
        assert result["valor_total"] == "262.35"
        assert result["pis_cofins"] == "5.20"
        assert result["tarifa_unitaria"] == "0.45"

    def test_standard_3_tokens(self):
        result = process_values("477,00 0,55 262,35", "standard")
        assert result["quantidade"] == "477.00"
        assert result["preco_unitario"] == "0.55"
        assert result["valor_total"] == "262.35"
        assert result["pis_cofins"] == ""

    def test_simple_1_token(self):
        result = process_values("23,01", "simple")
        assert result["valor_total"] == "23.01"
        assert result["quantidade"] == ""

    def test_empty(self):
        result = process_values("", "standard")
        assert result["valor_total"] == ""
        assert result["quantidade"] == ""


# ==============================================================================
# clean_cmyk_artifacts
# ==============================================================================


class TestCleanCmykArtifacts:
    def test_cmyk_prefix(self):
        assert clean_cmyk_artifacts("Y     Energia Atv Inj") == "Energia Atv Inj"

    def test_multi_prefix(self):
        assert clean_cmyk_artifacts("CMCM CCMMCCMM Energia Consumida") == "Energia Consumida"

    def test_clean_line(self):
        assert clean_cmyk_artifacts("Energia Ativa Fornecida") == "Energia Ativa Fornecida"

    def test_empty(self):
        assert clean_cmyk_artifacts("") == ""

    def test_none(self):
        assert clean_cmyk_artifacts(None) is None
