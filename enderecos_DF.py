import pandas as pd
import requests
import time
import re

# =====================================================
# CONFIGURAÇÕES
# =====================================================

API_KEY = "AIzaSyBVPfEGtY1hwhHzjPaPuF3dxNpUU46CNgo"

ARQUIVO_ENTRADA = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto_DF\receita.xlsx"
ARQUIVO_SAIDA = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto_DF\clientes_google_geocodificados.xlsx"
ARQUIVO_ERROS = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto_DF\enderecos_nao_localizados_google.xlsx"

# =====================================================
# DICIONÁRIO OFICIAL DE SIGLAS DF
# =====================================================

SIGLAS_DF = {
    # Superquadras / Comércio Local
    "SHCN": "SUPERQUADRA NORTE COMERCIO LOCAL",
    "SHCS": "SUPERQUADRA SUL COMERCIO LOCAL",
    "SHCGN": "SUPERQUADRA NORTE",
    "SHCGS": "SUPERQUADRA SUL",

    # Hotel / Comercial
    "SHN": "SETOR HOTELEIRO NORTE",
    "SHS": "SETOR HOTELEIRO SUL",
    "SCN": "SETOR COMERCIAL NORTE",
    "SCS": "SETOR COMERCIAL SUL",
    "SDN": "SETOR DE DIVERSOES NORTE",
    "SDS": "SETOR DE DIVERSOES SUL",

    # Habitação
    "SHIN": "SETOR DE HABITACOES INDIVIDUAIS NORTE",
    "SHIS": "SETOR DE HABITACOES INDIVIDUAIS SUL",

    # Clubes / Esportes
    "SCES": "SETOR DE CLUBES ESPORTIVOS SUL",
    "SCEN": "SETOR DE CLUBES ESPORTIVOS NORTE",

    # Rádio / TV
    "SRTVN": "SETOR DE RADIO E TV NORTE",
    "SRTVS": "SETOR DE RADIO E TV SUL",

    # Industrial
    "SIA": "SETOR DE INDUSTRIA E ABASTECIMENTO",
    "SIG": "SETOR DE INDUSTRIAS GRAFICAS",
    "SOF": "SETOR DE OFICINAS",
    "SAAN": "SETOR DE ARMAZENAGEM E ABASTECIMENTO NORTE",
    "SAUS": "SETOR DE AUTARQUIAS SUL",
    "SAUN": "SETOR DE AUTARQUIAS NORTE",
    "SIBS": "SETOR DE INDUSTRIA BERNARDO SAYAO",
    "SCIA": "SETOR COMPLEMENTAR DE INDUSTRIA E ABASTECIMENTO",

    # Bancário
    "SBN": "SETOR BANCARIO NORTE",
    "SBS": "SETOR BANCARIO SUL",

    # Outros
    "SMDB": "SETOR DE MANSOES DOM BOSCO",
    "SMAS": "SETOR DE MULTIPLAS ATIVIDADES SUL",
    "SMAN": "SETOR DE MULTIPLAS ATIVIDADES NORTE",
    "AOS": "AREA OCTOGONAL SUL",
    "CEASA": "CENTRAIS DE ABASTECIMENTO DE BRASILIA",

    # Ceilândia / Taguatinga / Guará
    "QNM": "QUADRA NORTE M",
    "QNN": "QUADRA NORTE N",
    "QNL": "QUADRA NORTE L",
    "QNP": "QUADRA NORTE P",
    "QNO": "QUADRA NORTE O",
    "QNR": "QUADRA NORTE R",
    "QSA": "QUADRA SUL A",
    "QSD": "QUADRA SUL D",
    "QSC": "QUADRA SUL C",
    "QSE": "QUADRA SUL E",
    "QSB": "QUADRA SUL B",
    "QS": "QUADRA SUL",
    "QE": "QUADRA ESPECIAL",
    "QI": "QUADRA INTERNA",
    "QR": "QUADRA RESIDENCIAL",

    # Entrequadras
    "EQ": "ENTREQUADRA",
    "EQNM": "ENTREQUADRA NORTE M",
    "EQNL": "ENTREQUADRA NORTE L",
    "EQNP": "ENTREQUADRA NORTE P",
    "EQNO": "ENTREQUADRA NORTE O",
}

# =====================================================
# LIMPEZA DE TEXTO
# =====================================================

def limpar_texto(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    texto = re.sub(r"\s+", " ", texto)
    texto = texto.replace(".", "")
    texto = texto.replace("(", "")
    texto = texto.replace(")", "")
    texto = texto.replace("/", " ")

    return texto


# =====================================================
# PADRONIZAÇÃO DE ENDEREÇO
# =====================================================

def traduzir_siglas(endereco):
    endereco = limpar_texto(endereco)

    for sigla, nome in sorted(SIGLAS_DF.items(), key=lambda x: len(x[0]), reverse=True):
        endereco = re.sub(rf"\b{sigla}\b", nome, endereco)

    return endereco


def montar_tentativas(endereco_original):
    base = traduzir_siglas(endereco_original)

    tentativas = [
        f"{base}, Brasília, DF, Brasil",
        f"{base}, Distrito Federal, Brasil",
        f"{base}, Brasília",
        base
    ]

    return tentativas


# =====================================================
# GOOGLE GEOCODING API
# =====================================================

def geocodificar_google(endereco):
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": endereco,
        "key": API_KEY,
        "region": "br",
        "language": "pt-BR"
    }

    response = requests.get(url, params=params)
    dados = response.json()

    if dados["status"] == "OK":
        resultado = dados["results"][0]

        lat = resultado["geometry"]["location"]["lat"]
        lng = resultado["geometry"]["location"]["lng"]
        endereco_encontrado = resultado["formatted_address"]

        return lat, lng, endereco_encontrado, "LOCALIZADO"

    else:
        return None, None, None, dados["status"]


# =====================================================
# LEITURA DA PLANILHA
# =====================================================

print("Lendo planilha...")

df = pd.read_excel(ARQUIVO_ENTRADA)

df["ENDERECO_BASE"] = (
    df["LOGRADOURO RECEITA FEDERAL"].fillna("").astype(str)
    + ", "
    + df["BAIRRO RECEITA FEDERAL"].fillna("").astype(str)
)

# =====================================================
# RESULTADOS
# =====================================================

latitudes = []
longitudes = []
status = []
melhor_endereco = []
motivo_falha = []
tentativa_usada = []

erros = []

# =====================================================
# PROCESSAMENTO
# =====================================================

print("Iniciando geocodificação profissional com Google API...")

for i, endereco in enumerate(df["ENDERECO_BASE"], start=1):
    encontrado = False
    tentativas = montar_tentativas(endereco)

    print(f"\n{i} - Original: {endereco}")

    for tentativa in tentativas:
        try:
            print(f"→ Tentando: {tentativa}")

            lat, lng, endereco_ok, status_google = geocodificar_google(tentativa)

            if status_google == "LOCALIZADO":
                latitudes.append(lat)
                longitudes.append(lng)
                status.append("LOCALIZADO")
                melhor_endereco.append(endereco_ok)
                motivo_falha.append("")
                tentativa_usada.append(tentativa)

                encontrado = True

                print(f"✓ Encontrado: {endereco_ok}")
                break

            time.sleep(0.2)

        except Exception as erro:
            print(f"Erro: {erro}")

    if not encontrado:
        latitudes.append(None)
        longitudes.append(None)
        status.append("NÃO ENCONTRADO")
        melhor_endereco.append(None)
        tentativa_usada.append(None)

        motivo = "Google Maps não encontrou nenhuma tentativa"

        motivo_falha.append(motivo)

        erros.append({
            "CODIGO CLIENTE": df.loc[i - 1, "CODIGO CLIENTE"],
            "CLIENTE": df.loc[i - 1, "NOME RECEITA FEDERAL"],
            "ENDERECO ORIGINAL": endereco,
            "TENTATIVAS_REALIZADAS": " | ".join(tentativas),
            "MOTIVO": motivo
        })

        print("✗ Não localizado")

# =====================================================
# SALVAR RESULTADO PRINCIPAL
# =====================================================

df["LATITUDE"] = latitudes
df["LONGITUDE"] = longitudes
df["STATUS"] = status
df["ENDERECO_ENCONTRADO"] = melhor_endereco
df["TENTATIVA_UTILIZADA"] = tentativa_usada
df["MOTIVO_FALHA"] = motivo_falha

df.to_excel(
    ARQUIVO_SAIDA,
    index=False,
    engine="openpyxl"
)

# =====================================================
# SALVAR ARQUIVO DE ERROS
# =====================================================

if erros:
    df_erros = pd.DataFrame(erros)

    df_erros.to_excel(
        ARQUIVO_ERROS,
        index=False,
        engine="openpyxl"
    )

    print("\nArquivo de erros salvo em:")
    print(ARQUIVO_ERROS)

print("\nProcesso finalizado com sucesso.")
print("Arquivo principal salvo em:")
print(ARQUIVO_SAIDA)