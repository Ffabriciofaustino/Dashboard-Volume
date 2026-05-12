import pandas as pd
arquivo = r"C:\Users\fabricio.faustino\Desktop\TABELAS\TABELA_DE_FRETE.xlsx"

CAPACIDADES_KG = {
    "BI-TRUCK": 16000,
    "FIORINO": 500,
    "SEMI-LEVE": 1500,
    "SUPER 3/4": 5000,
    "TOCO": 6000,
    "TRUCK": 11000,
    "VUC": 2500,
    "3/4": 3500,
}

COLS_OBRIGATORIAS = [
    "TRANSPORTADORA",
    "ORIGEM",
    "TIPOLOGIA",
    "SAIDA",
    "KM",
    "SAIDA PERNOITE",
    "DESCONTA SEGURO",
    "VALOR SEGURO",
]


def normaliza_tipologia(x):
    if pd.isna(x):
        return ""

    s = str(x).strip().upper()

    if s in {"0.75", "0,75", "0.750", "0,750"}:
        s = "3/4"

    s = s.replace("BITRUCK", "BI-TRUCK")
    s = s.replace("BI TRUCK", "BI-TRUCK")

    return s


def calcula_frete(row, km_input, pernoites, incluir_seguro):
    saida = float(row["SAIDA"])
    r_km = float(row["KM"])

    frete_km = r_km * km_input
    frete_saida = saida + frete_km
    frete_pernoite = pernoites * saida
    frete_seguro = 0

    if incluir_seguro and row["DESCONTA SEGURO"] == "SIM":
        frete_seguro = float(row["VALOR SEGURO"])

    total = frete_saida + frete_pernoite + frete_seguro

    return total


# ====== INÍCIO DO PROGRAMA ======

arquivo = "TABELA_DE_FRETE.xlsx"

df = pd.read_excel(arquivo)
df.columns = [c.strip().upper() for c in df.columns]

faltando = [c for c in COLS_OBRIGATORIAS if c not in df.columns]
if faltando:
    print("Colunas obrigatórias faltando:", faltando)
    exit()

df["TIPOLOGIA"] = df["TIPOLOGIA"].apply(normaliza_tipologia)
df["DESCONTA SEGURO"] = df["DESCONTA SEGURO"].astype(str).str.upper()

print("\nORIGENS DISPONÍVEIS:")
print(df["ORIGEM"].unique())

origem = input("\nDigite a origem: ").strip()

print("\nTRANSPORTADORAS:")
print(df[df["ORIGEM"] == origem]["TRANSPORTADORA"].unique())

transportadora = input("\nDigite a transportadora: ").strip()

print("\nTIPOLOGIAS:")
print(
    df[
        (df["ORIGEM"] == origem)
        & (df["TRANSPORTADORA"] == transportadora)
    ]["TIPOLOGIA"].unique()
)

tipologia = input("\nDigite a tipologia: ").strip().upper()

peso = float(input("Peso (kg): "))
km = float(input("Distância (km): "))
pernoites = int(input("Quantidade de pernoites: "))
seguro = input("Incluir seguro? (S/N): ").upper() == "S"

filtro = (
    (df["ORIGEM"] == origem)
    & (df["TRANSPORTADORA"] == transportadora)
    & (df["TIPOLOGIA"] == tipologia)
)

if not filtro.any():
    print("Combinação não encontrada.")
    exit()

row = df.loc[filtro].iloc[0]

total = calcula_frete(row, km, pernoites, seguro)

print("\n========== RESULTADO ==========")
print(f"Frete total: R$ {total:.2f}")

capacidade = CAPACIDADES_KG.get(tipologia)

if capacidade:
    ocupacao = (peso / capacidade) * 100
    print(f"Ocupação do veículo: {ocupacao:.1f}%")