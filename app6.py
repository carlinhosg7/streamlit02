import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import tempfile
import os
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import time
import plotly.io as pio
import kaleido # força o loading do kaleido para evitar erro de importação
pio.kaleido.scope.default_format = "png"
import plotly.express as px

# CONFIG PÁGINA
st.set_page_config(
    page_title="Dashboard Analítico",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS CUSTOMIZADO
def add_custom_css():
    st.markdown("""
        <style>
        body {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .css-1d391kg {
            background-color: #1e1e1e !important;
        }
        .block-container {
            padding: 2rem;
        }
        div.stButton > button:first-child {
            background-color: #E60012;
            color: white;
            border-radius: 8px;
            height: 3em;
            width: 100%;
            font-weight: bold;
            border: none;
            transition: 0.3s;
        }
        div.stButton > button:first-child:hover {
            background-color: #A3000B;
        }
        footer {visibility: hidden;}

        /* Cards para métricas */
        .metric-card {
            background-color: #2d2d2d;
            padding: 16px;
            border-radius: 10px;
            box-shadow: 1px 1px 8px rgba(0,0,0,0.3);
            text-align: center;
            margin-bottom: 8px;
            border: 1px solid #fba72033;
        }
        .metric-label {
            font-size: 13px;
            color: #bbbbbb;
        }
        .metric-value {
            font-size: 22px;
            font-weight: bold;
            color: #F7A400;
        }
        </style>
    """, unsafe_allow_html=True)

add_custom_css()

# LOGO KIDY
logo_kidy = Image.open("logo_kidy.png")
st.image(logo_kidy, width=100)

# DICIONÁRIO MESES
meses_portugues = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# URL do arquivo no GitHub (modo leitura)
URL_1 = "https://raw.githubusercontent.com/carlinhosg7/streamlit02/refs/heads/main/DADOS_PREDITIVA_1.csv"
URL_2 = "https://raw.githubusercontent.com/carlinhosg7/streamlit02/refs/heads/main/DADOS_PREDITIVA_2.csv"

# CARREGAR DADOS
@st.cache_data(ttl=3600)
def carregar_dados_processados():
    try:
        df1 = pd.read_csv(URL_1)
        df2 = pd.read_csv(URL_2)
        df = pd.concat([df1, df2], ignore_index=True)

        # Conversões e ajustes como antes
        df['Data Cadastro'] = pd.to_datetime(df['Data Cadastro'], errors='coerce')
        df['Data Ultima Compra'] = pd.to_datetime(df['Data Ultima Compra'], errors='coerce')
        df['Codigo Grupo Cliente'] = df['Codigo Grupo Cliente'].astype(str).str.upper()
        df['Codigo Cliente'] = df['Codigo Cliente'].astype(str).str.upper()
        df['Preço Médio Produto'] = df.apply(
            lambda row: row['Vlr Venda'] / row['Qtd Venda'] if row['Qtd Venda'] > 0 else 0, axis=1
        )
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# RFV SCORE
def calcular_rfv_individual(dados_filtrados):
    hoje = datetime.today()

    recencia = (hoje - dados_filtrados['Data Ultima Compra'].max()).days if pd.notnull(dados_filtrados['Data Ultima Compra'].max()) else 999
    frequencia = dados_filtrados['Data Cadastro'].nunique()
    valor = dados_filtrados['Vlr Venda'].sum()

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
        'Classificação': classificacao
    }

# CARREGA DADOS
df = carregar_dados_processados()

if df.empty:
    st.stop()

# FILTROS SIDEBAR
st.title("📊 Dashboard Analítico")
st.sidebar.image(logo_kidy, width=100)
st.sidebar.header("🔧 Filtros de Análise")

codigo_grupo_cliente = st.sidebar.text_input("Código do Grupo de Cliente (Opcional):").strip().upper()
codigo_cliente = st.sidebar.text_input("Código do Cliente (Opcional):").strip().upper()

data_min = df['Data Cadastro'].min().date()
data_max = df['Data Cadastro'].max().date()

periodo = st.sidebar.date_input(
    "Período da análise:",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max
)

# BOTÃO
if st.sidebar.button("🔎 Analisar Grupo/Cliente"):

    if not codigo_grupo_cliente and not codigo_cliente:
        st.sidebar.warning("⚠️ Informe pelo menos um código!")
    else:
        with st.spinner('🔎 Analisando dados...'):

            dados_filtrados = df.copy()

            if codigo_cliente:
                dados_filtrados = dados_filtrados[dados_filtrados['Codigo Cliente'] == codigo_cliente]
            elif codigo_grupo_cliente:
                dados_filtrados = dados_filtrados[dados_filtrados['Codigo Grupo Cliente'] == codigo_grupo_cliente]

            dados_filtrados = dados_filtrados[
                (dados_filtrados['Data Cadastro'] >= pd.to_datetime(periodo[0])) &
                (dados_filtrados['Data Cadastro'] <= pd.to_datetime(periodo[1]))
            ]

            if dados_filtrados.empty:
                st.warning("⚠️ Nenhum dado encontrado no período!")
            else:
                dados_filtrados['Ano'] = dados_filtrados['Data Cadastro'].dt.year
                nome_grupo = dados_filtrados['Grupo Cliente'].iloc[0]
                total_lojas = dados_filtrados['Codigo Cliente'].nunique()

                st.markdown(f"## 📍 Grupo Cliente: {nome_grupo} | 🏬 Lojas: {total_lojas}")

                rfv_resultado = calcular_rfv_individual(dados_filtrados)
                colrfv1, colrfv2, colrfv3, colrfv4, colrfv5 = st.columns(5)

                for col, label, value in zip(
                    [colrfv1, colrfv2, colrfv3, colrfv4, colrfv5],
                    ['Recência (dias)', 'Frequência', 'Valor Total (R$)', 'RFV Score', 'Classificação'],
                    [rfv_resultado['Recência (dias)'], rfv_resultado['Frequência (pedidos únicos)'], rfv_resultado['Valor Total (R$)'], rfv_resultado['RFV Score'], rfv_resultado['Classificação']]
                ):
                    col.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{label}</div>
                            <div class="metric-value">{value}</div>
                        </div>
                    """, unsafe_allow_html=True)

                # KPIs
                ultima_data_compra = dados_filtrados['Data Ultima Compra'].max()
                ultima_compra = ultima_data_compra.strftime('%d/%m/%Y') if pd.notnull(ultima_data_compra) else 'Sem compras'

                primeira_data = dados_filtrados['Data Cadastro'].min()
                ultima_data = dados_filtrados['Data Cadastro'].max()
                periodo_analise = f"{primeira_data.strftime('%d/%m/%Y')} até {ultima_data.strftime('%d/%m/%Y')}"

                vendas_totais = dados_filtrados['Qtd Venda'].sum()
                melhor_mes_num = dados_filtrados['Data Cadastro'].dt.month.mode()[0]
                melhor_mes_nome = meses_portugues.get(melhor_mes_num, 'Mês inválido')

                col1, col2, col3 = st.columns(3)
                for col, label, value in zip(
                    [col1, col2, col3],
                    ['📅 Última Compra', '🕒 Período da Análise', '📈 Melhor Mês para Oferta'],
                    [ultima_compra, periodo_analise, melhor_mes_nome]
                ):
                    col.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{label}</div>
                            <div class="metric-value">{value}</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.success(f"📦 Total de Itens Vendidos: {vendas_totais:,} unidades")

                # TOP 10 LINHAS
                total_vendas_linha = dados_filtrados.groupby(['Codigo Linha', 'Linha'])['Qtd Venda'].sum().reset_index(name='Quantidade Vendida')
                top_linhas = total_vendas_linha.sort_values(by='Quantidade Vendida', ascending=False).head(10)

                st.markdown("👉 **🔮 Top 10 Linhas Preditivas para Ofertar:**")
                st.table(top_linhas)

                fig_top_linhas = px.bar(
                    top_linhas,
                    x='Linha',
                    y='Quantidade Vendida',
                    color='Linha',
                    text='Quantidade Vendida',
                    title='🎯 Top 10 Linhas Mais Vendidas'
                )
                fig_top_linhas.update_traces(textposition='outside')
                st.plotly_chart(fig_top_linhas)

                # MACHINE LEARNING
                st.subheader("🤖 Previsão de Linhas para Oferta (Machine Learning)")
                progress_bar = st.progress(0)

                dados_ml = df.copy()
                dados_ml['Mes Pedido'] = dados_ml['Data Cadastro'].dt.month
                dados_ml['Compra'] = dados_ml['Qtd Venda'].apply(lambda x: 1 if x > 0 else 0)

                le_grupo = LabelEncoder().fit(dados_ml['Codigo Grupo Cliente'])
                le_cliente = LabelEncoder().fit(dados_ml['Codigo Cliente'])
                le_linha = LabelEncoder().fit(dados_ml['Linha'])

                dados_ml['Grupo_Code'] = le_grupo.transform(dados_ml['Codigo Grupo Cliente'])
                dados_ml['Cliente_Code'] = le_cliente.transform(dados_ml['Codigo Cliente'])
                dados_ml['Linha_Code'] = le_linha.transform(dados_ml['Linha'])

                X = dados_ml[['Grupo_Code', 'Cliente_Code', 'Linha_Code', 'Mes Pedido']]
                y = dados_ml['Compra']

                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                modelo_rf = RandomForestClassifier(n_estimators=100, random_state=42)
                modelo_rf.fit(X_train, y_train)

                acc = accuracy_score(y_test, modelo_rf.predict(X_test))
                st.info(f"🔎 Acurácia do Modelo: {acc:.2%}")

                grupo_id = codigo_grupo_cliente or dados_filtrados['Codigo Grupo Cliente'].iloc[0]
                cliente_id = codigo_cliente or dados_filtrados['Codigo Cliente'].iloc[0]

                linhas_possiveis = df['Linha'].unique()
                mes_atual = datetime.now().month

                dados_para_prever = pd.DataFrame({
                    'Grupo_Code': le_grupo.transform([grupo_id] * len(linhas_possiveis)),
                    'Cliente_Code': le_cliente.transform([cliente_id] * len(linhas_possiveis)),
                    'Linha_Code': le_linha.transform(linhas_possiveis),
                    'Mes Pedido': [mes_atual] * len(linhas_possiveis)
                })

                probs = modelo_rf.predict_proba(dados_para_prever)[:, 1]

                df_preds = pd.DataFrame({
                    'Linha': linhas_possiveis,
                    'Probabilidade de Compra': probs
                }).sort_values(by='Probabilidade de Compra', ascending=False)

                st.table(df_preds.head(10))

                # GRÁFICOS ANALÍTICOS
                st.subheader("📊 Gráficos Analíticos do Período Selecionado")

                fig1 = px.bar(dados_filtrados.groupby('Ano')['Qtd Venda'].sum().reset_index(), x='Ano', y='Qtd Venda', color='Ano', text='Qtd Venda', title="📦 Quantidade Vendida por Ano")
                fig2 = px.bar(dados_filtrados.groupby('Ano')['Codigo Cliente'].nunique().reset_index(name='Quantidade de Pedidos'), x='Ano', y='Quantidade de Pedidos', color='Ano', text='Quantidade de Pedidos', title="📝 Quantidade de Pedidos por Ano")
                fig3 = px.bar(dados_filtrados.groupby('Ano')['Preço Médio Produto'].mean().reset_index(), x='Ano', y='Preço Médio Produto', color='Ano', text='Preço Médio Produto', title="💰 Preço Médio dos Produtos por Ano")
                fig4 = px.bar(dados_filtrados.groupby('Ano')['Vlr Venda'].sum().reset_index(), x='Ano', y='Vlr Venda', color='Ano', text='Vlr Venda', title="💸 Valores Vendidos por Ano")

                top10_periodo = dados_filtrados.groupby('Linha')['Qtd Venda'].sum().reset_index().sort_values(by='Qtd Venda', ascending=False).head(10)
                fig5 = px.bar(top10_periodo, x='Linha', y='Qtd Venda', color='Linha', text='Qtd Venda', title="🏆 Top 10 Linhas Mais Vendidas no Período")

                for fig in [fig1, fig2, fig3, fig4, fig5]:
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig)
                # 🔐 Armazena resultados no session_state para uso posterior (como PDF)
                st.session_state['pdf_ready'] = True
                st.session_state['dados_filtrados'] = dados_filtrados
                st.session_state['rfv_resultado'] = rfv_resultado
                st.session_state['top_linhas'] = top_linhas
                st.session_state['nome_grupo'] = nome_grupo
                st.session_state['total_lojas'] = total_lojas
                st.session_state['periodo_analise'] = periodo_analise
                st.session_state['ultima_compra'] = ultima_compra
                st.session_state['fig1'] = fig1
                st.session_state['fig2'] = fig2
                st.session_state['fig3'] = fig3
                st.session_state['fig4'] = fig4
                st.session_state['fig5'] = fig5



# Gerar PDF
if st.session_state.get("pdf_ready", False):
    st.subheader("📄 Exportar Relatório em PDF")
    gerar_pdf = st.button("📥 Gerar Relatório PDF")

    if gerar_pdf:
        with st.spinner("🧾 Gerando relatório..."):
            st.write("Iniciando a geração do relatório...")

            # Função para salvar gráfico com verificação
            def salvar_grafico(fig, nome):
                import tempfile
                import os
                import plotly.io as pio

                st.write(f"Verificando gráfico: {nome}")  # Verificando o gráfico sendo processado

                if not fig.data:
                    st.warning(f"⚠️ O gráfico '{nome}' está vazio e não será incluído no relatório.")
                    return None

                try:
                    caminho = os.path.join(tempfile.gettempdir(), f"{nome}.png")
                    fig.write_image(caminho, format="png", engine="kaleido", scale=2)
                    st.write(f"Gráfico {nome} salvo com sucesso!")
                    return caminho
                except Exception as e:
                    st.error(f"❌ Erro ao salvar gráfico '{nome}': {e}")
                    return None


            # Início do PDF
            st.write("Iniciando o processo de criação do PDF...")  # Marca o início do processo do PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(230, 0, 18)
            pdf.cell(0, 10, "Relatório Preditivo Kidy", ln=True)

            pdf.set_font("Arial", size=12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, f"Grupo Cliente: {st.session_state['nome_grupo']}", ln=True)
            pdf.cell(0, 10, f"Lojas Atendidas: {st.session_state['total_lojas']}", ln=True)
            pdf.cell(0, 10, f"Período Analisado: {st.session_state['periodo_analise']}", ln=True)
            pdf.cell(0, 10, f"Última Compra: {st.session_state['ultima_compra']}", ln=True)
            pdf.ln(10)

            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Métricas RFV", ln=True)
            pdf.set_font("Arial", size=12)
            for key, val in st.session_state['rfv_resultado'].items():
                pdf.cell(0, 10, f"{key}: {val}", ln=True)
            pdf.ln(10)

            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Top 10 Linhas Vendidas", ln=True)
            pdf.set_font("Arial", size=12)
            for _, row in st.session_state['top_linhas'].iterrows():
                pdf.cell(0, 10, f"{row['Linha']}: {int(row['Quantidade Vendida'])} unidades", ln=True)
            pdf.ln(10)

            # Gráficos
            graficos = [
                st.session_state['fig1'], st.session_state['fig2'],
                st.session_state['fig3'], st.session_state['fig4'], st.session_state['fig5']
            ]
            nomes = ["vendas_ano", "pedidos_ano", "preco_medio", "valores_vendidos", "top10_linhas"]

            st.info("📊 Iniciando salvamento dos gráficos para PDF...")

            for fig, nome in zip(graficos, nomes):
                st.write(f"📊 Salvando gráfico: {nome}")
                path = salvar_grafico(fig, nome)
                if path:
                    pdf.add_page()
                    pdf.image(path, x=10, y=20, w=190)
                else:
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(0, 10, f"[Gráfico ausente ou inválido: {nome}]", ln=True)

            # Finalizar PDF
            caminho_pdf = os.path.join(tempfile.gettempdir(), "relatorio_preditivo_kidy.pdf")
            pdf.output(caminho_pdf)

            with open(caminho_pdf, "rb") as f:
                st.download_button(
                    label="📥 Baixar Relatório PDF",
                    data=f,
                    file_name="relatorio_preditivo_kidy.pdf",
                    mime="application/pdf"
                )

            st.success("✅ Relatório gerado com sucesso!")
                
# RODAPÉ
st.sidebar.markdown("---")
st.sidebar.caption(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.markdown("Desenvolvido por Kidy Data Team 🚀")
