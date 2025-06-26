import pandas as pd
import gzip

arquivos = [
    "DADOS_PREDITIVA_1.csv.gz",
    "DADOS_PREDITIVA_2.csv.gz",
    "DADOS_PREDITIVA_3.csv.gz",
    "DADOS_PREDITIVA_4.csv.gz"
]

for arquivo in arquivos:
    print(f"🔍 Verificando {arquivo}")
    try:
        df = pd.read_csv(arquivo, sep=";", encoding="latin1", compression="gzip", engine="python")
        print(f"✅ {arquivo} lido com sucesso. Linhas: {len(df)}, Colunas: {len(df.columns)}")
        print(f"📋 Colunas: {df.columns.tolist()}\n")
    except Exception as e:
        print(f"❌ Erro ao ler {arquivo}: {e}\n")
