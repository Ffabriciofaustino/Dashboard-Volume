import pandas as pd
from geopy.geocoders import Nominatim
import time

# =====================================
# CONFIGURAÇÕES
# =====================================

ARQUIVO_ENTRADA = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto_DF\receita.xlsx"
ARQUIVO_SAIDA = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto_DF\clientes_geocodificados.xlsx"

# Geocodificador OpenStreetMap
geolocator = Nominatim(user_agent="geocodificacao_df")

# =====================================
# LER PLANILHA
# =====================================

print("Lendo planilha...")

df = pd.read_excel(ARQUIVO_ENTRADA)

# =====================================
# CRIAR ENDEREÇO COMPLETO
# =====================================

print("Montando endereço completo...")

df["ENDERECO_COMPLETO"] = (
    df["LOGRADOURO RECEITA FEDERAL"].fillna("").astype(str) + ", " +
    df["BAIRRO RECEITA FEDERAL"].fillna("").astype(str) + ", " +
    df["CIDADE"].fillna("").astype(str) + ", " +
    df["UF"].fillna("").astype(str)
)

# =====================================
# LISTAS DE RESULTADO
# =====================================

latitudes = []
longitudes = []
enderecos_encontrados = []
status = []

# =====================================
# GEOCODIFICAÇÃO
# =====================================

print("Iniciando geocodificação...")

for i, endereco in enumerate(df["ENDERECO_COMPLETO"], start=1):
    try:
        print(f"Processando {i}: {endereco}")

        location = geolocator.geocode(endereco)

        if location:
            latitudes.append(location.latitude)
            longitudes.append(location.longitude)
            enderecos_encontrados.append(location.address)
            status.append("LOCALIZADO")
        else:
            latitudes.append(None)
            longitudes.append(None)
            enderecos_encontrados.append(None)
            status.append("NÃO ENCONTRADO")

        # evita bloqueio do OpenStreetMap
        time.sleep(1)

    except Exception as erro:
        print(f"Erro no endereço: {endereco}")
        print(erro)

        latitudes.append(None)
        longitudes.append(None)
        enderecos_encontrados.append(None)
        status.append("ERRO NA CONSULTA")

# =====================================
# SALVAR RESULTADO
# =====================================

df["LATITUDE"] = latitudes
df["LONGITUDE"] = longitudes
df["ENDERECO_ENCONTRADO"] = enderecos_encontrados
df["STATUS_GEOCODIFICACAO"] = status

df.to_excel(ARQUIVO_SAIDA, index=False)

print("\nProcesso finalizado com sucesso.")
print(f"Arquivo salvo como: {ARQUIVO_SAIDA}")