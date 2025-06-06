import pandas as pd

arquivos = [
    "DADOS_PREDITIVA_1.csv",
    "DADOS_PREDITIVA_2.csv",
    "DADOS_PREDITIVA_3.csv",
    "DADOS_PREDITIVA_4.csv"
]

for arquivo in arquivos:
    try:
        print(f"🔄 Compactando {arquivo} ...")
        df = pd.read_csv(arquivo, sep=";", encoding="cp1252")
        df.to_csv(f"{arquivo}.gz", sep=";", index=False, encoding="cp1252", compression="gzip")
        print(f"✅ Salvo como {arquivo}.gz")
    except Exception as e:
        print(f"❌ Erro com {arquivo}: {e}")
