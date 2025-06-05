import pandas as pd

# Caminho do seu arquivo
arquivo_excel = "DADOS_PREDITIVA.xlsx"

# Lê a planilha inteira
df = pd.read_excel(arquivo_excel, sheet_name=0)

# Divide em duas partes
meio = len(df) // 2
df1 = df.iloc[:meio]
df2 = df.iloc[meio:]

# Salva os dois arquivos como CSV
df1.to_csv("DADOS_PREDITIVA_1.csv", index=False, encoding='utf-8-sig')
df2.to_csv("DADOS_PREDITIVA_2.csv", index=False, encoding='utf-8-sig')

print("Arquivos divididos e salvos com sucesso!")
