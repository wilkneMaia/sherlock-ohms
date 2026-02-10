import re

import pandas as pd
import pdfplumber

# --- HELPER FUNCTIONS ---


def normalize_negative_value(value_str):
    """
    Normaliza valores negativos no formato "19,52-" para "-19.52"
    Também trata valores positivos convertendo vírgula para ponto.
    """
    if not value_str:
        return value_str

    # Converte para string se não for
    if not isinstance(value_str, str):
        value_str = str(value_str)

    value_str = value_str.strip()

    # Se estiver vazio após strip, retorna como está
    if not value_str:
        return value_str

    # Verifica se já tem sinal negativo no início
    is_negative = False
    if value_str.startswith("-"):
        is_negative = True
        value_str = value_str[1:]  # Remove o sinal do início temporariamente
    elif value_str.endswith("-"):
        # Sinal negativo no final (ex: "19,52-")
        is_negative = True
        value_str = value_str[:-1]  # Remove o sinal do final

    # Converte vírgula para ponto
    value_str = value_str.replace(",", ".")

    # Adiciona sinal negativo no início se necessário
    if is_negative:
        value_str = "-" + value_str

    return value_str


def clean_line(line):
    """
    Tenta separar a linha em: Descrição | Unidade | Valores
    """
    # 1. Remove Histórico (Estratégia Conservadora)
    # Remove apenas se tiver espaço antes (ex: " JAN/24") para não quebrar linhas que começam com texto
    history_pattern = (
        r"\s(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)[\s\/]*\d{2,4}.*$"
    )
    cleaned_line = re.sub(history_pattern, "", line, flags=re.IGNORECASE).strip()

    if not cleaned_line:
        return None

    # 2. Tenta encontrar unidades conhecidas (kWh, dias, etc)
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

    # 3. Itens Simples (Descrição + Valor)
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

    # Normaliza valores negativos (formato "19,52-" -> "-19.52")
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

        # Tenta encaixar os tokens nos campos
        if len(tokens) >= 8:
            for i, field in enumerate(fields):
                columns[field] = tokens[i]
        elif len(tokens) >= 3:
            columns["quantidade"] = tokens[0]
            columns["preco_unitario"] = tokens[1]
            columns["valor_total"] = tokens[2]
            # Preenche o restante se houver
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


def extract_measurement_2025(full_text):
    measurement_items = []
    lines = full_text.split("\n")
    is_capturing = False

    # Regex ajustado para pegar medição (Consumo)
    # Procura linha com data (dd/mm/aaaa) e números
    regex_measure = re.compile(
        r"(\S+)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)"
    )

    for line in lines:
        line_upper = line.upper().strip()

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

            match = regex_measure.search(line)
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


# --- MAIN EXTRACTION FUNCTIONS ---


def extract_invoice_data_2025(file_path, password=None):
    """
    Extrai dados brutos de faturas Enel-CE no formato do ano 2025.
    """
    data = {
        "reference": "Not Found",
        "client_id": "Not Found",
        "items": [],
        "measurement": [],
    }

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

    try:
        # Verifica se é path string ou objeto de arquivo (Streamlit)
        if isinstance(file_path, str):
            pdf_context = pdfplumber.open(file_path, password=password)
        else:
            pdf_context = pdfplumber.open(file_path, password=password)

        with pdf_context as pdf:
            page = pdf.pages[0]
            # layout=True é essencial para manter a estrutura visual
            text = page.extract_text(layout=True)

            # 1. Reference (Mês/Ano)
            ref_match = re.search(r"(?<!\d/)\b(\d{2}/\d{4})\b", text)
            if ref_match:
                data["reference"] = ref_match.group(1)

            # 2. Client ID
            code_match = re.search(
                r"utilizando\s+o\s+código\s+(\d+)", text, re.IGNORECASE
            )
            if code_match:
                data["client_id"] = code_match.group(1)
            else:
                visual_match = re.search(r"\b(\d{7,12})\s*\n\s*\d{2}/\d{4}", text)
                if visual_match:
                    data["client_id"] = visual_match.group(1)

            # 3. Measurement Data
            data["measurement"] = extract_measurement_2025(text)

            # 4. Financial Items extraction
            lines = text.split("\n")
            is_capturing = False
            temp_items = []

            for line in lines:
                clean_txt = line.strip()
                upper_txt = clean_txt.upper()

                if not clean_txt:
                    continue

                # Detecta início da tabela financeira
                if (
                    "DESCRI" in upper_txt or "ITENS" in upper_txt
                ) and "FATURA" in upper_txt:
                    is_capturing = True
                    continue

                # Detecta fim da tabela
                if is_capturing and ("TOTAL" in upper_txt or "SUBTOTAL" in upper_txt):
                    is_capturing = False
                    break

                if is_capturing:
                    # Filtros de ruído
                    if any(term in upper_txt for term in IGNORED_TERMS):
                        continue
                    if re.match(r"^\d{5,}", clean_txt):
                        continue  # Números soltos grandes

                    info = clean_line(clean_txt)

                    if info and info["description"] and len(info["description"]) > 2:
                        desc_upper = info["description"].upper().strip()

                        # --- FILTRO DE LIXO PÓS-EXTRAÇÃO (AQUI É A CORREÇÃO) ---
                        # Ignora linhas que sejam apenas cabeçalhos fiscais
                        if desc_upper in [
                            "PIS",
                            "COFINS",
                            "ICMS",
                            "I CMS",
                            "TOTAL",
                            "SUBTOTAL",
                        ]:
                            continue

                        # Ignora linhas que sejam HISTÓRICO (Ex: ABR/24 ou ABR 24)
                        # Isso elimina o erro [ABR24] sem quebrar as outras linhas
                        if re.match(
                            r"^(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)[\s\/\-]*\d{2,4}$",
                            desc_upper,
                        ):
                            continue
                        # -------------------------------------------------------

                        value_cols = process_values(info["values_str"], info["type"])
                        item = {
                            "descricao": info["description"],
                            "unidade": info["unit"],
                            **value_cols,
                        }
                        temp_items.append(item)

            data["items"] = temp_items
            return data

    except Exception as e:
        # Se for erro de senha, avisa diferente
        if "Password" in str(e):
            print(f"❌ Erro de Senha: {e}")
        else:
            print(f"❌ Erro Crítico: {e}")
        return None


# --- FUNÇÕES PARA FATURA 2026 ---


def clean_cmyk_artifacts(line):
    """
    Remove artefatos de marcadores CMYK que vazam no texto extraído
    das faturas Enel-CE a partir de 2026.
    Ex: "Y     Energia Atv Inj..." → "Energia Atv Inj..."
    Ex: "CMCM CCMMCCMM Energia Consumida..." → "Energia Consumida..."
    """
    if not line:
        return line

    # Remove prefixos CMYK comuns no início da linha
    # Padrão: sequências de C, M, Y, K (maiúsculas) seguidas de espaços
    cleaned = re.sub(
        r"^(?:[CMYK]{1,8}\s+)+",
        "",
        line.strip(),
    )

    return cleaned.strip()


def extract_measurement_2026(full_text):
    """
    Extrai dados de medição das faturas Enel-CE no formato de 2026.
    Similar ao 2025, mas com limpeza de artefatos CMYK.
    """
    measurement_items = []
    lines = full_text.split("\n")
    is_capturing = False

    regex_measure = re.compile(
        r"(\S+)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)"
    )

    for line in lines:
        # Limpa artefatos CMYK antes de processar
        cleaned_line = clean_cmyk_artifacts(line)
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

            match = regex_measure.search(cleaned_line)
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


def extract_invoice_data_2026(file_path, password=None):
    """
    Extrai dados brutos de faturas Enel-CE no formato do ano 2026.
    Adaptado para lidar com artefatos CMYK e o novo layout.
    """
    data = {
        "reference": "Not Found",
        "client_id": "Not Found",
        "items": [],
        "measurement": [],
    }

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

    try:
        if isinstance(file_path, str):
            pdf_context = pdfplumber.open(file_path, password=password)
        else:
            pdf_context = pdfplumber.open(file_path, password=password)

        with pdf_context as pdf:
            page = pdf.pages[0]
            text = page.extract_text(layout=True)

            # 1. Reference (Mês/Ano) - Busca na seção MÊS/ANO VENCIMENTO
            # No formato 2026, a referência aparece na linha com o valor R$
            # Ex: "4869679 / 52217494 R$ 193,24" com MÊS/ANO acima
            # A referência mais confiável é na linha de dados de pagamento:
            # "08/01/2026 0202601197000378 01/2026 25/01/2026 193,24"
            ref_match = re.search(
                r"\d{2}/\d{2}/\d{4}\s+\d+\s+(\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+[\d.,]+",
                text,
            )
            if ref_match:
                data["reference"] = ref_match.group(1)
            else:
                # Fallback: procura no padrão "VENCIMENTO" seguido de data
                ref_fallback = re.search(
                    r"(\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+R\$", text
                )
                if ref_fallback:
                    data["reference"] = ref_fallback.group(1)

            # 2. Client ID - Busca pelo código do cliente
            code_match = re.search(
                r"utilizando\s+o\s+código\s+(\d+)", text, re.IGNORECASE
            )
            if code_match:
                data["client_id"] = code_match.group(1)
            else:
                # No formato 2026, o código aparece na linha:
                # "4869679 / 52217494 R$"
                id_match = re.search(r"(\d{7,12})\s*/\s*(\d{7,12})\s+R\$", text)
                if id_match:
                    data["client_id"] = id_match.group(2)
                else:
                    visual_match = re.search(
                        r"\b(\d{7,12})\s*\n\s*\d{2}/\d{4}", text
                    )
                    if visual_match:
                        data["client_id"] = visual_match.group(1)

            # 3. Measurement Data
            data["measurement"] = extract_measurement_2026(text)

            # 4. Financial Items extraction
            # No formato 2026, extract_text(layout=True) gera texto intercalado
            # (garbled) em muitas linhas. Usando extract_words() com tolerância
            # baixa, as palavras são extraídas corretamente por posição Y.
            from collections import defaultdict

            words = page.extract_words(
                x_tolerance=1, y_tolerance=1, keep_blank_chars=False
            )

            # Agrupa palavras por coordenada Y (arredondada)
            lines_by_y = defaultdict(list)
            for w in words:
                y = round(float(w["top"]), 0)
                lines_by_y[y].append(w)

            # Reconstrói linhas limpas a partir das palavras agrupadas
            reconstructed_lines = []
            for y in sorted(lines_by_y.keys()):
                ws = sorted(lines_by_y[y], key=lambda w: float(w["x0"]))
                # Filtra marcadores CMYK (posição X negativa ou apenas letras CMYK)
                ws = [
                    w
                    for w in ws
                    if float(w["x0"]) > 0
                    or not re.match(r"^[CMYK]+$", w["text"])
                ]
                line_text = " ".join(w["text"] for w in ws).strip()
                if line_text:
                    reconstructed_lines.append(line_text)

            is_capturing = False
            temp_items = []

            for clean_txt in reconstructed_lines:
                upper_txt = clean_txt.upper()

                if not clean_txt:
                    continue

                # Detecta início da tabela financeira
                if (
                    "DESCRI" in upper_txt or "ITENS" in upper_txt
                ) and "FATURA" in upper_txt:
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
                    # Filtros de ruído
                    if any(term in upper_txt for term in IGNORED_TERMS):
                        continue
                    if re.match(r"^\d{5,}", clean_txt):
                        continue

                    # Filtra linhas de histórico soltas (ex: "AGO25 477.00 30 LID")
                    if re.match(
                        r"^(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\d{2}\s",
                        clean_txt,
                    ):
                        continue

                    # Filtra linha de totalização (só números, sem descrição)
                    if re.match(r"^\d+[.,]\d{2}\s+\d+[.,]\d{2}", clean_txt):
                        continue

                    info = clean_line(clean_txt)

                    if info and info["description"] and len(info["description"]) > 2:
                        desc_upper = info["description"].upper().strip()

                        # Ignora cabeçalhos fiscais
                        if desc_upper in [
                            "PIS",
                            "COFINS",
                            "ICMS",
                            "I CMS",
                            "TOTAL",
                            "SUBTOTAL",
                        ]:
                            continue

                        # Ignora linhas de HISTÓRICO
                        if re.match(
                            r"^(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)[\s\/\-]*\d{2,4}$",
                            desc_upper,
                        ):
                            continue

                        value_cols = process_values(info["values_str"], info["type"])
                        item = {
                            "descricao": info["description"],
                            "unidade": info["unit"],
                            **value_cols,
                        }
                        temp_items.append(item)

            data["items"] = temp_items
            return data

    except Exception as e:
        if "Password" in str(e):
            print(f"❌ Erro de Senha: {e}")
        else:
            print(f"❌ Erro Crítico: {e}")
        return None


def _detect_invoice_year(file_path, password=None):
    """
    Detecta o ano da fatura para rotear para o parser correto.
    Retorna o ano como inteiro (ex: 2025, 2026).
    """
    try:
        if isinstance(file_path, str):
            pdf_context = pdfplumber.open(file_path, password=password)
        else:
            pdf_context = pdfplumber.open(file_path, password=password)

        with pdf_context as pdf:
            page = pdf.pages[0]
            text = page.extract_text(layout=True)

            # Busca a referência na linha de pagamento (mais confiável)
            # Formato: "dd/mm/aaaa NNNNN mm/aaaa dd/mm/aaaa valor"
            pay_match = re.search(
                r"\d{2}/\d{2}/(\d{4})\s+\d+\s+\d{2}/(\d{4})\s+\d{2}/\d{2}/\d{4}\s+[\d.,]+",
                text,
            )
            if pay_match:
                return int(pay_match.group(2))

            # Fallback: procura padrão MÊS/ANO com vencimento
            ref_match = re.search(
                r"(\d{2}/(\d{4}))\s+\d{2}/\d{2}/\d{4}\s+R\$", text
            )
            if ref_match:
                return int(ref_match.group(2))

            # Fallback final: primeira referência MM/AAAA no texto
            simple_match = re.search(r"(?<!\d/)\b\d{2}/(\d{4})\b", text)
            if simple_match:
                return int(simple_match.group(1))

    except Exception:
        pass

    # Default: assume formato mais antigo
    return 2025


# --- FUNÇÃO DE INTERFACE (Compatível com a Nova Arquitetura) ---


def standardize_frame(df, mapping):
    """
    Padroniza nomes de colunas e remove caracteres especiais.
    """
    if df.empty:
        return df

    # 1. Normaliza nomes atuais (remove espaços extras e acentos básicos)
    new_cols = []
    for col in df.columns:
        c = str(col).strip()
        # Mapeamento reverso simples para garantir consistência se vier da extração bruta
        new_cols.append(c)
    df.columns = new_cols

    # 2. Renomeia conforme mapa oficial
    df = df.rename(columns=mapping)

    # 3. Garante snake_case para colunas que não estavam no mapa
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

def extract_data_from_pdf(file_path, password=None):
    """
    Extrai dados do PDF e retorna dois DataFrames:
    - df_financeiro: Dados financeiros com coluna 'Referência'
    - df_medicao: Dados de medição com coluna 'Referência'

    Esta função é a interface principal usada pelo sistema de importação.
    Roteia automaticamente para o parser correto baseado no ano da fatura.
    """
    # 1. Detecta o ano e roteia para o parser correto
    year = _detect_invoice_year(file_path, password)

    if year >= 2026:
        raw_data = extract_invoice_data_2026(file_path, password)
    else:
        raw_data = extract_invoice_data_2025(file_path, password)

    if not raw_data:
        return pd.DataFrame(), pd.DataFrame()

    reference = raw_data.get("reference", "Not Found")
    client_id = raw_data.get("client_id", "Desconhecido")

    # Mapeamento Oficial de Colunas
    map_cols = {
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
        # Medição
        "N° Medidor": "numero_medidor",
        "P.Horário/Segmento": "segmento",
        "Data Leitura (Anterior)": "data_leitura_anterior",
        "Leitura (Anterior)": "leitura_anterior",
        "Data Leitura (Atual)": "data_leitura_atual",
        "Leitura (Atual)": "leitura_atual",
        "Fator Multiplicador": "fator_multiplicador",
        "Consumo kWh": "consumo_kwh",
        "N° Dias": "numero_dias"
    }

    # 2. Converte items financeiros em DataFrame
    items = raw_data.get("items", [])
    if items:
        df_fin = pd.DataFrame(items)
        # Adiciona coluna Referência em todas as linhas
        df_fin["mes_referencia"] = reference
        df_fin["numero_cliente"] = client_id

        # Padroniza colunas
        df_fin = standardize_frame(df_fin, map_cols)

        # Converte valores numéricos de string para float
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
                # Normaliza valores negativos e converte para string
                df_fin[col] = (
                    df_fin[col].astype(str).apply(normalize_negative_value).str.strip()
                )
                # Converte para float, ignorando valores vazios ou inválidos
                df_fin[col] = pd.to_numeric(df_fin[col], errors="coerce").fillna(0)
    else:
        df_fin = pd.DataFrame()

    # 3. Converte dados de medição em DataFrame
    measurements = raw_data.get("measurement", [])
    if measurements:
        df_med = pd.DataFrame(measurements)
        # Adiciona coluna Referência em todas as linhas
        df_med["mes_referencia"] = reference
        df_med["numero_cliente"] = client_id

        # Padroniza colunas
        df_med = standardize_frame(df_med, map_cols)

        # Converte valores numéricos de string para float
        numeric_cols_med = [
            "leitura_anterior",
            "leitura_atual",
            "fator_multiplicador",
            "consumo_kwh",
            "numero_dias",
        ]

        for col in numeric_cols_med:
            if col in df_med.columns:
                # Normaliza valores negativos e converte para string
                df_med[col] = (
                    df_med[col].astype(str).apply(normalize_negative_value).str.strip()
                )
                # Converte para float, ignorando valores vazios ou inválidos
                df_med[col] = pd.to_numeric(df_med[col], errors="coerce")
    else:
        df_med = pd.DataFrame()

    # Garante colunas essenciais mesmo se vazias
    if not df_med.empty and "numero_dias" not in df_med.columns:
        df_med["numero_dias"] = 30
    if not df_med.empty and "segmento" not in df_med.columns:
        df_med["segmento"] = "Convencional"

    return df_fin, df_med
