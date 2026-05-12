import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import re

# =====================================================
# ARQUIVOS
# =====================================================

ARQUIVO_ENTRADA = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto_MG\bh.xlsx"
ARQUIVO_SAIDA = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto_MG\clientes_validados.xlsx"
ARQUIVO_ERROS = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\Projeto_MG\clientes_com_divergencia.xlsx"

# =====================================================
# GEOCODIFICADOR (SEM API)
# =====================================================

geolocator = Nominatim(user_agent="validacao_clientes_mg")

# =====================================================
# LIMPEZA DE TEXTO
# =====================================================

def limpar_texto(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    # remove espaços duplicados
    texto = re.sub(r"\s+", " ", texto)

    # remove pontos desnecessários
    texto = texto.replace(".", "")

    return texto


# =====================================================
# CONVERTER LAT/LONG
# (pois vem com vírgula)
# =====================================================

def converter_coordenada(valor):
    if pd.isna(valor):
        return None

    valor = str(valor).replace(",", ".").strip()

    try:
        return float(valor)
    except:
        return None


# =====================================================
# VALIDAR ENDEREÇOS RUINS
# =====================================================

def endereco_ruim(endereco):
    endereco = str(endereco).upper()

    termos_ruins = [
        "R A",
        "R B",
        "R C",
        "R D",
        "S/N",
        "SN",
        "SEM NUMERO",
        "SEM NÚMERO",
        "RUA A",
        "RUA B",
        "RUA C",
        "RUA D"
    ]

    for termo in termos_ruins:
        if termo in endereco:
            return True

    return False


# =====================================================
# CLASSIFICAÇÃO POR DISTÂNCIA
# =====================================================

def classificar_distancia(distancia_metros):
    if distancia_metros is None:
        return "NÃO LOCALIZADO", 0

    if distancia_metros <= 300:
        return "CORRETO", 100

    elif distancia_metros <= 1000:
        return "ACEITÁVEL", 80

    elif distancia_metros <= 3000:
        return "SUSPEITO", 50

    else:
        return "DIVERGENTE", 0


# =====================================================
# GEOCODIFICAR
# =====================================================

def buscar_coordenadas(endereco):
    try:
        location = geolocator.geocode(
            endereco,
            timeout=15,
            exactly_one=True
        )

        if location:
            return (
                location.latitude,
                location.longitude,
                location.address
            )

        return None, None, None

    except Exception as erro:
        print(f"Erro ao geocodificar: {erro}")
        return None, None, None


# =====================================================
# LEITURA DA PLANILHA
# =====================================================

print("Lendo planilha...")

df = pd.read_excel(ARQUIVO_ENTRADA)

# =====================================================
# MONTAR ENDEREÇO COMPLETO (CORRIGIDO)
# =====================================================
# IMPORTANTE:
# NÃO usar Província_ aqui
# usar:
# Endereço + Cidade + Estado + CEP + Brasil

df["ENDERECO_COMPLETO"] = (
    df["Endereço_"].fillna("").astype(str).str.strip() + ", " +
    df["Cidade_"].fillna("").astype(str).str.strip() + ", " +
    df["Estado_"].fillna("").astype(str).str.strip() + ", " +
    df["CEP_"].fillna("").astype(str).str.strip() + ", Brasil"
)

# =====================================================
# LISTAS DE RESULTADO
# =====================================================

lat_encontrada = []
long_encontrada = []
endereco_encontrado = []
distancia_lista = []
status_lista = []
score_lista = []

erros = []

# =====================================================
# PROCESSAMENTO
# =====================================================

print("Iniciando validação de coordenadas...")

for i, row in df.iterrows():
    cliente = row["Descrição_"]
    endereco = limpar_texto(row["ENDERECO_COMPLETO"])

    print(f"\n{i+1} - Cliente: {cliente}")
    print(f"Endereço: {endereco}")

    # coordenadas atuais
    lat_atual = converter_coordenada(row["Latitude_"])
    long_atual = converter_coordenada(row["Longitude_"])

    # verificar endereço ruim
    if endereco_ruim(endereco):
        print("Endereço ruim detectado -> revisão manual")

        nova_lat = None
        nova_long = None
        endereco_ok = None

        distancia = None
        status = "REVISÃO MANUAL"
        score = 0

    else:
        # busca nova coordenada
        nova_lat, nova_long, endereco_ok = buscar_coordenadas(endereco)

        # comparação correta usando is not None
        if (
            lat_atual is not None and
            long_atual is not None and
            nova_lat is not None and
            nova_long is not None
        ):
            distancia = geodesic(
                (lat_atual, long_atual),
                (nova_lat, nova_long)
            ).meters

            status, score = classificar_distancia(distancia)

        else:
            distancia = None
            status = "NÃO LOCALIZADO"
            score = 0

    lat_encontrada.append(nova_lat)
    long_encontrada.append(nova_long)
    endereco_encontrado.append(endereco_ok)
    distancia_lista.append(distancia)
    status_lista.append(status)
    score_lista.append(score)

    print(f"Status: {status}")

    if status in [
        "SUSPEITO",
        "DIVERGENTE",
        "NÃO LOCALIZADO",
        "REVISÃO MANUAL"
    ]:
        erros.append({
            "ID_CLIENTE": row["ID_do_cliente_"],
            "CLIENTE": cliente,
            "ENDERECO_ORIGINAL": endereco,
            "LAT_ATUAL": lat_atual,
            "LONG_ATUAL": long_atual,
            "LAT_NOVA": nova_lat,
            "LONG_NOVA": nova_long,
            "DISTANCIA_METROS": distancia,
            "STATUS": status,
            "SCORE": score
        })

    # evitar bloqueio do Nominatim
    time.sleep(1)

# =====================================================
# SALVAR RESULTADO PRINCIPAL
# =====================================================

df["LATITUDE_NOVA"] = lat_encontrada
df["LONGITUDE_NOVA"] = long_encontrada
df["ENDERECO_ENCONTRADO"] = endereco_encontrado
df["DISTANCIA_METROS"] = distancia_lista
df["STATUS_VALIDACAO"] = status_lista
df["SCORE_CONFIANCA"] = score_lista

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

    print("\nArquivo de divergências salvo em:")
    print(ARQUIVO_ERROS)

# =====================================================
# FINAL
# =====================================================

print("\nProcesso finalizado com sucesso.")
print("Arquivo principal salvo em:")
print(ARQUIVO_SAIDA)