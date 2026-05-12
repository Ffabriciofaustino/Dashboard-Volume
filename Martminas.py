import pandas as pd
from pathlib import Path
from datetime import datetime

# =========================
# PARÂMETROS
# =========================
arquivo_consolidado = r"C:\Users\fabricio.faustino\Desktop\PROJETOS\consolidado_loja_mes.xlsx"
mes_planejado = "2026-02"
peso_previsto_mes = 200_000

peso_base = "Peso_Embarcado"   # ou "Peso_Solicitado"
col_cidade = "Cidade"

# =========================
# LEITURA
# =========================
df = pd.read_excel(arquivo_consolidado)
df["Mes"] = df["Mes"].astype(str).str.strip()

for c in [col_cidade, "Mes", peso_base]:
    if c not in df.columns:
        raise ValueError(f"Coluna '{c}' não encontrada. Colunas disponíveis: {list(df.columns)}")

# usa o último mês do histórico como referência de proporção
mes_ref = df["Mes"].max()

base = (df[df["Mes"] == mes_ref]
        .groupby(col_cidade, as_index=False)[peso_base]
        .sum()
        .rename(columns={peso_base: "Peso_Ref"}))

total_ref = float(base["Peso_Ref"].sum())
if total_ref <= 0:
    raise ValueError(f"Total de '{peso_base}' no mês de referência ({mes_ref}) é 0.")

base["Proporcao"] = base["Peso_Ref"] / total_ref

# previsão por cidade
base["Mes_Planejado"] = mes_planejado
base["Peso_Previsto_Cidade"] = base["Proporcao"] * peso_previsto_mes

# =========================
# SAÍDA
# =========================
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
saida = Path(arquivo_consolidado).with_name(f"kg_por_cidade_{mes_planejado}_{ts}.xlsx")

out = base.sort_values("Peso_Previsto_Cidade", ascending=False)
out.to_excel(saida, index=False)

print(f"OK -> {saida}")
print(f"Soma previsto (checagem): {out['Peso_Previsto_Cidade'].sum():,.2f} kg")