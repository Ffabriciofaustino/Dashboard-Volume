import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
import os

# ===============================
# CONFIGURAÇÕES
# ===============================
arquivo = r"ravex.xlsx"

RAIO_TERRA = 6371000  # metros
LIMITE_OK = 50        # metros
LIMITE_ALERTA = 300  # metros

# ===============================
# FUNÇÃO HAVERSINE
# ===============================
def distancia_metros(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return RAIO_TERRA * c

# ===============================
# VALIDAÇÃO DO ARQUIVO
# ===============================
if not os.path.exists(arquivo):
    raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

# ===============================
# LEITURA DO EXCEL
# ===============================
df = pd.read_excel(arquivo, engine="openpyxl")

# ===============================
# TRATAMENTO DAS COORDENADAS
# ===============================
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
# CLASSIFICAÇÃO DO GPS
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
# RESUMO POR PLACA
# ===============================
resumo_placa = (
    df.groupby("Placa")
      .agg(
          Total_Entregas=("Placa", "count"),
          Qtde_OK=("Status_GPS", lambda x: (x == "OK").sum()),
          Qtde_Alerta=("Status_GPS", lambda x: (x == "ALERTA").sum()),
          Qtde_Erro=("Status_GPS", lambda x: (x == "ERRO").sum()),
          Distancia_Media=("Distancia_metros", "mean"),
          Distancia_Maxima=("Distancia_metros", "max")
      )
      .reset_index()
)

resumo_placa["Taxa_Erro_%"] = (
    resumo_placa["Qtde_Erro"] / resumo_placa["Total_Entregas"] * 100
).round(2)

# ===============================
# ✅ RESUMO POR CLIENTE (CÓDIGO + NOME)
# ===============================
resumo_cliente = (
    df.groupby(["Código do cliente", "Cliente"])
      .agg(
          Total_Entregas=("Cliente", "count"),
          Qtde_OK=("Status_GPS", lambda x: (x == "OK").sum()),
          Qtde_Alerta=("Status_GPS", lambda x: (x == "ALERTA").sum()),
          Qtde_Erro=("Status_GPS", lambda x: (x == "ERRO").sum()),
          Distancia_Media=("Distancia_metros", "mean"),
          Distancia_Maxima=("Distancia_metros", "max")
      )
      .reset_index()
)

resumo_cliente["Taxa_Erro_%"] = (
    resumo_cliente["Qtde_Erro"] / resumo_cliente["Total_Entregas"] * 100
).round(2)

# ===============================
# EXPORTAÇÃO DOS RESULTADOS
# ===============================
df.to_excel("detalhe_validacao_gps.xlsx", index=False)
resumo_placa.to_excel("resumo_placas_gps.xlsx", index=False)
resumo_cliente.to_excel("resumo_clientes_gps.xlsx", index=False)

print("✅ Projeto finalizado com sucesso!")
print("📄 detalhe_validacao_gps.xlsx")
print("🚚 resumo_placas_gps.xlsx")
print("🏢 resumo_clientes_gps.xlsx")