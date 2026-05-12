
import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2

# ===============================
# CONFIGURAÇÕES
# ===============================
arquivo = r"GEOCODIFICACAO.xlsx"
RAIO_TERRA = 6371000  # metros
LIMITE_OK = 50        # metros
LIMITE_ALERTA = 150  # metros

# ===============================
# FUNÇÃO HAVERSINE
# ===============================
def distancia_metros(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return RAIO_TERRA * c

# ===============================
# LEITURA DOS DADOS
# ===============================

df = pd.read_excel(arquivo, engine="openpyxl")
# Ajuste vírgula → ponto
cols_latlon = [
    "Latitude Realizada", "Longitude Realizada",
    "Latitude Referência", "Longitude Referência"
]

for c in cols_latlon:
    df[c] = (
        df[c]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .replace("nan", np.nan)
        .astype(float)
    )

df = df.dropna(subset=cols_latlon)

# ===============================
# CÁLCULO DA DISTÂNCIA
# ===============================
df["Distancia_metros"] = df.apply(
    lambda r: distancia_metros(
        r["Latitude Realizada"],
        r["Longitude Realizada"],
        r["Latitude Referência"],
        r["Longitude Referência"]
    ),
    axis=1
)

# ===============================
# CLASSIFICAÇÃO
# ===============================
def classificar(d):
    if d <= LIMITE_OK:
        return "OK"
    elif d <= LIMITE_ALERTA:
        return "ALERTA"
    else:
        return "ERRO"

df["Status_GPS"] = df["Distancia_metros"].apply(classificar)

# ===============================
# RESUMO POR MOTORISTA
# ===============================
resumo_motorista = (
    df.groupby("Placa")
      .agg(
          Total_Entregas=("Placa", "count"),
          Erros=("Status_GPS", lambda x: (x == "ERRO").sum()),
          Distancia_Media=("Distancia_metros", "mean"),
          Distancia_Maxima=("Distancia_metros", "max")
      )
      .reset_index()
)

resumo_motorista["Taxa_Erro_%"] = (
    resumo_motorista["Erros"] / resumo_motorista["Total_Entregas"] * 100
).round(2)

# ===============================
# EXPORTAÇÃO
# ===============================
df.to_excel("detalhe_validacao_gps.xlsx", index=False)
resumo_motorista.to_excel("resumo_motoristas_gps.xlsx", index=False)

print("✅ Projeto finalizado")
print("➡ detalhe_validacao_gps.xlsx")
