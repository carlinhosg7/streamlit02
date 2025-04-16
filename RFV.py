import pandas as pd
import numpy as np

# Caminho do arquivo
file_path = "H:/Meu Drive/Kidy/PREDITIVA/DADOS/DADOS_PREDITIVA.xlsx"

# Carregar somente as colunas necessárias para o cálculo do RFV
colunas_rfv = ["Codigo Cliente", "Data Ultima Compra", "Numero Pedido", "Vlr Venda"]
df = pd.read_excel(file_path, sheet_name="DADOS_PREDITIVA", usecols=colunas_rfv, parse_dates=["Data Ultima Compra"])

# Garantir que o código do cliente seja string
df["Codigo Cliente"] = df["Codigo Cliente"].astype(str)

# Agrupar os dados para RFV
rfv = df.groupby("Codigo Cliente").agg({
    "Data Ultima Compra": lambda x: (pd.Timestamp.today() - x.max()).days,
    "Numero Pedido": "count",
    "Vlr Venda": "sum"
}).rename(columns={
    "Data Ultima Compra": "Recencia",
    "Numero Pedido": "Frequencia",
    "Vlr Venda": "Valor"
})

# Quantis para RFV
rfv["R_quantil"] = pd.qcut(rfv["Recencia"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfv["F_quantil"] = pd.qcut(rfv["Frequencia"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfv["V_quantil"] = pd.qcut(rfv["Valor"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

# RFV Score
rfv["RFV_Score"] = rfv["R_quantil"].astype(str) + rfv["F_quantil"].astype(str) + rfv["V_quantil"].astype(str)

# Classificação de Segmento
def classificar(score):
    total = sum(int(d) for d in score)
    if total >= 13:
        return "Cliente Premium"
    elif total >= 10:
        return "Cliente Valioso"
    elif total >= 7:
        return "Cliente Médio"
    else:
        return "Cliente em Risco"

rfv["Segmento"] = rfv["RFV_Score"].apply(classificar)

# Exportar para Excel
rfv.reset_index().to_excel("RFV_CLIENTES.xlsx", index=False)
