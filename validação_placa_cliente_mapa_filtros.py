import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
import os
import folium
from folium import FeatureGroup
from folium.plugins import Search

# ===============================
# CONFIGURAÇÕES
# ===============================
arquivo = r"GEOCODIFICACAO.xlsx"

RAIO_TERRA = 6371000
LIMITE_OK = 50
LIMITE_ALERTA = 150

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
    ), axis=1
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
# MAPA ÚNICO INTERATIVO
# ===============================
mapa = folium.Map(
    location=[
        df["Latitude Referência"].mean(),
        df["Longitude Referência"].mean()
    ],
    zoom_start=11,
    tiles="OpenStreetMap"
)

# Camadas por status
camada_ok = FeatureGroup(name="✅ OK")
camada_alerta = FeatureGroup(name="⚠️ ALERTA")
camada_erro = FeatureGroup(name="❌ ERRO")

camada_busca = FeatureGroup(name="🔍 Busca")

cores = {
    "OK": "green",
    "ALERTA": "orange",
    "ERRO": "red"
}

for _, r in df.iterrows():
    status = r["Status_GPS"]
    cor = cores[status]

    popup = f"""
    <b>Cliente:</b> {r['Cliente']}<br>
    <b>Código do cliente:</b> {r['Código do cliente']}<br>
    <b>Placa:</b> {r['Placa']}<br>
    <b>Distância:</b> {round(r['Distancia_metros'],2)} m<br>
    <b>Status:</b> {status}
    """

    linha = folium.PolyLine(
        [
            (r["Latitude Referência"], r["Longitude Referência"]),
            (r["Latitude Realizada"], r["Longitude Realizada"])
        ],
        color=cor,
        weight=2,
        opacity=0.7
    )

    ponto_ref = folium.CircleMarker(
        (r["Latitude Referência"], r["Longitude Referência"]),
        radius=4,
        color="blue",
        fill=True
    )

    ponto_real = folium.CircleMarker(
        (r["Latitude Realizada"], r["Longitude Realizada"]),
        radius=5,
        color=cor,
        fill=True,
        popup=popup,
        tooltip=f"{r['Cliente']} | {r['Placa']}"
    )

    camada = camada_ok if status == "OK" else camada_alerta if status == "ALERTA" else camada_erro

    linha.add_to(camada)
    ponto_ref.add_to(camada)
    ponto_real.add_to(camada)

    # Camada usada para busca
    folium.Marker(
        (r["Latitude Realizada"], r["Longitude Realizada"]),
        tooltip=f"{r['Cliente']} | {r['Placa']}"
    ).add_to(camada_busca)

# Adiciona camadas
camada_ok.add_to(mapa)
camada_alerta.add_to(mapa)
camada_erro.add_to(mapa)
camada_busca.add_to(mapa)

# Filtros
folium.LayerControl(collapsed=False).add_to(mapa)

Search(
    layer=camada_busca,
    search_label="tooltip",
    placeholder="Buscar Cliente ou Placa",
    collapsed=False
).add_to(mapa)

# ===============================
# SALVA MAPA
# ===============================
mapa.save("mapa_validacao_interativo.html")

print("✅ PROCESSO FINALIZADO")
print("🗺️ Arquivo gerado: mapa_validacao_interativo.html")