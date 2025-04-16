import streamlit as st
import pandas as pd
import calendar

# Carregar os dados (pode ser ajustado para carregar em cache)
@st.cache_data
def carregar_dados():
    file_path = r"C:/Kidy/PREDITIVA/DADOS_PREDITIVA.xlsx"
    return pd.read_excel(file_path, sheet_name='DADOS PREDITIVA')

df = carregar_dados()

st.title("🔍 Análise de Grupo de Clientes - Preditiva Kidy")

# Interface do usuário
codigo_grupo_cliente = st.text_input("Digite o Código do Grupo de Cliente:")

if st.button("Analisar Grupo"):
    if not codigo_grupo_cliente:
        st.warning("⚠️ Informe um código de grupo de cliente!")
    else:
        dados_grupo = df[df['Codigo Grupo Cliente'] == codigo_grupo_cliente].copy()

        if dados_grupo.empty:
            st.error(f"Nenhum dado encontrado para o grupo: {codigo_grupo_cliente}")
        else:
            nome_grupo = dados_grupo['Grupo Cliente'].iloc[0]
            ultima_data = dados_grupo['Data Ultima Compra'].max()
            ultima_compra = ultima_data.strftime('%d/%m/%Y') if pd.notnull(ultima_data) else 'Sem compras registradas'
            
            st.subheader(f"📌 Grupo Cliente: {nome_grupo}")
            st.write(f"🗓️ Última Compra: {ultima_compra}")

            if dados_grupo['Data Cadastro'].isnull().all():
                st.warning("⚠️ Nenhuma data de cadastro disponível para análise!")
            else:
                dados_grupo['Mes Pedido'] = dados_grupo['Data Cadastro'].dt.month
                melhor_mes_num = dados_grupo['Mes Pedido'].mode()[0]
                melhor_mes_nome = calendar.month_name[melhor_mes_num]

                st.success(f"👉 Melhor mês para oferecer produtos: **{melhor_mes_nome}**")
                
                top_linhas = (dados_grupo.groupby('Linha')['Qtd Venda']
                              .sum()
                              .sort_values(ascending=False)
                              .head(10))

                if top_linhas.empty:
                    st.warning("⚠️ Nenhuma venda encontrada para análise de linhas de produto.")
                else:
                    st.subheader("👉 Top 10 Linhas de Produtos para Oferecer:")
                    st.table(top_linhas.reset_index().rename(columns={'Qtd Venda': 'Quantidade Vendida'}))

