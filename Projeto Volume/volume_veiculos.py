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

print("=== INICIANDO ===\n")

# ======================================================
# LEITURA
# ======================================================

df = pd.read_excel(arquivo_pesos)
df_grade = pd.read_excel(arquivo_grade)

# ======================================================
# 🔥 NORMALIZAR NOMES DAS COLUNAS (ANTI BUG)
# ======================================================

df.columns = df.columns.str.strip().str.upper()
df_grade.columns = df_grade.columns.str.strip().str.upper()

print("COLUNAS PESOS:", df.columns.tolist())
print("COLUNAS GRADE:", df_grade.columns.tolist(), "\n")

# ======================================================
# DEFINIR COLUNAS (AGORA EM UPPER)
# ======================================================

COL_DATA = "DATA ENTREGA"
COL_CIDADE = "CIDADE"
COL_PESO = "PESO TOTAL"

# ======================================================
# VALIDAR
# ======================================================

colunas_grade_necessarias = ["CIDADE", "MALHA", "TSP", "EMPRESA", "ROTEIRIZADOR", "VEICULO"]

for col in colunas_grade_necessarias:
    if col not in df_grade.columns:
        raise Exception(f"❌ Coluna não encontrada na GRADE: {col}")

# ======================================================
# DATA
# ======================================================

df[COL_DATA] = pd.to_datetime(
    df[COL_DATA].astype(str).str.strip(),
    format="%d/%m/%Y",
    errors="coerce"
)

df = df.dropna(subset=[COL_DATA])
df[COL_DATA] = df[COL_DATA].dt.date

# ======================================================
# PESO
# ======================================================

df[COL_PESO] = (
    df[COL_PESO]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

df[COL_PESO] = pd.to_numeric(df[COL_PESO], errors="coerce").fillna(0)

# ======================================================
# TEXTO
# ======================================================

df[COL_CIDADE] = df[COL_CIDADE].astype(str).str.upper().str.strip()

for col in colunas_grade_necessarias:
    df_grade[col] = df_grade[col].astype(str).str.upper().str.strip()

# ======================================================
# DATA GRADE
# ======================================================

hoje = datetime.today().date()
data_grade = hoje + timedelta(days=1)

df["TIPO_PEDIDO"] = df[COL_DATA].apply(
    lambda x: "GRADE" if x == data_grade else "ABERTO"
)

# ======================================================
# 🔥 MERGE ANTES DO AGRUPAMENTO
# ======================================================

df = df.merge(
    df_grade[["CIDADE", "MALHA", "TSP", "EMPRESA", "ROTEIRIZADOR"]]
    .drop_duplicates("CIDADE"),
    how="left",
    left_on=COL_CIDADE,
    right_on="CIDADE"
)

# DEBUG
print("\nVERIFICANDO MALHA:")
print(df[["CIDADE", "MALHA"]].head())

# ======================================================
# AGRUPAR POR MALHA
# ======================================================

relatorio = (
    df.groupby(
        [
            COL_DATA,
            "MALHA",
            "TSP",
            "EMPRESA",
            "ROTEIRIZADOR",
            "TIPO_PEDIDO"
        ],
        as_index=False
    )
    .agg(PESO_TOTAL=(COL_PESO, "sum"))
)

# ======================================================
# VEÍCULO POR MALHA
# ======================================================

relatorio = relatorio.merge(
    df_grade[["MALHA", "VEICULO"]].drop_duplicates("MALHA"),
    how="left",
    on="MALHA"
)

relatorio["VEICULO"] = relatorio["VEICULO"].fillna("SEM VEICULO")

# ======================================================
# CAPACIDADE
# ======================================================

capacidade = {
    "SEMI-LEVE": 1500,
    "3/4": 3500,
    "SUPER 3/4": 5000
}

relatorio["CAPACIDADE"] = relatorio["VEICULO"].map(capacidade).fillna(0)

# ======================================================
# VEÍCULOS NECESSÁRIOS
# ======================================================

relatorio["QTD_VEICULOS"] = relatorio.apply(
    lambda r: math.ceil(r["PESO_TOTAL"] / r["CAPACIDADE"]) if r["CAPACIDADE"] > 0 else 0,
    axis=1
)

# ======================================================
# EXPORTAR
# ======================================================

arquivo_saida = BASE_DIR / "relatorio_final.xlsx"
relatorio.to_excel(arquivo_saida, index=False)

print("\n✅ RELATÓRIO FINAL GERADO")
print(f"📄 {arquivo_saida}")