import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import unicodedata

# ======================================================
# NORMALIZAR TEXTO
# ======================================================

def normalizar(texto):
    if pd.isna(texto):
        return None
    
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    
    return texto

# ======================================================
# CAMINHO
# ======================================================

BASE_DIR = Path(__file__).resolve().parent

df = pd.read_excel(BASE_DIR / "volume.xlsx")
df_grade = pd.read_excel(BASE_DIR / "GRADE MI  MAIO 2026.xlsx")

# ======================================================
# COLUNAS
# ======================================================

COL_DATA = "Data Entrega"
COL_CIDADE = "Cidade"
COL_PESO = "Peso Total"
COL_ZONEAMENTO = "Zoneamento"

# ======================================================
# TRATAMENTO
# ======================================================

df[COL_DATA] = pd.to_datetime(df[COL_DATA], dayfirst=True, errors="coerce").dt.date

df[COL_PESO] = (
    df[COL_PESO].astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)
df[COL_PESO] = pd.to_numeric(df[COL_PESO], errors="coerce").fillna(0)

# normalizar
df[COL_CIDADE] = df[COL_CIDADE].apply(normalizar)
df[COL_ZONEAMENTO] = df[COL_ZONEAMENTO].apply(normalizar)

df_grade["Cidade"] = df_grade["Cidade"].apply(normalizar)
df_grade["Malha"] = df_grade["Malha"].apply(normalizar)

# ======================================================
# DICIONÁRIO CIDADE → MALHA (GRADE)
# ======================================================

dict_cidade_malha = (
    df_grade.drop_duplicates("Cidade")
    .set_index("Cidade")["Malha"]
    .to_dict()
)

# ======================================================
# 🔥 REGRA PRINCIPAL (BH DIFERENTE)
# ======================================================

def definir_malha(row):
    cidade = row[COL_CIDADE]
    zona = row[COL_ZONEAMENTO]
    
    # REGRA BH
    if cidade == "BELO HORIZONTE":
        if pd.notna(zona) and zona not in ["", "0"]:
            return zona  # usa zoneamento como malha
        else:
            return "SEM MALHA"
    
    # REGRA NORMAL
    return dict_cidade_malha.get(cidade, "SEM MALHA")

df["Malha"] = df.apply(definir_malha, axis=1)

# ======================================================
# CLASSIFICAÇÃO
# ======================================================

hoje = datetime.today().date()
data_grade = hoje + timedelta(days=1)

df["TIPO_PEDIDO"] = df[COL_DATA].apply(
    lambda x: "GRADE" if x == data_grade else "ABERTO"
)

# ======================================================
# AGRUPAMENTO FINAL (POR MALHA)
# ======================================================

relatorio = df.groupby(
    [COL_DATA, "Malha", "TIPO_PEDIDO"],
    as_index=False
).agg(PESO_TOTAL=(COL_PESO, "sum"))

# ======================================================
# EXPORTAÇÃO
# ======================================================

arquivo_saida = BASE_DIR / "peso_por_malha_bh_corrigido.xlsx"
relatorio.to_excel(arquivo_saida, index=False)

print("✅ RELATÓRIO FINAL CORRETO")
print(arquivo_saida)