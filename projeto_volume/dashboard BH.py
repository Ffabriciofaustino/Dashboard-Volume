import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import math

# ======================================================
# CONFIG
# ======================================================

st.set_page_config(
    page_title="Dashboard Logístico",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent

arquivo = BASE_DIR / "relatorio_consolidado_grade.xlsx"

# ======================================================
# LOAD
# ======================================================

@st.cache_data
def carregar():
    return pd.read_excel(arquivo)

df = carregar()

df["Data Entrega"] = pd.to_datetime(df["Data Entrega"])

# ======================================================
# 🚛 MAPA DE VEÍCULOS
# ======================================================

capacidade_malha = {

    "BARBACENA": ("3/4", 3500),
    "CONSELHEIRO LAFAIETE": ("3/4", 3500),
    "BARREIRO": ("SEMI-LEVE", 1500),
    "CENTROBH": ("SEMI-LEVE", 1500),
    "CENTROSULBH": ("SEMI-LEVE", 1500),
    "CIDADE NOVA": ("SEMI-LEVE", 1500),
    "CONTAGEM": ("SEMI-LEVE", 1500),
    "DIVINOPOLIS": ("3/4", 3500),
    "ESMERALDAS": ("SEMI-LEVE", 1500),
    "FORMIGA": ("3/4", 3500),
    "GOVERNADOR VALADARES": ("3/4", 3500),
    "IPATINGA": ("3/4", 3500),
    "JOAO MONLEVADE": ("3/4", 3500),
    "JUIZ DE FORA": ("3/4", 3500),
    "LAGOA SANTA": ("SEMI-LEVE", 1500),
    "LAVRAS": ("3/4", 3500),
    "MANHUACU": ("3/4", 3500),
    "MONTES CLAROS": ("3/4", 3500),
    "NORTE": ("SEMI-LEVE", 1500),
    "OURO PRETO": ("SEMI-LEVE", 1500),
    "PAMPULHA": ("SEMI-LEVE", 1500),
    "PE EUSTAQUIO": ("SEMI-LEVE", 1500),
    "REDOR": ("SEMI-LEVE", 1500),
    "SETE LAGOAS": ("SEMI-LEVE", 1500),
    "UBA": ("3/4", 3500),
    "VENDA NOVA BH": ("SEMI-LEVE", 1500),

}

# ======================================================
# CRIAR COLUNAS BASE
# ======================================================

df["TIPO_VEICULO"] = df["MALHA"].map(
    lambda x: capacidade_malha.get(x, ("PADRÃO", 1500))[0]
)

df["CAPACIDADE"] = df["MALHA"].map(
    lambda x: capacidade_malha.get(x, ("PADRÃO", 1500))[1]
)

# ======================================================
# FILTROS
# ======================================================

st.sidebar.title("Filtros")

datas = sorted(df["Data Entrega"].dt.date.unique())

data_sel = st.sidebar.multiselect(
    "Data",
    datas,
    default=datas
)

malhas = sorted(df["MALHA"].dropna().unique())

malha_sel = st.sidebar.multiselect(
    "Malha",
    malhas,
    default=malhas
)

tsps = sorted(df["TSP"].dropna().unique())

tsp_sel = st.sidebar.multiselect(
    "TSP",
    tsps,
    default=tsps
)

# ======================================================
# FILTRO GRADE / ABERTO
# ======================================================

tipo_pedido = st.sidebar.radio(
    "Tipo Pedido",
    ["TODOS", "GRADE", "ABERTO"]
)

# ======================================================
# FILTRO BASE
# ======================================================

df_filtro = df[

    (df["Data Entrega"].dt.date.isin(data_sel)) &
    (df["MALHA"].isin(malha_sel)) &
    (df["TSP"].isin(tsp_sel))

]

# filtro adicional
if tipo_pedido != "TODOS":

    df_filtro = df_filtro[
        df_filtro["TIPO_PEDIDO"] == tipo_pedido
    ]

# ======================================================
# 🚛 CÁLCULO DE FROTA
# ======================================================

df_malha = (

    df_filtro.groupby(
        [
            "MALHA",
            "TIPO_VEICULO",
            "TIPO_PEDIDO"
        ],
        as_index=False
    )

    .agg(
        PESO_TOTAL=("PESO_TOTAL", "sum")
    )

)

df_malha["CAPACIDADE"] = df_malha["MALHA"].map(
    lambda x: capacidade_malha.get(x, ("PADRÃO", 1500))[1]
)

df_malha["QTD_VEICULOS"] = df_malha.apply(

    lambda r: math.ceil(
        r["PESO_TOTAL"] / r["CAPACIDADE"]
    ),

    axis=1
)

df_malha["CAP_TOTAL"] = (
    df_malha["QTD_VEICULOS"] *
    df_malha["CAPACIDADE"]
)

df_malha["EXCESSO_KG"] = (

    df_malha["PESO_TOTAL"] -
    df_malha["CAP_TOTAL"]

).clip(lower=0)

df_malha["STATUS"] = df_malha["EXCESSO_KG"].apply(

    lambda x:
    "🔴 EXCESSO"
    if x > 0
    else "🟢 OK"

)

# ======================================================
# KPIs
# ======================================================

peso_total = df_filtro["PESO_TOTAL"].sum()

peso_grade = df_filtro[
    df_filtro["TIPO_PEDIDO"] == "GRADE"
]["PESO_TOTAL"].sum()

peso_aberto = df_filtro[
    df_filtro["TIPO_PEDIDO"] == "ABERTO"
]["PESO_TOTAL"].sum()

col1, col2, col3 = st.columns(3)

col1.metric(
    "🚚 Peso Total",
    f"{peso_total:,.0f} kg"
)

col2.metric(
    "📦 Grade",
    f"{peso_grade:,.0f} kg",
    f"{(peso_grade/peso_total*100 if peso_total else 0):.1f}%"
)

col3.metric(
    "📭 Aberto",
    f"{peso_aberto:,.0f} kg",
    f"{(peso_aberto/peso_total*100 if peso_total else 0):.1f}%"
)

st.divider()

# ======================================================
# KPIs VEÍCULOS
# ======================================================

total_veiculos = df_malha["QTD_VEICULOS"].sum()

total_excesso = df_malha["EXCESSO_KG"].sum()

col4, col5 = st.columns(2)

col4.metric(
    "🚛 Veículos Necessários",
    total_veiculos
)

col5.metric(
    "🔴 Excesso Total",
    f"{total_excesso:,.0f} kg"
)

# ======================================================
# CAPACIDADE CD
# ======================================================

CAPACIDADE_CD = 60000

carga_total_cd = peso_total

excesso_cd = max(
    carga_total_cd - CAPACIDADE_CD,
    0
)

status_cd = (
    "🔴 ESTOURADO"
    if excesso_cd > 0
    else "🟢 DENTRO"
)

st.divider()

st.subheader("🏭 Capacidade Operacional do CD")

col_cd1, col_cd2, col_cd3 = st.columns(3)

col_cd1.metric(
    "Capacidade CD",
    f"{CAPACIDADE_CD:,.0f} kg"
)

col_cd2.metric(
    "Carga Total",
    f"{carga_total_cd:,.0f} kg"
)

col_cd3.metric(
    "Excesso",
    f"{excesso_cd:,.0f} kg",
    status_cd
)

# ======================================================
# GRÁFICO CD
# ======================================================

fig_cd = go.Figure()

fig_cd.add_trace(

    go.Bar(

        x=["Capacidade", "Carga"],

        y=[
            CAPACIDADE_CD,
            carga_total_cd
        ],

        text=[
            f"{CAPACIDADE_CD:,.0f}",
            f"{carga_total_cd:,.0f}"
        ],

        textposition="auto"
    )

)

fig_cd.update_layout(
    title="Capacidade vs Carga do CD"
)

st.plotly_chart(
    fig_cd,
    width="stretch"
)

# ======================================================
# GRÁFICO FROTA
# ======================================================

fig = px.bar(

    df_malha.sort_values(
        "PESO_TOTAL",
        ascending=False
    ),

    x="MALHA",

    y="PESO_TOTAL",

    color="TIPO_VEICULO",

    text="QTD_VEICULOS",

    hover_data={

        "PESO_TOTAL": ":,.0f",

        "QTD_VEICULOS": True,

        "TIPO_VEICULO": True,

        "CAPACIDADE": ":,.0f",

        "STATUS": True,

        "TIPO_PEDIDO": True
    }
)

fig.update_traces(

    texttemplate=
    "<b>%{text} veículos</b>",

    textposition="outside"
)

fig.update_layout(

    title="🚛 Peso por Malha + Frota Necessária",

    xaxis_title="Malha",

    yaxis_title="Peso Total (KG)",

    height=700
)

st.plotly_chart(
    fig,
    width="stretch"
)

# ======================================================
# SUNBURST
# ======================================================

grafico2 = df_filtro.groupby(

    [
        "MALHA",
        "Cidade",
        "TIPO_PEDIDO"
    ],

    as_index=False

)["PESO_TOTAL"].sum()

fig2 = px.sunburst(

    grafico2,

    path=[
        "MALHA",
        "Cidade",
        "TIPO_PEDIDO"
    ],

    values="PESO_TOTAL"
)

st.plotly_chart(
    fig2,
    width="stretch"
)

# ======================================================
# TABELA FINAL
# ======================================================

st.subheader("📋 Resumo Operacional")

st.dataframe(

    df_malha.sort_values(
        "EXCESSO_KG",
        ascending=False
    ),

    width="stretch"
)