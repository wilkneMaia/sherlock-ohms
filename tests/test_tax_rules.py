"""Tests for tax_rules module."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.tax_rules import CURRENT_BASE_RATE, get_cip_expected_value, get_law_rate


class TestGetLawRate:
    def test_isento_0_50(self):
        assert get_law_rate(30) == 0.00
        assert get_law_rate(50) == 0.00

    def test_faixa_51_100(self):
        assert get_law_rate(75) == 0.0059

    def test_faixa_101_150(self):
        assert get_law_rate(125) == 0.0145

    def test_faixa_151_200(self):
        assert get_law_rate(175) == 0.0356

    def test_faixa_201_250(self):
        assert get_law_rate(225) == 0.0617

    def test_faixa_251_300(self):
        assert get_law_rate(275) == 0.1009

    def test_faixa_301_400(self):
        assert get_law_rate(350) == 0.1447

    def test_faixa_401_500(self):
        """Faixa residencial comum — 477 kWh."""
        assert get_law_rate(477) == 0.2072

    def test_faixa_501_plus(self):
        assert get_law_rate(600) == 0.2777

    def test_boundary_exact(self):
        """Testa limites exatos das faixas."""
        assert get_law_rate(50) == 0.00
        assert get_law_rate(51) == 0.0059
        assert get_law_rate(100) == 0.0059
        assert get_law_rate(101) == 0.0145


class TestGetCipExpectedValue:
    def test_isento(self):
        assert get_cip_expected_value(30) == 0.00

    def test_faixa_percentual(self):
        """477 kWh → 20.72% × R$ 111.05 ≈ R$ 23.01"""
        result = get_cip_expected_value(477)
        expected = 0.2072 * CURRENT_BASE_RATE
        assert abs(result - expected) < 0.01

    def test_faixa_residencial_realista(self):
        """Valor real típico da fatura de Jan/2025."""
        result = get_cip_expected_value(477)
        assert 22.0 < result < 24.0  # ~R$ 23.01
