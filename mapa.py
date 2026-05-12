import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from pathlib import Path

arquivo_kg_cidade = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\kg_por_cidade_2026-02.xlsx"
col_cidade = "Cidade"
col_peso = "Peso_Previsto_Cidade"

df = pd.read_excel(arquivo_kg_cidade)
df[col_cidade] = df[col_cidade].astype(str).str.strip()

cache_file = Path(arquivo_kg_cidade).with_name("geocode_cache_cidades.csv")
if cache_file.exists():
    cache = pd.read_csv(cache_file)
else:
    cache = pd.DataFrame(columns=[col_cidade, "lat", "lon", "display_name"])
cache[col_cidade] = cache[col_cidade].astype(str)

geo = Nominatim(user_agent="martminas_mapa")
geocode = RateLimiter(geo.geocode, min_delay_seconds=1)

new_rows = []
lats, lons = [], []

for cidade in df[col_cidade]:
    hit = cache[cache[col_cidade].str.lower() == str(cidade).lower()]
    if not hit.empty:
        lats.append(float(hit.iloc[0]["lat"]))
        lons.append(float(hit.iloc[0]["lon"]))
        continue

    loc = geocode(f"{cidade}, Minas Gerais, Brasil") or geocode(f"{cidade}, Brasil")
    if loc is not None:
        lat, lon = loc.latitude, loc.longitude
        new_rows.append({col_cidade: cidade, "lat": lat, "lon": lon, "display_name": loc.address})
    else:
        lat, lon = None, None

    lats.append(lat)
    lons.append(lon)

df["lat"] = lats
df["lon"] = lons

if new_rows:
    cache = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True)
    cache.drop_duplicates(subset=[col_cidade], keep="first", inplace=True)
    cache.to_csv(cache_file, index=False)

dfm = df.dropna(subset=["lat", "lon"]).copy()
if dfm.empty:
    raise SystemExit("Nenhuma cidade foi geocodificada. Verifique nomes das cidades ou conexão com internet.")

center = [dfm["lat"].mean(), dfm["lon"].mean()]
m = folium.Map(location=center, zoom_start=6, tiles="CartoDB positron")
cluster = MarkerCluster().add_to(m)

peso_max = float(dfm[col_peso].max()) if len(dfm) else 1.0

for _, r in dfm.iterrows():
    cidade = r[col_cidade]
    peso = float(r[col_peso])
    lat = float(r["lat"])
    lon = float(r["lon"])

    radius = 6 + 24 * (peso / peso_max)

    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color="#1f77b4",
        fill=True,
        fill_color="#1f77b4",
        fill_opacity=0.6,
        popup=f"{cidade}<br>Peso previsto: {peso:,.0f} kg",
    ).add_to(cluster)

saida_html = Path(arquivo_kg_cidade).with_name("mapa_kg_por_cidade.html")
m.save(saida_html)

print(f"OK -> {saida_html}")
print(f"Cache -> {cache_file}")