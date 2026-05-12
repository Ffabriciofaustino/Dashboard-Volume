import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
import os
import folium
from folium import FeatureGroup
from folium.plugins import MarkerCluster, Search

# ===============================
# CONFIGURAÇÕES
# ===============================
arquivo = r"GEOCODIFICACAO.xlsx"

RAIO_TERRA = 6371000  # metros
LIMITE_OK = 50
LIMITE_ALERTA = 150

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
# LEITURA DO EXCEL
# ===============================
if not os.path.exists(arquivo):
    raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

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
        df[c].astype(str)
              .str.replace(",", ".", regex=False)
              .replace("nan", np.nan)
              .astype(float)
    )

df = df.dropna(subset=cols_latlon)

# ===============================
# DISTÂNCIA E STATUS
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

def classificar(d):
    if d <= LIMITE_OK:
        return "OK"
    elif d <= LIMITE_ALERTA:
        return "ALERTA"
    else:
        return "ERRO"

df["Status_GPS"] = df["Distancia_metros"].apply(classificar)

# ===============================
# EXPORTA EXCEL – DETALHE
# ===============================
df.to_excel("detalhe_validacao_gps.xlsx", index=False)

# ===============================
# EXPORTA EXCEL – RESUMO POR PLACA
# ===============================
resumo_placa = (
    df.groupby("Placa")
      .agg(
          Total_Entregas=("Placa", "count"),
          Qtde_OK=("Status_GPS", lambda x: (x == "OK").sum()),
          Qtde_ALERTA=("Status_GPS", lambda x: (x == "ALERTA").sum()),
          Qtde_ERRO=("Status_GPS", lambda x: (x == "ERRO").sum()),
          Distancia_Media=("Distancia_metros", "mean"),
          Distancia_Maxima=("Distancia_metros", "max")
      )
      .reset_index()
)

resumo_placa.to_excel("resumo_placas_gps.xlsx", index=False)

# ===============================
# EXPORTA EXCEL – RESUMO POR CLIENTE
# ===============================
resumo_cliente = (
    df.groupby(["Código do cliente", "Cliente"])
      .agg(
          Total_Entregas=("Cliente", "count"),
          Qtde_OK=("Status_GPS", lambda x: (x == "OK").sum()),
          Qtde_ALERTA=("Status_GPS", lambda x: (x == "ALERTA").sum()),
          Qtde_ERRO=("Status_GPS", lambda x: (x == "ERRO").sum()),
          Distancia_Media=("Distancia_metros", "mean"),
          Distancia_Maxima=("Distancia_metros", "max")
      )
      .reset_index()
)

resumo_cliente.to_excel("resumo_clientes_gps.xlsx", index=False)

# ===============================
# MAPA ÚNICO OTIMIZADO
# ===============================
mapa = folium.Map(
    location=[
        df["Latitude Referência"].mean(),
        df["Longitude Referência"].mean()
    ],
    zoom_start=11,
    tiles="OpenStreetMap",
    prefer_canvas=True  # MUITO IMPORTANTE (performance)
)

cluster_ok = MarkerCluster(name="✅ OK")
cluster_alerta = MarkerCluster(name="⚠️ ALERTA")
cluster_erro = MarkerCluster(name="❌ ERRO")
cluster_busca = MarkerCluster(name="🔍 Buscar Cliente / Placa")

cores = {"OK": "green", "ALERTA": "orange", "ERRO": "red"}

for _, r in df.iterrows():
    status = r["Status_GPS"]
    cor = cores[status]

    popup = f"""
    <b>Cliente:</b> {r['Cliente']}<br>
    <b>Código:</b> {r['Código do cliente']}<br>
    <b>Placa:</b> {r['Placa']}<br>
    <b>Distância:</b> {round(r['Distancia_metros'], 1)} m<br>
    <b>Status:</b> {status}
    """

    cluster = cluster_ok if status == "OK" else cluster_alerta if status == "ALERTA" else cluster_erro

    folium.Marker(
        (r["Latitude Realizada"], r["Longitude Realizada"]),
        popup=popup,
        tooltip=f"{r['Cliente']} | {r['Placa']}",
        icon=folium.Icon(color=cor, icon="truck", prefix="fa")
    ).add_to(cluster)

    # Linha SOMENTE para ERRO
    if status == "ERRO":
        folium.PolyLine(
            [
                (r["Latitude Referência"], r["Longitude Referência"]),
                (r["Latitude Realizada"], r["Longitude Realizada"])
            ],
            color="red",
            weight=2,
            opacity=0.6
        ).add_to(mapa)

    # Cluster invisível apenas para busca
    folium.Marker(
        (r["Latitude Realizada"], r["Longitude Realizada"]),
        tooltip=f"{r['Cliente']} | {r['Placa']}"
    ).add_to(cluster_busca)

cluster_ok.add_to(mapa)
cluster_alerta.add_to(mapa)
cluster_erro.add_to(mapa)
cluster_busca.add_to(mapa)

folium.LayerControl(collapsed=False).add_to(mapa)

Search(
    layer=cluster_busca,
    search_label="tooltip",
    placeholder="Buscar Cliente ou Placa",
    collapsed=False
).add_to(mapa)

mapa.save("mapa_validacao_interativo.html")

# ===============================
# FINALIZAÇÃO
# ===============================
print("✅ PROCESSO FINALIZADO COM SUCESSO")
print("📄 detalhe_validacao_gps.xlsx")
print("🚚 resumo_placas_gps.xlsx")
print("🏢 resumo_clientes_gps.xlsx")
print("🗺️ mapa_validacao_interativo.html")
