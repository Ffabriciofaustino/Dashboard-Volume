import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import math

# ======================================================
# CAMINHO
# ======================================================

BASE_DIR = Path(__file__).resolve().parent

arquivo_pesos = BASE_DIR / "volume.xlsx"
arquivo_grade = BASE_DIR / "GRADE MI  MAIO 2026.xlsx"

print("=== INICIANDO PROCESSAMENTO ===\n")

# ======================================================
# LEITURA
# ======================================================

df = pd.read_excel(arquivo_pesos)
df_grade = pd.read_excel(arquivo_grade)

df.columns = df.columns.str.strip()
df_grade.columns = df_grade.columns.str.strip()

# ======================================================
# COLUNAS
# ======================================================

COL_DATA = "Data Entrega"
COL_CIDADE = "Cidade"
COL_PESO = "Peso Total"
COL_MALHA = "Malha"

# ======================================================
# TRATAMENTO DE DATA
# ======================================================

df[COL_DATA] = pd.to_datetime(
    df[COL_DATA].astype(str).str.strip(),
    format="%d/%m/%Y",
    errors="coerce"
)

df = df.dropna(subset=[COL_DATA])
df[COL_DATA] = df[COL_DATA].dt.date

print("Datas tratadas\n")

# ======================================================
# TRATAMENTO DE PESO
# ======================================================

df[COL_PESO] = (
    df[COL_PESO]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

df[COL_PESO] = pd.to_numeric(df[COL_PESO], errors="coerce").fillna(0)

print("Pesos tratados\n")

# ======================================================
# PADRONIZAÇÃO
# ======================================================

df[COL_CIDADE] = df[COL_CIDADE].astype(str).str.upper().str.strip()
df[COL_MALHA] = df[COL_MALHA].astype(str).str.upper().str.strip()

for col in ["Malha", "TSP", "Empresa", "Roteirizador"]:
    df_grade[col] = df_grade[col].astype(str).str.upper().str.strip()

print("Texto padronizado\n")

# ======================================================
# DATA DA GRADE
# ======================================================

hoje = datetime.today().date()
data_grade = hoje + timedelta(days=1)

df["TIPO_PEDIDO"] = df[COL_DATA].apply(
    lambda x: "GRADE" if x == data_grade else "ABERTO"
)

# ======================================================
# AGRUPAMENTO POR MALHA
# ======================================================

relatorio = (
    df.groupby(
        [COL_DATA, COL_MALHA, "TIPO_PEDIDO"],
        as_index=False
    )
    .agg(PESO_TOTAL=(COL_PESO, "sum"))
)

# ======================================================
# TRAZER DADOS DA GRADE
# ======================================================

relatorio = relatorio.merge(
    df_grade[["Malha", "TSP", "Empresa", "Roteirizador"]]
    .drop_duplicates("Malha"),
    how="left",
    on="Malha"
)

# ======================================================
# BIBLIOTECA DE VEÍCULOS (EDITÁVEL)
# ======================================================

biblioteca_veiculos = {
    "CONTAGEM": "SEMI-LEVE",
    "IPATINGA": "3/4",
    "BETIM": "SEMI-LEVE"
}

relatorio["Veiculo"] = relatorio["Malha"].map(biblioteca_veiculos).fillna("SEM VEICULO")

# ======================================================
# 🔥 NOVA COLUNA MALHA_VEICULO
# ======================================================

def montar_malha_veiculo(row):
    malha = row["Malha"]
    veiculo = row["Veiculo"]

    if malha == "SEM MALHA" or veiculo == "SEM VEICULO":
        return "INDEFINIDO"

    return f"{malha} - {veiculo}"

relatorio["MALHA_VEICULO"] = relatorio.apply(montar_malha_veiculo, axis=1)

# ======================================================
# CAPACIDADE
# ======================================================

capacidade = {
    "SEMI-LEVE": 1500,
    "3/4": 3500,
    "SUPER 3/4": 5000
}

relatorio["CAPACIDADE"] = relatorio["Veiculo"].map(capacidade).fillna(0)

# ======================================================
# STATUS DE CARGA
# ======================================================

relatorio["EXCESSO_KG"] = (relatorio["PESO_TOTAL"] - relatorio["CAPACIDADE"]).clip(lower=0)

relatorio["STATUS_CARGA"] = relatorio["EXCESSO_KG"].apply(
    lambda x: "EXCESSO" if x > 0 else "OK"
)

# ======================================================
# VEÍCULOS NECESSÁRIOS
# ======================================================

relatorio["QTD_VEICULOS"] = relatorio.apply(
    lambda r: math.ceil(r["PESO_TOTAL"] / r["CAPACIDADE"]) if r["CAPACIDADE"] > 0 else 0,
    axis=1
)

# ======================================================
# DIVISÃO DE CARGA
# ======================================================

relatorio["DIVISAO_CARGA"] = relatorio.apply(
    lambda r: f'{r["QTD_VEICULOS"]}x {round(r["PESO_TOTAL"]/r["QTD_VEICULOS"],2)} kg'
    if r["QTD_VEICULOS"] > 1 else f'1x {round(r["PESO_TOTAL"],2)} kg',
    axis=1
)

# ======================================================
# ORGANIZAÇÃO FINAL
# ======================================================

relatorio = relatorio[
    [
        COL_DATA,
        "Malha",
        "MALHA_VEICULO",
        "TSP",
        "Empresa",
        "Roteirizador",
        "Veiculo",
        "CAPACIDADE",
        "PESO_TOTAL",
        "QTD_VEICULOS",
        "DIVISAO_CARGA",
        "EXCESSO_KG",
        "STATUS_CARGA",
        "TIPO_PEDIDO"
    ]
]

# ======================================================
# EXPORTAÇÃO
# ======================================================

arquivo_saida = BASE_DIR / "relatorio_final_malha_veiculo.xlsx"

relatorio.to_excel(arquivo_saida, index=False)

print("✅ RELATÓRIO FINAL GERADO COM MALHA_VEICULO")
print(f"📄 Arquivo salvo em: {arquivo_saida}")