"""
Módulo de extração de dados de faturas de energia Enel-CE.

Arquitetura:
- Helper functions (módulo level): normalize_negative_value, clean_line, process_values, etc.
- InvoiceParser (base): lógica compartilhada (template method pattern)
- Parser2025 / Parser2026: implementações específicas por formato
- extract_data_from_pdf: interface pública (roteia para o parser correto)
"""

import logging
import re
from abc import ABC, abstractmethod
from collections import defaultdict

import pandas as pd
import pdfplumber

logger = logging.getLogger(__name__)

# ==============================================================================
# HELPER FUNCTIONS (Pure, sem dependência de estado)
# ==============================================================================


def normalize_negative_value(value_str):
    """
    Normaliza valores negativos no formato "19,52-" para "-19.52"
    Também trata valores positivos convertendo vírgula para ponto.
    """
    if not value_str:
        return value_str

    if not isinstance(value_str, str):
        value_str = str(value_str)

    value_str = value_str.strip()

    if not value_str:
        return value_str

    is_negative = False
    if value_str.startswith("-"):
        is_negative = True
        value_str = value_str[1:]
    elif value_str.endswith("-"):
        is_negative = True
        value_str = value_str[:-1]

    value_str = value_str.replace(",", ".")

    if is_negative:
        value_str = "-" + value_str

    return value_str


def clean_line(line):
    """
    Tenta separar a linha em: Descrição | Unidade | Valores
    """
    history_pattern = (
        r"\s(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)[\s\/]*\d{2,4}.*$"
    )
    cleaned_line = re.sub(history_pattern, "", line, flags=re.IGNORECASE).strip()

    if not cleaned_line:
        return None

    unit_match = re.search(
        r"^(.*?)\s+(kWh|kW|dias|unid|un)\s+(.*)$", cleaned_line, re.IGNORECASE
    )
    if unit_match:
        return {
            "description": unit_match.group(1).strip(),
            "unit": unit_match.group(2).strip(),
            "values_str": unit_match.group(3).strip(),
            "type": "standard",
        }

    number_match = re.search(r"^(.*?)\s+(\d+[.,]\d{2}.*)$", cleaned_line)
    if number_match:
        return {
            "description": number_match.group(1).strip(),
            "unit": "",
            "values_str": number_match.group(2).strip(),
            "type": "simple",
        }

    return None


def process_values(values_str, item_type):
    """
    Mapeia a string de números para as colunas corretas.
    """
    clean_values = re.sub(
        r"\s(I\s?CMS|LID|DE|FATURAMENTO|TRIBUTOS|COFINS|PIS).*",
        "",
        values_str,
        flags=re.IGNORECASE,
    ).strip()
    tokens = clean_values.split()

    tokens = [normalize_negative_value(token) for token in tokens]

    columns = {
        "quantidade": "",
        "preco_unitario": "",
        "valor_total": "",
        "pis_cofins": "",
        "base_calculo_icms": "",
        "aliquota_icms": "",
        "valor_icms": "",
        "tarifa_unitaria": "",
    }

    if not tokens:
        return columns

    if item_type == "standard":
        fields = [
            "quantidade",
            "preco_unitario",
            "valor_total",
            "pis_cofins",
            "base_calculo_icms",
            "aliquota_icms",
            "valor_icms",
            "tarifa_unitaria",
        ]

        if len(tokens) >= 8:
            for i, field in enumerate(fields):
                columns[field] = tokens[i]
        elif len(tokens) >= 3:
            columns["quantidade"] = tokens[0]
            columns["preco_unitario"] = tokens[1]
            columns["valor_total"] = tokens[2]
            for i, val in enumerate(tokens[3:]):
                if i < len(fields[3:]):
                    columns[fields[3 + i]] = val

    elif item_type == "simple":
        columns["valor_total"] = tokens[0]
        fields = ["pis_cofins", "base_calculo_icms", "aliquota_icms", "valor_icms"]
        for i, val in enumerate(tokens[1:]):
            if i < len(fields):
                columns[fields[i]] = val

    return columns


def clean_cmyk_artifacts(line):
    """
    Remove artefatos de marcadores CMYK que vazam no texto extraído
    das faturas Enel-CE a partir de 2026.
    """
    if not line:
        return line

    cleaned = re.sub(
        r"^(?:[CMYK]{1,8}\s+)+",
        "",
        line.strip(),
    )

    return cleaned.strip()


def standardize_frame(df, mapping):
    """
    Padroniza nomes de colunas e remove caracteres especiais.
    """
    if df.empty:
        return df

    new_cols = []
    for col in df.columns:
        c = str(col).strip()
        new_cols.append(c)
    df.columns = new_cols

    df = df.rename(columns=mapping)

    final_cols = []
    for col in df.columns:
        c = str(col).lower().strip()
        c = c.replace('á', 'a').replace('ã', 'a').replace('â', 'a')
        c = c.replace('é', 'e').replace('ê', 'e')
        c = c.replace('í', 'i').replace('ó', 'o').replace('õ', 'o')
        c = c.replace('ú', 'u').replace('ç', 'c')
        final_cols.append(c.replace(" ", "_").replace("/", "_").replace(".", ""))
    df.columns = final_cols
    return df


# ==============================================================================
# CONSTANTES COMPARTILHADAS
# ==============================================================================

IGNORED_TERMS = [
    "MES_ANO",
    "COMSUMO",
    "CONSUMO",
    "TIPOS DE FATURAMENTO",
    "DIAS",
    "TRIBUTOS",
    "ICMS UNIT",
    "PIS/PASEP",
    "DADOS DE MEDIÇÃO",
    "LEITURA",
    "CONST. MEDIDOR",
    "GRANDEZAS",
    "POSTOS TARIFÁRIOS",
    "ELE-",
    "HFP",
    "SALDO",
    "RESERVADO",
]

JUNK_DESCRIPTIONS = ["PIS", "COFINS", "ICMS", "I CMS", "TOTAL", "SUBTOTAL"]

HISTORY_REGEX = re.compile(
    r"^(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)[\s\/\-]*\d{2,4}$"
)

MEASUREMENT_REGEX = re.compile(
    r"(\S+)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)"
)

MAP_COLS = {
    "Itens de Fatura": "descricao",
    "Unid.": "unidade",
    "Quant.": "quantidade",
    "Preço unit (R$) com tributos": "preco_unitario",
    "Valor (R$)": "valor_total",
    "PIS/COFINS": "pis_cofins",
    "Base Calc ICMS (R$)": "base_calculo_icms",
    "Alíquota ICMS": "aliquota_icms",
    "ICMS": "valor_icms",
    "Tarifa unit (R$)": "tarifa_unitaria",
    "N° Medidor": "numero_medidor",
    "P.Horário/Segmento": "segmento",
    "Data Leitura (Anterior)": "data_leitura_anterior",
    "Leitura (Anterior)": "leitura_anterior",
    "Data Leitura (Atual)": "data_leitura_atual",
    "Leitura (Atual)": "leitura_atual",
    "Fator Multiplicador": "fator_multiplicador",
    "Consumo kWh": "consumo_kwh",
    "N° Dias": "numero_dias",
}


# ==============================================================================
# BASE CLASS: InvoiceParser (Template Method)
# ==============================================================================


class InvoiceParser(ABC):
    """
    Classe base para extração de faturas Enel-CE.
    Usa o Template Method pattern: extract() orquestra os passos,
    e subclasses implementam as diferenças específicas.
    """

    def __init__(self, file_path, password=None):
        self.file_path = file_path
        self.password = password

    def extract(self):
        """
        Extrai dados brutos da fatura. Retorna dict com:
        reference, client_id, items, measurement.
        """
        data = {
            "reference": "Not Found",
            "client_id": "Not Found",
            "items": [],
            "measurement": [],
        }

        try:
            pdf_context = pdfplumber.open(self.file_path, password=self.password)

            with pdf_context as pdf:
                page = pdf.pages[0]
                text = page.extract_text(layout=True)

                # 1. Referência
                data["reference"] = self._extract_reference(text)

                # 2. Client ID
                data["client_id"] = self._extract_client_id(text)

                # 3. Medição
                data["measurement"] = self._extract_measurement(text)

                # 4. Itens Financeiros
                data["items"] = self._extract_financial_items(page)

            return data

        except Exception as e:
            if "Password" in str(e):
                logger.error("Erro de Senha: %s", e)
            else:
                logger.error("Erro Crítico na extração: %s", e)
            return None

    # --- Métodos abstratos (devem ser implementados pelas subclasses) ---

    @abstractmethod
    def _extract_reference(self, text):
        """Extrai a referência (mês/ano) do texto."""

    @abstractmethod
    def _get_financial_lines(self, page):
        """
        Retorna lista de linhas limpas para extração financeira.
        A principal diferença entre 2025 e 2026.
        """

    # --- Métodos com implementação padrão (podem ser sobrescritos) ---

    def _preprocess_line(self, line):
        """Hook para pré-processamento de linhas. Identidade por padrão."""
        return line

    def _extract_client_id(self, text):
        """Extrai o código do cliente."""
        code_match = re.search(
            r"utilizando\s+o\s+código\s+(\d+)", text, re.IGNORECASE
        )
        if code_match:
            return code_match.group(1)

        visual_match = re.search(r"\b(\d{7,12})\s*\n\s*\d{2}/\d{4}", text)
        if visual_match:
            return visual_match.group(1)

        return "Not Found"

    def _extract_measurement(self, text):
        """Extrai dados de medição. Compartilhado entre formatos."""
        measurement_items = []
        lines = text.split("\n")
        is_capturing = False

        for line in lines:
            cleaned_line = self._preprocess_line(line)
            line_upper = cleaned_line.upper().strip()

            if "EQUIPAMENTOS DE MEDIÇÃO" in line_upper or "DADOS DE MEDIÇÃO" in line_upper:
                is_capturing = True
                continue

            if is_capturing:
                if (
                    "MES_ANO" in line_upper
                    or "HISTÓRICO" in line_upper
                    or "NOTIFICAÇÃO" in line_upper
                ):
                    break

                match = MEASUREMENT_REGEX.search(cleaned_line)
                if match:
                    measurement_items.append(
                        {
                            "numero_medidor": match.group(1),
                            "segmento": match.group(2),
                            "data_leitura_anterior": match.group(3),
                            "leitura_anterior": match.group(4),
                            "data_leitura_atual": match.group(5),
                            "leitura_atual": match.group(6),
                            "fator_multiplicador": match.group(7),
                            "consumo_kwh": match.group(8),
                            "numero_dias": match.group(9),
                        }
                    )
        return measurement_items

    def _extract_financial_items(self, page):
        """Extrai itens financeiros usando as linhas da subclasse."""
        lines = self._get_financial_lines(page)

        is_capturing = False
        temp_items = []

        for clean_txt in lines:
            upper_txt = clean_txt.upper()

            if not clean_txt:
                continue

            # Detecta início da tabela financeira
            if ("DESCRI" in upper_txt or "ITENS" in upper_txt) and "FATURA" in upper_txt:
                is_capturing = True
                continue

            # Detecta fim da tabela
            if is_capturing and (
                upper_txt.startswith("SUBTOTAL")
                or upper_txt.startswith("TOTAL")
                or "EQUIPAMENTOS DE MEDIÇÃO" in upper_txt
            ):
                if upper_txt.startswith("TOTAL") or "EQUIPAMENTOS" in upper_txt:
                    is_capturing = False
                    break
                continue

            if is_capturing:
                item = self._process_financial_line(clean_txt, upper_txt)
                if item:
                    temp_items.append(item)

        return temp_items

    def _process_financial_line(self, clean_txt, upper_txt):
        """Processa uma linha financeira individual. Compartilhado."""
        # Filtros de ruído
        if any(term in upper_txt for term in IGNORED_TERMS):
            return None
        if re.match(r"^\d{5,}", clean_txt):
            return None

        # Filtra linhas de histórico soltas (ex: "AGO25 477.00 30 LID")
        if re.match(
            r"^(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\d{2}\s",
            clean_txt,
        ):
            return None

        # Filtra linha de totalização (só números, sem descrição)
        if re.match(r"^\d+[.,]\d{2}\s+\d+[.,]\d{2}", clean_txt):
            return None

        info = clean_line(clean_txt)

        if info and info["description"] and len(info["description"]) > 2:
            desc_upper = info["description"].upper().strip()

            if desc_upper in JUNK_DESCRIPTIONS:
                return None

            if HISTORY_REGEX.match(desc_upper):
                return None

            value_cols = process_values(info["values_str"], info["type"])
            return {
                "descricao": info["description"],
                "unidade": info["unit"],
                **value_cols,
            }

        return None


# ==============================================================================
# PARSER 2025
# ==============================================================================


class Parser2025(InvoiceParser):
    """Parser para faturas Enel-CE no formato do ano 2025."""

    def _extract_reference(self, text):
        ref_match = re.search(r"(?<!\d/)\b(\d{2}/\d{4})\b", text)
        return ref_match.group(1) if ref_match else "Not Found"

    def _get_financial_lines(self, page):
        text = page.extract_text(layout=True)
        return [line.strip() for line in text.split("\n") if line.strip()]


# ==============================================================================
# PARSER 2026
# ==============================================================================


class Parser2026(InvoiceParser):
    """Parser para faturas Enel-CE no formato do ano 2026."""

    def _preprocess_line(self, line):
        return clean_cmyk_artifacts(line)

    def _extract_reference(self, text):
        # Referência na linha de pagamento
        ref_match = re.search(
            r"\d{2}/\d{2}/\d{4}\s+\d+\s+(\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+[\d.,]+",
            text,
        )
        if ref_match:
            return ref_match.group(1)

        # Fallback: padrão VENCIMENTO
        ref_fallback = re.search(
            r"(\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+R\$", text
        )
        if ref_fallback:
            return ref_fallback.group(1)

        return "Not Found"

    def _extract_client_id(self, text):
        # Tenta o padrão base primeiro
        code_match = re.search(
            r"utilizando\s+o\s+código\s+(\d+)", text, re.IGNORECASE
        )
        if code_match:
            return code_match.group(1)

        # Padrão 2026: "4869679 / 52217494 R$"
        id_match = re.search(r"(\d{7,12})\s*/\s*(\d{7,12})\s+R\$", text)
        if id_match:
            return id_match.group(2)

        # Fallback visual
        visual_match = re.search(r"\b(\d{7,12})\s*\n\s*\d{2}/\d{4}", text)
        if visual_match:
            return visual_match.group(1)

        return "Not Found"

    def _get_financial_lines(self, page):
        """
        No formato 2026, extract_text(layout=True) gera texto intercalado.
        Usa extract_words() agrupado por coordenada Y para reconstruir linhas.
        """
        words = page.extract_words(
            x_tolerance=1, y_tolerance=1, keep_blank_chars=False
        )

        lines_by_y = defaultdict(list)
        for w in words:
            y = round(float(w["top"]), 0)
            lines_by_y[y].append(w)

        reconstructed_lines = []
        for y in sorted(lines_by_y.keys()):
            ws = sorted(lines_by_y[y], key=lambda w: float(w["x0"]))
            ws = [
                w
                for w in ws
                if float(w["x0"]) > 0
                or not re.match(r"^[CMYK]+$", w["text"])
            ]
            line_text = " ".join(w["text"] for w in ws).strip()
            if line_text:
                reconstructed_lines.append(line_text)

        return reconstructed_lines


# ==============================================================================
# DETECÇÃO DE ANO
# ==============================================================================


def _detect_invoice_year(file_path, password=None):
    """
    Detecta o ano da fatura para rotear para o parser correto.
    Retorna o ano como inteiro (ex: 2025, 2026).
    """
    try:
        pdf_context = pdfplumber.open(file_path, password=password)

        with pdf_context as pdf:
            page = pdf.pages[0]
            text = page.extract_text(layout=True)

            pay_match = re.search(
                r"\d{2}/\d{2}/(\d{4})\s+\d+\s+\d{2}/(\d{4})\s+\d{2}/\d{2}/\d{4}\s+[\d.,]+",
                text,
            )
            if pay_match:
                return int(pay_match.group(2))

            ref_match = re.search(
                r"(\d{2}/(\d{4}))\s+\d{2}/\d{2}/\d{4}\s+R\$", text
            )
            if ref_match:
                return int(ref_match.group(2))

            simple_match = re.search(r"(?<!\d/)\b\d{2}/(\d{4})\b", text)
            if simple_match:
                return int(simple_match.group(1))

    except Exception:
        pass

    return 2025


# ==============================================================================
# INTERFACE PÚBLICA
# ==============================================================================


def extract_data_from_pdf(file_path, password=None):
    """
    Extrai dados do PDF e retorna dois DataFrames:
    - df_financeiro: Dados financeiros com coluna 'mes_referencia'
    - df_medicao: Dados de medição com coluna 'mes_referencia'

    Esta função é a interface principal usada pelo sistema de importação.
    Roteia automaticamente para o parser correto baseado no ano da fatura.
    """
    # 1. Detecta o ano e instancia o parser correto
    year = _detect_invoice_year(file_path, password)

    if year >= 2026:
        parser = Parser2026(file_path, password)
    else:
        parser = Parser2025(file_path, password)

    raw_data = parser.extract()

    if not raw_data:
        return pd.DataFrame(), pd.DataFrame()

    reference = raw_data.get("reference", "Not Found")
    client_id = raw_data.get("client_id", "Desconhecido")

    # 2. Converte items financeiros em DataFrame
    items = raw_data.get("items", [])
    if items:
        df_fin = pd.DataFrame(items)
        df_fin["mes_referencia"] = reference
        df_fin["numero_cliente"] = client_id

        df_fin = standardize_frame(df_fin, MAP_COLS)

        numeric_cols = [
            "quantidade",
            "preco_unitario",
            "valor_total",
            "pis_cofins",
            "base_calculo_icms",
            "aliquota_icms",
            "valor_icms",
            "tarifa_unitaria",
        ]

        for col in numeric_cols:
            if col in df_fin.columns:
                df_fin[col] = (
                    df_fin[col].astype(str).apply(normalize_negative_value).str.strip()
                )
                df_fin[col] = pd.to_numeric(df_fin[col], errors="coerce").fillna(0)
    else:
        df_fin = pd.DataFrame()

    # 3. Converte dados de medição em DataFrame
    measurements = raw_data.get("measurement", [])
    if measurements:
        df_med = pd.DataFrame(measurements)
        df_med["mes_referencia"] = reference
        df_med["numero_cliente"] = client_id

        df_med = standardize_frame(df_med, MAP_COLS)

        numeric_cols_med = [
            "leitura_anterior",
            "leitura_atual",
            "fator_multiplicador",
            "consumo_kwh",
            "numero_dias",
        ]

        for col in numeric_cols_med:
            if col in df_med.columns:
                df_med[col] = (
                    df_med[col].astype(str).apply(normalize_negative_value).str.strip()
                )
                df_med[col] = pd.to_numeric(df_med[col], errors="coerce")
    else:
        df_med = pd.DataFrame()

    # Garante colunas essenciais mesmo se vazias
    if not df_med.empty and "numero_dias" not in df_med.columns:
        df_med["numero_dias"] = 30
    if not df_med.empty and "segmento" not in df_med.columns:
        df_med["segmento"] = "Convencional"

    return df_fin, df_med
