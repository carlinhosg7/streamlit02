import pandas as pd

arquivos = [
    "DADOS_PREDITIVA_1_LIMPO.csv.gz",
    "DADOS_PREDITIVA_2_LIMPO.csv.gz",
    "DADOS_PREDITIVA_3_LIMPO.csv.gz",
    "DADOS_PREDITIVA_4_LIMPO.csv.gz"
]

for arquivo in arquivos:
    print(f"🔍 Verificando {arquivo}")
    try:
        df = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig", compression="gzip", engine="python")
        print(f"✅ {arquivo} lido com sucesso. Linhas: {len(df)}, Colunas: {len(df.columns)}")
        print(f"📋 Colunas: {df.columns.tolist()}\n")
    except Exception as e:
        print(f"❌ Erro ao ler {arquivo}: {e}\n")
