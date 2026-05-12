# =========================================================
# DASHBOARD LOGÍSTICO - STREAMLIT
# COMPARTILHAMENTO LOCAL VIA LINK
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import socket

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Dashboard Logístico",
    layout="wide"
)

st.markdown("""
<style>

.block-container{
    padding-top: 1rem;
}

</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent

arquivo = BASE_DIR / "relatorio_consolidado_grade.xlsx"

# =========================================================
# PEGAR IP DA MÁQUINA
# =========================================================

def pegar_ip():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

    except:

        ip = "127.0.0.1"

    finally:

        s.close()

    return ip

ip_maquina = pegar_ip()

# =========================================================
# LOAD
# =========================================================

@st.cache_data
def carregar():

    df = pd.read_excel(arquivo)

    return df

df = carregar()

# =========================================================
# NORMALIZAR COLUNAS
# =========================================================

df.columns = (
    df.columns
    .astype(str)
    .str.upper()
    .str.strip()
)

# =========================================================
# VALIDAR
# =========================================================

colunas_obrigatorias = [

    "DATA ENTREGA",
    "CIDADE",
    "MALHA",
    "TSP",
    "EMPRESA",
    "TIPO_PEDIDO",
    "EQUIPE VENDA",
    "PESO_TOTAL"

]

faltando = [

    c for c in colunas_obrigatorias
    if c not in df.columns

]

if faltando:

    st.error(f"Colunas não encontradas: {faltando}")

    st.stop()

# =========================================================
# DATA
# =========================================================

df["DATA ENTREGA"] = pd.to_datetime(
    df["DATA ENTREGA"],
    errors="coerce"
)

# =========================================================
# LIMPAR TEXTO
# =========================================================

colunas_texto = [

    "CIDADE",
    "MALHA",
    "TSP",
    "EMPRESA",
    "TIPO_PEDIDO",
    "EQUIPE VENDA"

]

for col in colunas_texto:

    df[col] = (
        df[col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

# =========================================================
# PESO
# =========================================================

df["PESO_TOTAL"] = pd.to_numeric(
    df["PESO_TOTAL"],
    errors="coerce"
).fillna(0)

# =========================================================
# NORMALIZAR TSP
# =========================================================

def normalizar_tsp(nome):

    nome = str(nome).upper().strip()

    if "BH" in nome:
        return "CD BH"

    elif "TRES CORACOES" in nome:
        return "TRES CORACOES"

    elif "UBERLANDIA" in nome:
        return "UBERLANDIA"

    return nome

df["TSP_NORMALIZADO"] = df["TSP"].apply(normalizar_tsp)

# =========================================================
# CONFIG TSP
# =========================================================

config_tsp = {

    "CD BH": {

        "capacidade_cd": 60000,

        "malhas": {

            "BARBACENA": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "CONSELHEIRO LAFAIETE": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "BARREIRO": [("SEMI-LEVE", 1500)],
            "CONTAGEM": [("SEMI-LEVE", 1500)],
            "DIVINOPOLIS": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "FORMIGA": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "IPATINGA": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "JUIZ DE FORA": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "LAVRAS": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "MONTES CLAROS": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "SETE LAGOAS": [("SEMI-LEVE", 1500)],
            "BELO HORIZONTE": [("SEMI-LEVE", 1500)]
        }
    }
}

# =========================================================
# BUSCAR VEÍCULOS
# =========================================================

def buscar_veiculos_permitidos(tsp, malha):

    tsp = normalizar_tsp(tsp)

    malha = str(malha).upper().strip()

    if tsp in config_tsp:

        malhas = config_tsp[tsp]["malhas"]

        if malha in malhas:

            return malhas[malha]

    return [("PADRAO", 1500)]

df["VEICULOS_PERMITIDOS"] = df.apply(

    lambda r: buscar_veiculos_permitidos(
        r["TSP_NORMALIZADO"],
        r["MALHA"]
    ),

    axis=1
)

# =========================================================
# FILTROS
# =========================================================

st.sidebar.title("Filtros")

datas = sorted(
    df["DATA ENTREGA"].dt.date.dropna().unique()
)

data_sel = st.sidebar.multiselect(
    "Data",
    datas,
    default=datas
)

# =========================================================
# FILTRO
# =========================================================

df_filtro = df[
    df["DATA ENTREGA"].dt.date.isin(data_sel)
]

# =========================================================
# AGRUPAMENTO
# =========================================================

df_malha = (

    df_filtro.groupby(
        ["MALHA"],
        as_index=False
    )

    .agg(
        PESO_TOTAL=("PESO_TOTAL", "sum"),
        TSP_NORMALIZADO=("TSP_NORMALIZADO", "first"),
        VEICULOS_PERMITIDOS=("VEICULOS_PERMITIDOS", "first")
    )

)

# =========================================================
# OTIMIZADOR
# =========================================================

def otimizar_veiculo(veiculos_permitidos, peso):

    peso = float(peso)

    melhores = []

    for tipo, capacidade_unitaria in veiculos_permitidos:

        for qtd in range(1, 20):

            capacidade_total = qtd * capacidade_unitaria

            if capacidade_total >= peso:

                ocupacao = (
                    peso / capacidade_total
                ) * 100

                sobra = capacidade_total - peso

                melhores.append({

                    "veiculo": f"{qtd}x {tipo}",
                    "qtd": qtd,
                    "capacidade": capacidade_total,
                    "ocupacao": ocupacao,
                    "sobra": sobra
                })

    if not melhores:

        return (
            "SEM VEICULO",
            0,
            0,
            0
        )

    melhor = sorted(

        melhores,

        key=lambda x: x["sobra"]

    )[0]

    return (

        melhor["veiculo"],
        melhor["qtd"],
        melhor["capacidade"],
        melhor["ocupacao"]

    )

resultado = df_malha.apply(

    lambda r: otimizar_veiculo(
        r["VEICULOS_PERMITIDOS"],
        r["PESO_TOTAL"]
    ),

    axis=1
)

df_malha["VEICULO_ESCALADO"] = resultado.apply(lambda x: x[0])
df_malha["QTD_VEICULOS"] = resultado.apply(lambda x: x[1])
df_malha["CAPACIDADE_TOTAL"] = resultado.apply(lambda x: x[2])
df_malha["OCUPACAO"] = resultado.apply(lambda x: x[3])

# =========================================================
# KPI
# =========================================================

peso_total = df_malha["PESO_TOTAL"].sum()

st.title("📦 Dashboard Logístico")

st.metric(
    "🚚 Peso Total",
    f"{peso_total:,.0f} KG"
)

# =========================================================
# LINK COMPARTILHAMENTO
# =========================================================

st.success(f"""
🌐 LINK PARA COMPARTILHAR:

http://{ip_maquina}:8501
""")

st.info("""
⚠️ Funciona apenas para pessoas na mesma rede/Wi-Fi.
""")

# =========================================================
# GRÁFICO
# =========================================================

fig = px.bar(

    df_malha.sort_values(
        "PESO_TOTAL",
        ascending=False
    ),

    x="MALHA",
    y="PESO_TOTAL",

    text="PESO_TOTAL",

    color="OCUPACAO",

    custom_data=[

        "VEICULO_ESCALADO",
        "QTD_VEICULOS"

    ]
)

fig.update_traces(

    texttemplate=

    "<b>%{x}</b><br>" +
    "%{y:,.0f} KG<br>" +
    "%{customdata[0]}<br>" +
    "%{customdata[1]} veículos",

    textposition="inside"
)

fig.update_layout(

    height=700
)

st.plotly_chart(
    fig,
    width="stretch"
)

# =========================================================
# TABELA
# =========================================================

df_exibir = df_malha.copy()

df_exibir["VEICULOS_PERMITIDOS"] = df_exibir[
    "VEICULOS_PERMITIDOS"
].apply(

    lambda x: ", ".join(
        [f"{v[0]} ({v[1]} KG)" for v in x]
    )

)

st.dataframe(

    df_exibir,

    width="stretch",
    hide_index=True
)