import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="RFV App", layout="wide")

# 📦 Dados de exemplo (você pode trocar depois pelos seus dados reais)
data = {
    'Data Ultima Compra': pd.to_datetime(['2023-08-10', '2023-11-15', '2024-06-01']),
    'Data Cadastro': pd.to_datetime(['2023-08-10', '2023-11-15', '2024-06-01']),
    'Vlr Venda': [10000, 15000, 20000]
}
df = pd.DataFrame(data)
dados_filtrados = df.copy()

# ✅ Função correta com valor nos 12 meses ANTERIORES à última compra
def calcular_rfv_individual(dados_filtrados):
    hoje = datetime.today()

    if not dados_filtrados['Data Ultima Compra'].empty:
        data_ultima_compra = dados_filtrados['Data Ultima Compra'].max()
        recencia = (hoje - data_ultima_compra).days
    else:
        data_ultima_compra = None
        recencia = 999

    frequencia = dados_filtrados['Data Cadastro'].nunique()

    if data_ultima_compra:
        data_inicio = data_ultima_compra - pd.DateOffset(months=12)
        dados_valor = dados_filtrados[
            (dados_filtrados['Data Ultima Compra'] >= data_inicio) &
            (dados_filtrados['Data Ultima Compra'] <= data_ultima_compra)
        ]
        valor = dados_valor['Vlr Venda'].sum()
    else:
        valor = 0

    recencia_score = 5 if recencia <= 30 else 4 if recencia <= 90 else 3 if recencia <= 180 else 2 if recencia <= 365 else 1
    frequencia_score = 5 if frequencia >= 12 else 4 if frequencia >= 6 else 3 if frequencia >= 3 else 2 if frequencia >= 1 else 1
    valor_score = 5 if valor >= 50000 else 4 if valor >= 20000 else 3 if valor >= 10000 else 2 if valor >= 5000 else 1

    rfv_score = f"{recencia_score}{frequencia_score}{valor_score}"

    if rfv_score == '555':
        classificacao = 'Cliente VIP'
    elif recencia_score >= 4 and frequencia_score >= 4:
        classificacao = 'Cliente Leal'
    elif recencia_score >= 3:
        classificacao = 'Cliente Potencial'
    else:
        classificacao = 'Cliente em Risco'

    return {
        'Recência (dias)': recencia,
        'Frequência (pedidos únicos)': frequencia,
        'Valor Total (R$)': f"{valor:,.2f}",
        'RFV Score': rfv_score,
        'Classificação': classificacao,
        'Última Compra': data_ultima_compra.strftime('%d/%m/%Y') if data_ultima_compra else 'Sem registro'
    }

# 🧠 Chamada e exibição
st.title("Análise RFV (baseada na última compra)")
if dados_filtrados.empty:
    st.warning("Nenhum dado encontrado.")
else:
    rfv_resultado = calcular_rfv_individual(dados_filtrados)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Recência (dias)", rfv_resultado['Recência (dias)'])
    col2.metric("Frequência", rfv_resultado['Frequência (pedidos únicos)'])
    col3.metric("Valor Total (R$)", rfv_resultado['Valor Total (R$)'])
    col4.metric("RFV Score", rfv_resultado['RFV Score'])
    col5.metric("Classificação", rfv_resultado['Classificação'])

    st.caption(f"📅 Última Compra: {rfv_resultado['Última Compra']}")
