import pandas as pd

# Caminho do arquivo original
arquivo_excel = "DADOS_PREDITIVA.xlsx"

# Carrega o Excel inteiro
df = pd.read_excel(arquivo_excel, sheet_name=0)

# Divide o DataFrame ao meio
meio = len(df) // 2
df1 = df.iloc[:meio]
df2 = df.iloc[meio:]

# Salva os arquivos divididos
df1.to_csv("DADOS_PREDITIVA_1.csv", index=False, encoding='utf-8-sig')
df2.to_csv("DADOS_PREDITIVA_2.csv", index=False, encoding='utf-8-sig')

print("Arquivos salvos com sucesso!")
