import pandas as pd

# Ajuste o caminho do arquivo
arquivo = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\base01-06.xlsx"
saida = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\base01-06_agrupado.xlsx"

# começa a ler a partir da 2ª linha (pula a 1ª)
df = pd.read_excel(arquivo, sheet_name=0, skiprows=2)

# nome das colunas que esta identico na planilha
col_data = "Data"
col_malha = "Rota"
col_cidade = "Cidade"
col_peso_solicitado = "Peso Solicitado"
col_peso_embarcado = "Peso Embarcado"
col_unidade = "Empresa"

df.columns = df.columns.astype(str).str.strip()
df[col_data] = pd.to_datetime(df[col_data], errors="coerce")

# Diário
diario = (
    df.assign(Periodo=df[col_data].dt.floor("D"))
      .groupby(["Periodo", col_cidade, col_malha, col_unidade], as_index=False)[[col_peso_solicitado , col_peso_embarcado]]
      .sum()
)

# Semanal (semana começando na segunda-feira)
semanal = (
    df.assign(Periodo=df[col_data].dt.to_period("W-MON").dt.start_time)
      .groupby(["Periodo", col_cidade, col_malha, col_unidade], as_index=False)[[col_peso_solicitado, col_peso_embarcado]]
      .sum()
)

# Mensal
mensal = (
    df.assign(Periodo=df[col_data].dt.to_period("M").dt.start_time)
      .groupby(["Periodo", col_cidade, col_malha,col_unidade], as_index=False)[[col_peso_solicitado, col_peso_embarcado]]
      .sum()
)


with pd.ExcelWriter(saida, engine="xlsxwriter") as writer:
    diario.to_excel(writer, sheet_name="Diario", index=False)
    semanal.to_excel(writer, sheet_name="Semanal", index=False)
    mensal.to_excel(writer, sheet_name="Mensal", index=False)

print("Arquivo gerado em:", saida)












#
#print("Linhas/colunas:", df.shape)
#print(df.head(10))