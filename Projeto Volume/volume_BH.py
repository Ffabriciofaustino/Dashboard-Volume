import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# ======================================================
# CAMINHO DOS ARQUIVOS
# ======================================================

BASE_DIR = Path(__file__).resolve().parent

arquivo_pesos = BASE_DIR / "volume.xlsx"
arquivo_grade = BASE_DIR / "GRADE MI  MAIO 2026.xlsx"

print("=== INICIANDO PROCESSAMENTO ===\n")

# ======================================================
# LEITURA DOS ARQUIVOS
# ======================================================

df = pd.read_excel(arquivo_pesos)

df.columns = (
    df.columns
    .astype(str)
    .str.upper()
    .str.strip()
)

df_grade = pd.read_excel(
    arquivo_grade,
    header=0
)

df_grade.columns = (
    df_grade.columns
    .astype(str)
    .str.upper()
    .str.strip()
)

print("✅ Planilhas carregadas com sucesso")
print(f"📄 Total linhas PESOS: {len(df)}")
print(f"📄 Total linhas GRADE: {len(df_grade)}")
print()

# ======================================================
# MOSTRAR COLUNAS DA GRADE
# ======================================================

print("📋 Colunas encontradas na planilha GRADE:")
print(df_grade.columns.tolist())
print()

# ======================================================
# COLUNAS UTILIZADAS
# ======================================================

COL_DATA = "DATA ENTREGA"
COL_CIDADE = "CIDADE"
COL_PESO = "PESO TOTAL"

# ======================================================
# TRATAMENTO DE DATA
# ======================================================

df[COL_DATA] = pd.to_datetime(
    df[COL_DATA],
    dayfirst=True,
    errors="coerce"
).dt.date

print("✅ Datas tratadas com sucesso\n")

# ======================================================
# TRATAMENTO DE PESO
# ======================================================

df[COL_PESO] = (
    df[COL_PESO]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

df[COL_PESO] = pd.to_numeric(
    df[COL_PESO],
    errors="coerce"
).fillna(0)

print("✅ Pesos tratados com sucesso\n")

# ======================================================
# PADRONIZAÇÃO DE TEXTO
# ======================================================

df[COL_CIDADE] = (
    df[COL_CIDADE]
    .astype(str)
    .str.upper()
    .str.strip()
)

df_grade.columns = (
    df_grade.columns
    .astype(str)
    .str.upper()
    .str.strip()
)

df_grade["CIDADE"] = (
    df_grade["CIDADE"]
    .astype(str)
    .str.upper()
    .str.strip()
)

df_grade["MALHA"] = (
    df_grade["MALHA"]
    .astype(str)
    .str.upper()
    .str.strip()
)

df_grade["TSP"] = (
    df_grade["TSP"]
    .astype(str)
    .str.upper()
    .str.strip()
)

df_grade["EMPRESA"] = (
    df_grade["EMPRESA"]
    .astype(str)
    .str.upper()
    .str.strip()
)

print("✅ Texto padronizado com sucesso\n")

# ======================================================
# DEFINIR DIA DA GRADE (PRÓXIMO DIA ÚTIL)
# ======================================================

hoje = datetime.today()

dia_semana_hoje = hoje.weekday()

# 0 = SEG
# 1 = TER
# 2 = QUA
# 3 = QUI
# 4 = SEX
# 5 = SAB
# 6 = DOM

# sexta -> segunda
if dia_semana_hoje == 4:
    data_grade = hoje + timedelta(days=3)

# sábado -> segunda
elif dia_semana_hoje == 5:
    data_grade = hoje + timedelta(days=2)

# domingo -> segunda
elif dia_semana_hoje == 6:
    data_grade = hoje + timedelta(days=1)

# demais dias -> próximo dia
else:
    data_grade = hoje + timedelta(days=1)

data_grade = data_grade.date()

print(f"📅 Hoje: {hoje.date()}")
print(f"📅 Data considerada para grade: {data_grade}")
print()

# ======================================================
# MAPA DOS DIAS
# ======================================================

mapa_dias = {
    0: "SEG",
    1: "TER",
    2: "QUA",
    3: "QUI",
    4: "SEX"
}

dia_grade = mapa_dias[data_grade.weekday()]

print(f"📌 Dia da grade identificado: {dia_grade}")
print()

# ======================================================
# COLUNAS DA GRADE
# ======================================================

colunas_grade = [
    "CIDADE",
    "SEG",
    "TER",
    "QUA",
    "QUI",
    "SEX",
    "EMPRESA",
    "TSP",
    "MALHA"
]

# ======================================================
# REMOVER MALHA ORIGINAL DO VOLUME
# ======================================================

if "MALHA" in df.columns:
    df.drop(columns=["MALHA"], inplace=True)

# ======================================================
# PROCV DA GRADE
# ======================================================

df = df.merge(
    df_grade[colunas_grade].drop_duplicates(subset=["CIDADE"]),
    how="left",
    left_on=COL_CIDADE,
    right_on="CIDADE",
    suffixes=("", "_GRADE")
)

print("✅ PROCV realizado com sucesso\n")

# ======================================================
# AJUSTAR COLUNAS DA GRADE
# ======================================================

# EMPRESA
if "EMPRESA_GRADE" in df.columns:
    df["EMPRESA"] = df["EMPRESA_GRADE"]

# TSP
if "TSP_GRADE" in df.columns:
    df["TSP"] = df["TSP_GRADE"]

# MALHA
if "MALHA_GRADE" in df.columns:
    df["MALHA"] = df["MALHA_GRADE"]

# ======================================================
# TRATAR VALORES NULOS
# ======================================================

df["EMPRESA"] = df["EMPRESA"].fillna("SEM GRADE")
df["TSP"] = df["TSP"].fillna("SEM TSP")
df["MALHA"] = df["MALHA"].fillna("SEM MALHA")

# ======================================================
# REGRA ESPECIAL - BELO HORIZONTE
# ======================================================

df.loc[
    df[COL_CIDADE] == "BELO HORIZONTE",
    "MALHA"
] = "BELO HORIZONTE"

# ======================================================
# CLASSIFICAÇÃO GRADE / ABERTO
# ======================================================

def classificar_grade(linha):

    try:

        valor_grade = linha[dia_grade]

        # se cidade atende no dia da grade
        if valor_grade == 1:
            return "GRADE"

        else:
            return "ABERTO"

    except:
        return "ABERTO"

df["TIPO_PEDIDO"] = df.apply(
    classificar_grade,
    axis=1
)

print("✅ Classificação criada com sucesso\n")

print("📊 Resumo:")
print(df["TIPO_PEDIDO"].value_counts())
print()

# ======================================================
# AGRUPAR PESOS
# ======================================================

relatorio = (
    df
    .groupby(
        [
            COL_DATA,
            COL_CIDADE,
            "MALHA",
            "TSP",
            "EMPRESA",
            "TIPO_PEDIDO",
            "EQUIPE VENDA"
        ],
        as_index=False
    )
    .agg(
        PESO_TOTAL=(COL_PESO, "sum")
    )
)

print("✅ Relatório consolidado criado com sucesso\n")

# ======================================================
# EXEMPLO RESULTADO
# ======================================================

print("📋 Exemplo do resultado:\n")

print(relatorio.head(20))

print()

# ======================================================
# EXPORTAÇÃO
# ======================================================

arquivo_saida = BASE_DIR / "relatorio_consolidado_grade.xlsx"

relatorio.to_excel(
    arquivo_saida,
    index=False
)

print("✅ RELATÓRIO GERADO COM SUCESSO")
print(f"📄 Arquivo salvo em: {arquivo_saida}")