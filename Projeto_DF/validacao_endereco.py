import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path

# ======================================================
# CONFIGURAÇÕES
# ======================================================

BASE_DIR = Path(__file__).resolve().parent
arquivo = BASE_DIR / "ravex.xlsx"

RAIO_TERRA = 6371000

# regra operacional
LIMITE_OK = 40         # até 50m = correto
LIMITE_ALERTA = 50    # 51 até 150m = alerta
LIMITE_ERRO = 100      # acima disso = erro

# para identificar ponto recorrente
CASAS_ARREDONDAMENTO = 5

print("==============================================")
print("VALIDAÇÃO INTELIGENTE DE COORDENADAS")
print("ROADNET x ENTREGA REAL")
print("==============================================\n")

# ======================================================
# FUNÇÃO HAVERSINE
# ======================================================

def distancia_metros(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(
        radians,
        [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return RAIO_TERRA * c


# ======================================================
# LEITURA
# ======================================================

if not arquivo.exists():
    raise FileNotFoundError(
        f"Arquivo não encontrado: {arquivo}"
    )

print("Lendo arquivo...\n")

df = pd.read_excel(
    arquivo,
    engine="openpyxl"
)

print(f"Total de linhas: {len(df)}")
print()

# ======================================================
# COLUNAS
# ======================================================

COL_CLIENTE = "Código do cliente"
COL_NOME = "Cliente"
COL_PLACA = "Placa"

COL_LAT_REAL = "Latitude Realizada"
COL_LON_REAL = "Longitude Realizada"

COL_LAT_REF = "Latitude Referência"
COL_LON_REF = "Longitude Referência"

# ======================================================
# TRATAMENTO DAS COORDENADAS
# ======================================================

cols_coord = [
    COL_LAT_REAL,
    COL_LON_REAL,
    COL_LAT_REF,
    COL_LON_REF
]

for col in cols_coord:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .replace("nan", np.nan)
    )

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna(
    subset=[
        COL_LAT_REAL,
        COL_LON_REAL
    ]
).copy()

print(f"Linhas válidas após limpeza: {len(df)}\n")

# ======================================================
# DISTÂNCIA ENTRE ENTREGA E REFERÊNCIA
# ======================================================

print("Calculando distância entre entrega e referência...\n")

df["DISTANCIA_METROS"] = df.apply(
    lambda r: distancia_metros(
        r[COL_LAT_REAL],
        r[COL_LON_REAL],
        r[COL_LAT_REF],
        r[COL_LON_REF]
    )
    if pd.notna(r[COL_LAT_REF]) and pd.notna(r[COL_LON_REF])
    else np.nan,
    axis=1
)

# ======================================================
# STATUS INDIVIDUAL DA ENTREGA
# ======================================================

def classificar_entrega(d):
    if pd.isna(d):
        return "SEM REFERÊNCIA"

    if d <= LIMITE_OK:
        return "OK"

    elif d <= LIMITE_ALERTA:
        return "ALERTA"

    return "ERRO"


df["STATUS_ENTREGA"] = df[
    "DISTANCIA_METROS"
].apply(classificar_entrega)

# ======================================================
# IDENTIFICAR COORDENADA MAIS RECORRENTE
# ======================================================

print("Calculando coordenada mais frequente...\n")

df["LAT_REAL_ARRED"] = df[
    COL_LAT_REAL
].round(CASAS_ARREDONDAMENTO)

df["LON_REAL_ARRED"] = df[
    COL_LON_REAL
].round(CASAS_ARREDONDAMENTO)

frequencia = (
    df.groupby(
        [
            COL_CLIENTE,
            COL_NOME,
            "LAT_REAL_ARRED",
            "LON_REAL_ARRED"
        ],
        as_index=False
    )
    .size()
    .rename(
        columns={
            "size": "QTD_PONTO"
        }
    )
)

coord_principal = (
    frequencia
    .sort_values(
        by=[
            COL_CLIENTE,
            "QTD_PONTO"
        ],
        ascending=[
            True,
            False
        ]
    )
    .groupby(
        COL_CLIENTE,
        as_index=False
    )
    .first()
)

# ======================================================
# RESUMO POR CLIENTE
# ======================================================

print("Gerando resumo inteligente por cliente...\n")

resumo_cliente = (
    df.groupby(
        [COL_CLIENTE, COL_NOME],
        as_index=False
    )
    .agg(
        TOTAL_ENTREGAS=(COL_CLIENTE, "count"),
        QTDE_OK=("STATUS_ENTREGA", lambda x: (x == "OK").sum()),
        QTDE_ALERTA=("STATUS_ENTREGA", lambda x: (x == "ALERTA").sum()),
        QTDE_ERRO=("STATUS_ENTREGA", lambda x: (x == "ERRO").sum()),
        DISTANCIA_MEDIA=("DISTANCIA_METROS", "mean"),
        DISTANCIA_MAXIMA=("DISTANCIA_METROS", "max")
    )
)

resumo_cliente["PERCENTUAL_ERRO"] = (
    resumo_cliente["QTDE_ERRO"]
    / resumo_cliente["TOTAL_ENTREGAS"]
    * 100
).round(2)

# ======================================================
# JUNÇÃO
# ======================================================

resultado = resumo_cliente.merge(
    coord_principal,
    how="left",
    on=[
        COL_CLIENTE,
        COL_NOME
    ]
)

# ======================================================
# CONFIANÇA DA COORDENADA
# ======================================================

resultado["CONFIANCA_COORDENADA_%"] = (
    resultado["QTD_PONTO"]
    / resultado["TOTAL_ENTREGAS"]
    * 100
).round(2)

# ======================================================
# NECESSITA REVISÃO
# ======================================================

def precisa_revisao(row):
    """
    REGRA:

    Se mais da metade das entregas
    estiver fora do raio aceitável,
    provavelmente o cadastro está errado
    """

    if row["PERCENTUAL_ERRO"] >= 50:
        return "🚨 REVISAR CADASTRO"

    if row["CONFIANCA_COORDENADA_%"] < 40:
        return "⚠️ BAIXA CONFIANÇA"

    if row["QTDE_OK"] >= row["QTDE_ERRO"]:
        return "✅ REFERÊNCIA PROVAVELMENTE CORRETA"

    return "⚠️ REVISAR"


resultado["STATUS_FINAL"] = resultado.apply(
    precisa_revisao,
    axis=1
)

# ======================================================
# ORGANIZAÇÃO FINAL
# ======================================================

resultado = resultado.rename(
    columns={
        "LAT_REAL_ARRED": "LATITUDE_CORRETA_PROVAVEL",
        "LON_REAL_ARRED": "LONGITUDE_CORRETA_PROVAVEL"
    }
)

resultado_final = resultado[
    [
        COL_CLIENTE,
        COL_NOME,
        "TOTAL_ENTREGAS",
        "QTDE_OK",
        "QTDE_ALERTA",
        "QTDE_ERRO",
        "PERCENTUAL_ERRO",
        "LATITUDE_CORRETA_PROVAVEL",
        "LONGITUDE_CORRETA_PROVAVEL",
        "QTD_PONTO",
        "CONFIANCA_COORDENADA_%",
        "DISTANCIA_MEDIA",
        "DISTANCIA_MAXIMA",
        "STATUS_FINAL"
    ]
]

# ======================================================
# EXPORTAÇÃO
# ======================================================

arquivo_saida_1 = BASE_DIR / "detalhe_validacao_gps.xlsx"
arquivo_saida_2 = BASE_DIR / "resumo_inteligente_clientes.xlsx"

df.to_excel(
    arquivo_saida_1,
    index=False
)

resultado_final.to_excel(
    arquivo_saida_2,
    index=False
)

# ======================================================
# FINAL
# ======================================================

print("==============================================")
print("PROCESSO FINALIZADO COM SUCESSO")
print("==============================================\n")

print("Arquivos gerados:")
print(f"📄 {arquivo_saida_1}")
print(f"📍 {arquivo_saida_2}")
print()

print("Resumo final:")
print(
    resultado_final["STATUS_FINAL"]
    .value_counts()
)
print()

print("TOP clientes:")
print(
    resultado_final.head(20)
)