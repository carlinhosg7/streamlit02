import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="📊 Cobertura de Carteira", layout="wide")
st.title("📈 Análise de Cobertura de Carteira por Representante")

# ✅ URL RAW correta do GitHub
URL_DADOS = "https://raw.githubusercontent.com/carlinhosg7/cob_cart/main/Cobertura_de_Carteira.xlsx"

try:
    # Baixa o conteúdo do Excel da URL
    response = requests.get(URL_DADOS)
    response.raise_for_status()
    df = pd.read_excel(BytesIO(response.content), header=7, engine="openpyxl")
    df.columns = df.columns.str.strip()

    colunas_ok = ['Rep', 'Nome Rep.', 'Saldo de Carteira', 'cobertura']
    if all(col in df.columns for col in colunas_ok):
        df = df.dropna(subset=['Rep', 'Saldo de Carteira', 'cobertura'])
        df = df.sort_values(by='Saldo de Carteira', ascending=False)

        # Filtro de Supervisor
        if 'Supervisor' in df.columns:
            supervisores_disponiveis = df['Supervisor'].dropna().unique().tolist()
            supervisor_selecionado = st.selectbox("🧑‍💼 Selecione um Supervisor:", options=["Todos"] + supervisores_disponiveis)
            if supervisor_selecionado != "Todos":
                df = df[df['Supervisor'] == supervisor_selecionado]

        # Filtro de Representante
        reps_disponiveis = df['Rep'].unique().tolist()
        rep_selecionado = st.selectbox("👤 Selecione um Representante:", options=["Todos"] + reps_disponiveis)

        if rep_selecionado == "Todos":
            total_saldo = df['Saldo de Carteira'].sum()
            total_cobertura = df['cobertura'].sum()
            perc_total = round((total_cobertura / total_saldo) * 100, 1)
            
            
            # 📈 Gráfico de Linha comparando Carteira vs Cobertura
            st.markdown("### 📉 Evolução da Carteira x Cobertura")

            fig_linha = go.Figure()

            fig_linha.add_trace(go.Scatter(
                x=df['Rep'].astype(str),
                y=df['Saldo de Carteira'],
                mode='lines+markers',
                name='💼 Carteira',
                line=dict(color='lightgray', width=3)
            ))

            fig_linha.add_trace(go.Scatter(
                x=df['Rep'].astype(str),
                y=df['cobertura'],
                mode='lines+markers',
                name='✅ Cobertura',
                line=dict(color='#FF6600', width=3)
            ))

            fig_linha.update_layout(
                xaxis_title='Representante',
                yaxis_title='Clientes',
                legend_title='Indicador',
                height=400,
                template='plotly_white'
            )

            st.plotly_chart(fig_linha, use_container_width=True)


            # Gráfico geral
            fig = go.Figure()
            fig.add_trace(go.Bar(y=["TOTAL"], x=[total_saldo], name='Saldo de Carteira', orientation='h', marker=dict(color='lightgray')))
            fig.add_trace(go.Bar(y=["TOTAL"], x=[total_cobertura], name='Cobertura', orientation='h', marker=dict(color='#FF6600')))
            fig.update_layout(barmode='overlay', title='Cobertura Total da Carteira', xaxis_title='Número de Clientes', yaxis_title='', height=300,
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)

            # Cartões com borda
            with st.container():
                st.markdown("### 📊 Resumo da Cobertura")
                col1, col2, col3 = st.columns(3)

                estilo = """
                    <div style='
                        border: 2px solid #ddd;
                        border-radius: 12px;
                        padding: 20px;
                        text-align: center;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                    '>
                        <div style='font-size: 20px; font-weight: bold;'>{}</div>
                        <div style='font-size: 32px; color: #444; margin-top: 8px;'>{}</div>
                    </div>
                """

                col1.markdown(estilo.format("💼 Carteira", f"{total_saldo:,.0f}".replace(",", ".")), unsafe_allow_html=True)
                col2.markdown(estilo.format("✅ Cobertura", f"{total_cobertura:,.0f}".replace(",", ".")), unsafe_allow_html=True)
                col3.markdown(estilo.format("📈 % Cobertura", f"{perc_total:.1f}%"), unsafe_allow_html=True)

            st.subheader("📋 Cobertura Geral (%)")
            st.dataframe(df[['Rep', 'Nome Rep.', 'Saldo de Carteira', 'cobertura']])

        else:
            df_filtrado = df[df['Rep'] == rep_selecionado]
            total_saldo = df_filtrado['Saldo de Carteira'].sum()
            total_cobertura = df_filtrado['cobertura'].sum()
            perc = round((total_cobertura / total_saldo) * 100, 1)

            # Gráfico individual
            fig = go.Figure()
            fig.add_trace(go.Bar(y=df_filtrado['Rep'].astype(str), x=df_filtrado['Saldo de Carteira'], name='Saldo de Carteira', orientation='h', marker=dict(color='lightgray')))
            fig.add_trace(go.Bar(y=df_filtrado['Rep'].astype(str), x=df_filtrado['cobertura'], name='Cobertura', orientation='h', marker=dict(color='#FF6600')))
            fig.update_layout(barmode='overlay', title=f'Cobertura de Carteira - Rep {rep_selecionado}', xaxis_title='Número de Clientes', yaxis_title='Representante', height=400,
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)

            # Cartões simples
            col1, col2 = st.columns(2)
            col1.metric("💼 Carteira", f"{total_saldo:,.0f}".replace(",", "."), help="Total de clientes ativos")
            col2.metric("✅ Cobertura", f"{total_cobertura:,.0f}".replace(",", "."), help="Clientes já positivados")

            # Tabela
            df_filtrado['% Cobertura'] = (df_filtrado['cobertura'] / df_filtrado['Saldo de Carteira']) * 100
            df_filtrado['% Cobertura'] = df_filtrado['% Cobertura'].round(1).astype(str) + '%'
            st.subheader("📋 Detalhamento da Cobertura (%)")
            st.dataframe(df_filtrado[['Rep', 'Nome Rep.', 'Saldo de Carteira', 'cobertura', '% Cobertura']])
    else:
        st.error("⚠️ Colunas obrigatórias não encontradas:")
        st.write("Colunas lidas:", df.columns.tolist())

except Exception as e:
    st.error(f"❌ Erro ao carregar os dados do GitHub: {e}")
