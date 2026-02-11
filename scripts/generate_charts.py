import os
import sys

import pandas as pd
import plotly.express as px
import plotly.io as pio

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from config.tax_rules import get_cip_expected_value, get_law_rate

# Configurações de exportação
pio.templates.default = "plotly_white"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

def generate_mock_data():
    """Gera dados simulados para um ano de consumo."""
    data = {
        "mes_referencia": [
            "JAN/2024", "FEV/2024", "MAR/2024", "ABR/2024", "MAI/2024", "JUN/2024",
            "JUL/2024", "AGO/2024", "SET/2024", "OUT/2024", "NOV/2024", "DEZ/2024"
        ],
        "consumo_kwh": [
            350, 320, 280, 420, 450, 480,
            390, 310, 290, 410, 460, 490
        ],
        "R$ Pago": [
            35.50, 32.10, 28.90, 45.20, 48.30, 52.10,
            42.80, 31.50, 29.40, 44.10, 49.50, 53.20
        ]
    }
    return pd.DataFrame(data)

def generate_charts():
    print("Gerando gráficos para o artigo...")

    # Check if assets dir exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Gera dados mockados
    df = generate_mock_data()

    # Aplica regras da lei
    df["R$ Lei"] = df["consumo_kwh"].apply(lambda x: get_cip_expected_value(x))
    df["Alíquota Lei"] = df["consumo_kwh"].apply(lambda x: get_law_rate(x)) * 100

    # Calcula Alíquota Paga (Reversa)
    # Tarifa base estimada (pode variar, usando uma fixa para simplificação no gráfico)
    BASE_RATE = 111.05
    df["Alíquota Paga"] = (df["R$ Pago"] / BASE_RATE) * 100

    # GRÁFICO 1: Comparativo de Valores (R$)
    # Melt para formato longo
    df_melted_val = df.melt(
        id_vars=["mes_referencia"],
        value_vars=["R$ Pago", "R$ Lei"],
        var_name="Tipo",
        value_name="Valor (R$)"
    )

    fig_val = px.bar(
        df_melted_val,
        x="mes_referencia",
        y="Valor (R$)",
        color="Tipo",
        barmode="group",
        color_discrete_map={"R$ Pago": "#EF553B", "R$ Lei": "#00CC96"},
        title="Comparativo: Valor Cobrado vs. Valor Legal"
    )
    fig_val.update_layout(
        width=800,
        height=400,
        legend_title_text="",
        xaxis_title="",
        yaxis_title="Valor (R$)"
    )

    val_chart_path = os.path.join(OUTPUT_DIR, "linkedin_chart_values.png")
    fig_val.write_image(val_chart_path, scale=2)
    print(f"Salvo: {val_chart_path}")

    # GRÁFICO 2: Evolução das Alíquotas (%)
    df_melted_aliq = df.melt(
        id_vars=["mes_referencia"],
        value_vars=["Alíquota Lei", "Alíquota Paga"],
        var_name="Tipo",
        value_name="Alíquota (%)"
    )

    fig_aliq = px.line(
        df_melted_aliq,
        x="mes_referencia",
        y="Alíquota (%)",
        color="Tipo",
        markers=True,
        line_shape="spline",
        color_discrete_map={"Alíquota Lei": "#00CC96", "Alíquota Paga": "#EF553B"},
        title="Divergência de Alíquotas: Lei vs. Cobrança Real"
    )
    fig_aliq.update_layout(
        width=800,
        height=400,
        legend_title_text="",
        xaxis_title="",
        yaxis_title="Alíquota (%)"
    )

    aliq_chart_path = os.path.join(OUTPUT_DIR, "linkedin_chart_aliquots.png")
    fig_aliq.write_image(aliq_chart_path, scale=2)
    print(f"Salvo: {aliq_chart_path}")

if __name__ == "__main__":
    generate_charts()
