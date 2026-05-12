# =========================================================
# DASHBOARD LOGÍSTICO - STREAMLIT
# dashboard.py
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

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
            "CENTROBH": [("SEMI-LEVE", 1500)],
            "CENTROSULBH": [("SEMI-LEVE", 1500)],
            "CIDADE NOVA": [("SEMI-LEVE", 1500)],
            "CONTAGEM": [("SEMI-LEVE", 1500)],
            "DIVINOPOLIS": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "ESMERALDAS": [("SEMI-LEVE", 1500)],
            "FORMIGA": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "GOVERNADOR VALADARES": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "IPATINGA": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "JOAO MONLEVADE": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "JUIZ DE FORA": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "LAGOA SANTA": [("SEMI-LEVE", 1500), ("SUPER 3/4", 5000)],
            "LAVRAS": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "MANHUACU": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "MONTES CLAROS": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "NORTE": [("SEMI-LEVE", 1500)],
            "OURO PRETO": [("SEMI-LEVE", 1500)],
            "PAMPULHA": [("SEMI-LEVE", 1500)],
            "PE EUSTAQUIO": [("SEMI-LEVE", 1500)],
            "REDOR": [("SEMI-LEVE", 1500)],
            "SETE LAGOAS": [("SEMI-LEVE", 1500)],
            "UBA": [("3/4", 3500), ("SUPER 3/4", 5000)],
            "BELO HORIZONTE": [("SEMI-LEVE", 1500)],
            "VENDA NOVA BH": [("SEMI-LEVE", 1500)]
        }
    },

    "TRES CORACOES": {

        "capacidade_cd": 30000,

        "malhas": {

            "ITAJUBA": [("3/4", 3500)],
            "PASSOS": [("3/4", 3500)],
            "POCOS DE CALDAS": [("3/4", 3500)],
            "POUSO ALEGRE": [("3/4", 3500)],
            "TRES CORACOES": [("3/4", 3500)],
            "VARGINHA": [("3/4", 3500)]

        }
    },

    "UBERLANDIA": {

        "capacidade_cd": 30000,

        "malhas": {

            "ARAXA": [("3/4", 3500)],
            "CAMPINA VERDE": [("3/4", 3500)],
            "ITUIUTABA": [("3/4", 3500)],
            "PATOS DE MINAS": [("3/4", 3500)],
            "PATROCINIO": [("3/4", 3500)],
            "UBERABA": [("3/4", 3500)],
            "UBERLANDIA": [("SEMI-LEVE", 1500), ("3/4", 3500)],
            "UNAI": [("3/4", 3500)]

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

malhas = sorted(
    df["MALHA"].dropna().unique()
)

malha_sel = st.sidebar.multiselect(
    "Malha",
    malhas,
    default=malhas
)

tsps = sorted(
    df["TSP_NORMALIZADO"].dropna().unique()
)

opcao_tsp = st.sidebar.selectbox(
    "Selecionar TSP",
    ["TODOS"] + tsps
)

if opcao_tsp == "TODOS":
    tsp_sel = tsps
else:
    tsp_sel = [opcao_tsp]

equipes = sorted(
    df["EQUIPE VENDA"].dropna().unique()
)

equipe_sel = st.sidebar.multiselect(
    "Equipe Venda",
    equipes,
    default=equipes
)

tipo_pedido = st.sidebar.radio(
    "Tipo Pedido",
    ["TODOS", "GRADE", "ABERTO"]
)

# =========================================================
# FILTRO BASE
# =========================================================

df_filtro = df[

    (df["DATA ENTREGA"].dt.date.isin(data_sel)) &
    (df["MALHA"].isin(malha_sel)) &
    (df["TSP_NORMALIZADO"].isin(tsp_sel)) &
    (df["EQUIPE VENDA"].isin(equipe_sel))

]

if tipo_pedido != "TODOS":

    df_filtro = df_filtro[
        df_filtro["TIPO_PEDIDO"] == tipo_pedido
    ]

# =========================================================
# KPI
# =========================================================

peso_total = df_filtro["PESO_TOTAL"].sum()

peso_grade = df_filtro[
    df_filtro["TIPO_PEDIDO"] == "GRADE"
]["PESO_TOTAL"].sum()

peso_aberto = df_filtro[
    df_filtro["TIPO_PEDIDO"] == "ABERTO"
]["PESO_TOTAL"].sum()

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

    acima_85 = [

        x for x in melhores
        if x["ocupacao"] >= 85

    ]

    if acima_85:

        melhor = sorted(

            acima_85,

            key=lambda x: (

                x["sobra"],
                x["qtd"]

            )

        )[0]

    else:

        melhor = sorted(

            melhores,

            key=lambda x: (

                abs(85 - x["ocupacao"]),
                x["sobra"]

            )

        )[0]

    return (

        melhor["veiculo"],
        melhor["qtd"],
        melhor["capacidade"],
        melhor["ocupacao"]

    )

# =========================================================
# APLICAR OTIMIZAÇÃO
# =========================================================

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
# STATUS
# =========================================================

def definir_status_ocupacao(ocupacao):

    if ocupacao >= 85:
        return "🟢 IDEAL"

    elif ocupacao >= 75:
        return "🟡 ATENCAO"

    else:
        return "🔴 CRITICO"

df_malha["STATUS_OCUPACAO"] = df_malha[
    "OCUPACAO"
].apply(definir_status_ocupacao)

# =========================================================
# ALERTAS
# =========================================================

df_alerta = df_malha[
    df_malha["OCUPACAO"] < 85
].copy()

qtd_alertas = len(df_alerta)

qtd_critico = len(
    df_malha[
        df_malha["OCUPACAO"] < 75
    ]
)

qtd_atencao = len(
    df_malha[
        (df_malha["OCUPACAO"] >= 75) &
        (df_malha["OCUPACAO"] < 85)
    ]
)

# =========================================================
# KPI CD
# =========================================================

capacidade_total_cd = 0

for tsp in tsp_sel:

    if tsp in config_tsp:

        capacidade_total_cd += config_tsp[tsp]["capacidade_cd"]

ocupacao_cd = 0

if capacidade_total_cd > 0:

    ocupacao_cd = (
        peso_total / capacidade_total_cd
    ) * 100

# =========================================================
# KPI
# =========================================================

st.title("📦 Dashboard Logístico")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric(
    "🚚 Peso Total",
    f"{peso_total:,.0f} KG"
)

col2.metric(
    "📦 Grade",
    f"{peso_grade:,.0f} KG"
)

col3.metric(
    "📭 Aberto",
    f"{peso_aberto:,.0f} KG"
)

col4.metric(
    "🏭 Ocupação CD",
    f"{ocupacao_cd:.1f}%"
)

col5.metric(
    "🟡 Atenção",
    qtd_atencao
)

col6.metric(
    "🔴 Crítico",
    qtd_critico
)

# =========================================================
# COR
# =========================================================

def cor_ocupacao(v):

    if v >= 85:
        return "background-color: #2ecc71; color: white"

    elif v >= 75:
        return "background-color: #f1c40f; color: black"

    else:
        return "background-color: #e74c3c; color: white"

# =========================================================
# ALERTAS
# =========================================================

if not df_alerta.empty:

    st.warning(
        f"⚠️ {qtd_alertas} malhas abaixo da ocupação ideal"
    )

    st.subheader("🚨 Alertas de Ocupação")

    st.dataframe(

        df_alerta[[

            "MALHA",
            "PESO_TOTAL",
            "VEICULO_ESCALADO",
            "CAPACIDADE_TOTAL",
            "OCUPACAO",
            "STATUS_OCUPACAO"

        ]]

        .sort_values(
            "OCUPACAO"
        )

        .style

        .map(
            cor_ocupacao,
            subset=["OCUPACAO"]
        )

        .format({

            "PESO_TOTAL": "{:,.0f}",
            "CAPACIDADE_TOTAL": "{:,.0f}",
            "OCUPACAO": "{:.1f}%"

        }),

        width="stretch"
    )

else:

    st.success(
        "✅ Todas as malhas estão na ocupação ideal"
    )

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

    color="STATUS_OCUPACAO",

    custom_data=[

        "VEICULO_ESCALADO",
        "OCUPACAO",
        "CAPACIDADE_TOTAL",
        "QTD_VEICULOS"

    ],

    color_discrete_map={

        "🟢 IDEAL": "green",
        "🟡 ATENCAO": "yellow",
        "🔴 CRITICO": "red"

    }
)

fig.update_traces(

    texttemplate=

    "<b>%{x}</b><br>" +
    "%{y:,.0f} KG<br>" +
    "%{customdata[0]}<br>" +
    "%{customdata[1]:.0f}%",

    textposition="inside",

    hovertemplate=

    "<b>%{x}</b><br><br>" +

    "Peso: %{y:,.0f} KG<br>" +

    "Veículo: %{customdata[0]}<br>" +

    "Quantidade: %{customdata[3]}<br>" +

    "Capacidade: %{customdata[2]:,.0f} KG<br>" +

    "Ocupação: %{customdata[1]:.1f}%<br>" +

    "<extra></extra>"
)

fig.update_layout(

    height=750,

    xaxis_title="Malha",
    yaxis_title="Peso KG",

    legend_title="Status",

    uniformtext_minsize=8,
    uniformtext_mode='hide'
)

st.plotly_chart(
    fig,
    width="stretch"
)

# =========================================================
# TABELA FINAL
# =========================================================

st.subheader("📋 Resumo Logístico")

df_exibir = df_malha.copy()

df_exibir["VEICULOS_PERMITIDOS"] = (
    df_exibir["VEICULOS_PERMITIDOS"]
    .astype(str)
)

st.dataframe(

    df_exibir.sort_values(
        "PESO_TOTAL",
        ascending=False
    )

    .style

    .map(
        cor_ocupacao,
        subset=["OCUPACAO"]
    )

    .format({

        "PESO_TOTAL": "{:,.0f}",
        "CAPACIDADE_TOTAL": "{:,.0f}",
        "OCUPACAO": "{:.1f}%"

    }),

    width="stretch"
)