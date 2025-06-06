import pandas as pd

arquivos = [
    "DADOS_PREDITIVA_1.csv",
    "DADOS_PREDITIVA_2.csv",
    "DADOS_PREDITIVA_3.csv",
    "DADOS_PREDITIVA_4.csv"
]

for arquivo in arquivos:
    print(f"🔄 Lendo {arquivo}")
    df = pd.read_csv(arquivo, sep=";", encoding="cp1252")
    
    saida = f"{arquivo}.gz"
    print(f"💾 Salvando como {saida}")
    df.to_csv(saida, sep=";", encoding="cp1252", index=False, compression="gzip")

    print(f"✅ {saida} gerado com sucesso\n")
