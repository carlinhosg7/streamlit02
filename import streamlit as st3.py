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
import unicodedata

# 🔐 FUNÇÃO DE AUTENTICAÇÃO
def autenticar_usuario_excel(caminho_arquivo):
    try:
        df_usuarios = pd.read_excel(caminho_arquivo, engine="openpyxl")

        # Normaliza os nomes das colunas
        df_usuarios.columns = [
            unicodedata.normalize('NFKD', col).encode('ascii', errors='ignore').decode('utf-8').strip().lower().replace(" ", "_")
            for col in df_usuarios.columns
        ]

        # Converte os dados para string
        df_usuarios['usuario'] = df_usuarios['usuario'].apply(lambda x: str(x).strip())
        df_usuarios['senha'] = df_usuarios['senha'].astype(str).str.strip()

        # Inicializa autenticação
        st.session_state['autenticado'] = st.session_state.get('autenticado', False)

        if not st.session_state['autenticado']:
            with st.sidebar:
                st.markdown("### 🔐 Login")
                usuario = st.text_input("Usuário").strip()
                senha = st.text_input("Senha", type="password").strip()

                if st.button("Entrar"):
                    if usuario in df_usuarios['usuario'].values:
                        senha_valida = df_usuarios[df_usuarios['usuario'] == usuario]['senha'].values[0]
                        if senha == senha_valida:
                            st.session_state['autenticado'] = True
                            st.session_state['codigo_representante'] = usuario  # <-- Adicione esta linha
                            st.success("✅ Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Senha incorreta.")  

        if not st.session_state['autenticado']:
            st.stop()

    except Exception as e:
        st.error(f"Erro ao carregar planilha de autenticação: {e}")
        st.stop()

# 🎨 CONFIG PÁGINA (PRIMEIRA CHAMADA DO STREAMLIT)
st.set_page_config(
    page_title="Dashboard Analítico",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🚀 SÓ DEPOIS AUTENTICAÇÃO
autenticar_usuario_excel("auth.xlsx")


st.title("🔓 Dashboard liberado após login")

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
st.image(logo_kidy, width=150)

# DICIONÁRIO MESES
meses_portugues = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# URLS DOS ARQUIVOS
URLS_DADOS = [
    "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/DADOS_PREDITIVA_1.csv",
    "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/DADOS_PREDITIVA_2.csv",
    "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/DADOS_PREDITIVA_3.csv",
    "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/DADOS_PREDITIVA_4.csv"
]

@st.cache_data(ttl=3600)
def carregar_dados_processados():
    try:
        # Lê os 4 arquivos com codificação Windows
        dfs = [pd.read_csv(url, encoding='cp1252', sep=';') for url in URLS_DADOS]
        df = pd.concat(dfs, ignore_index=True)

        # Padronizações
        df['Codigo Representante'] = df['Codigo Representante'].astype(str).str.strip().str.lstrip('0')
        df['Data Cadastro'] = pd.to_datetime(df['Data Cadastro'], errors='coerce')
        df['Data Ultima Compra'] = pd.to_datetime(df['Data Ultima Compra'], errors='coerce')
        df['Codigo Grupo Cliente'] = df['Codigo Grupo Cliente'].astype(str).str.upper()
        df['Codigo Cliente'] = df['Codigo Cliente'].astype(str).str.upper()
        
        # Converte colunas de valores para número
        df['Vlr Venda'] = pd.to_numeric(df['Vlr Venda'], errors='coerce')
        df['Qtd Venda'] = pd.to_numeric(df['Qtd Venda'], errors='coerce')

        # Calcula Preço Médio Produto com segurança
        df['Preço Médio Produto'] = df.apply(
            lambda row: row['Vlr Venda'] / row['Qtd Venda'] if pd.notnull(row['Qtd Venda']) and row['Qtd Venda'] > 0 else 0,
            axis=1
        )


        # Filtro por representante logado
        codigo_representante = str(st.session_state.get('codigo_representante', '')).strip().lower().lstrip('0')
        if codigo_representante and codigo_representante != 'admin':
            df = df[df['Codigo Representante'] == codigo_representante]

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


        # 🚨 AQUI ENTRA A LÓGICA DE PERFIL ADMIN
        codigo_representante = str(st.session_state.get('codigo_representante', '')).strip().lower().lstrip('0')
        if codigo_representante and codigo_representante != 'admin':
            df = df[df['Codigo Representante'] == codigo_representante]

        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()
        # sse bloco vai exibir um aviso claro no topo do dashboard, indicando se o usuário está como admin (vendo tudo) ou mostrando o código do representante comum.
        codigo_representante_logado = st.session_state.get('codigo_representante', '')
        if str(codigo_representante_logado).strip().lower() == 'admin':
            st.markdown("🟢 **Modo Admin: Visualizando todos os dados**")
        else:
            st.markdown(f"🆔 **Representante:** {codigo_representante_logado}")


# RFV SCORE
def calcular_rfv_individual(dados_filtrados):
    hoje = datetime.today()

    recencia = (hoje - dados_filtrados['Data Ultima Compra'].max()).days if pd.notnull(dados_filtrados['Data Ultima Compra'].max()) else 999
    frequencia = dados_filtrados['Data Cadastro'].nunique()
    valor = dados_filtrados['Vlr Venda'].sum()

    recencia_score = 5 if recencia <= 60 else 4 if recencia <= 120 else 3 if recencia <= 180 else 2 if recencia <= 365 else 1
    frequencia_score = 5 if frequencia >= 7 else 4 if frequencia >= 6 else 3 if frequencia >= 4 else 2 if frequencia >= 2 else 1
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

# Opções formatadas para busca com nome
opcoes_grupo_cliente = df[['Codigo Grupo Cliente', 'Grupo Cliente']].drop_duplicates()
opcoes_grupo_cliente['Busca'] = opcoes_grupo_cliente['Codigo Grupo Cliente'] + ' - ' + opcoes_grupo_cliente['Grupo Cliente']
busca_grupo = st.sidebar.selectbox("🔍 Buscar Grupo Cliente:", [''] + sorted(opcoes_grupo_cliente['Busca'].tolist()))

opcoes_cliente = df[['Codigo Cliente', 'Razao Social']].drop_duplicates()
opcoes_cliente['Busca'] = opcoes_cliente['Codigo Cliente'] + ' - ' + opcoes_cliente['Razao Social']
busca_cliente = st.sidebar.selectbox("🔍 Buscar Cliente:", [''] + sorted(opcoes_cliente['Busca'].tolist()))

# Extrair apenas os códigos selecionados
codigo_grupo_cliente = busca_grupo.split(' - ')[0].strip().upper() if busca_grupo else ''
codigo_cliente = busca_cliente.split(' - ')[0].strip().upper() if busca_cliente else ''

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

                # Mapeamento dos supervisores
                mapa_supervisores = {
                    '9902': 'Centro Oeste',
                    '9907': 'Sul',
                    '9914': 'Norte / Nordeste',
                    '9915': 'REM',
                    '9916': 'SPC',
                    '9917': 'SPI'
                }

                # Extrai representantes únicos do grupo selecionado nos dados filtrados
                cods_representantes = dados_filtrados['Codigo Representante'].astype(str).dropna().unique()
                cods_representantes = sorted(cods_representantes)
                cods_repr_str = ', '.join(cods_representantes)

                # Extrai código(s) de supervisor dos dados filtrados
                cod_supervisor = dados_filtrados['Codigo Supervisor'].astype(str).dropna().unique()
                nome_supervisor = mapa_supervisores.get(cod_supervisor[0], 'Desconhecido') if len(cod_supervisor) > 0 else 'Desconhecido'

                # Exibe o(s) representantes do grupo selecionado
                st.markdown(
                    f"## 📍 Grupo Cliente: {nome_grupo} | 🏬 Lojas: {total_lojas} | 🆔 Representante(s): {cods_repr_str}"
                )
                st.markdown(f"#### 🧑‍💼 Supervisor: {nome_supervisor}")



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
                
                # --- ANÁLISE DAS 3 ÚLTIMAS COLEÇÕES (INCLUINDO VIGENTE) ---
                st.markdown("### 👟 Vendas das 3 Últimas Coleções (Pares e Valores)")

                from datetime import datetime

                # 🔁 Função para identificar a coleção com base na nova regra
                def identificar_colecao(data):
                    if pd.isnull(data):
                        return None
                    mes = data.month
                    ano = data.year

                    if 5 <= mes <= 10:  # Verão: maio a outubro
                        return f"Verão {ano}"
                    elif 11 <= mes <= 12:  # Inverno: novembro e dezembro → pertence ao ano seguinte
                        return f"Inverno {ano + 1}"
                    else:  # Inverno: janeiro a abril → permanece no mesmo ano
                        return f"Inverno {ano}"

                # 📆 Determina a coleção vigente com base na data atual
                hoje = datetime.today()
                mes = hoje.month
                ano = hoje.year

                if 5 <= mes <= 10:
                    colecao_vigente = f"Verão {ano}"
                elif 11 <= mes <= 12:
                    colecao_vigente = f"Inverno {ano + 1}"
                else:
                    colecao_vigente = f"Inverno {ano}"
               
                # ✅ Aplica a classificação de coleção
                dados_filtrados['Colecao'] = dados_filtrados['Data Cadastro'].apply(identificar_colecao)

                # 📊 Agrupamento por coleção com data mínima e máxima
                vendas_colecao = dados_filtrados.groupby('Colecao').agg({
                    'Qtd Venda': 'sum',
                    'Vlr Venda': 'sum',
                    'Data Cadastro': ['min', 'max']
                }).reset_index()

                # Renomeia colunas após agregação múltipla
                vendas_colecao.columns = ['Colecao', 'Qtd Venda', 'Vlr Venda', 'Data Inicial', 'Data Final']

                # 🔢 Extrai o ano da coleção
                vendas_colecao['Ano'] = vendas_colecao['Colecao'].str.extract(r'(\d{4})').astype(int)

                # ✅ Garante presença da coleção vigente
                if colecao_vigente not in vendas_colecao['Colecao'].values:
                    linha_vigente = pd.DataFrame({
                        'Colecao': [colecao_vigente],
                        'Qtd Venda': [0],
                        'Vlr Venda': [0.0],
                        'Data Inicial': [hoje],
                        'Data Final': [hoje],
                        'Ano': [int(colecao_vigente.split()[1])]
                    })
                    vendas_colecao = pd.concat([linha_vigente, vendas_colecao], ignore_index=True)

                # 🔝 Seleciona as 3 últimas coleções mais recentes com base na Data Final
                colecoes_exibir = vendas_colecao.copy()
                colecoes_exibir['Data Final'] = pd.to_datetime(colecoes_exibir['Data Final'])
                colecoes_exibir = colecoes_exibir.sort_values(by='Data Final', ascending=False).drop_duplicates('Colecao').head(3)

                # 💰 Formata os campos
                colecoes_exibir['Pares Vendidos'] = colecoes_exibir['Qtd Venda'].astype(int)
                colecoes_exibir['Valor Vendido (R$)'] = colecoes_exibir['Vlr Venda'].apply(
                    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )
                colecoes_exibir['Período da Coleta'] = colecoes_exibir.apply(
                    lambda row: f"{row['Data Inicial'].strftime('%d/%m/%Y')} a {row['Data Final'].strftime('%d/%m/%Y')}", axis=1
                )

                # Seleciona e renomeia colunas finais
                colecoes_exibir = colecoes_exibir[['Colecao', 'Pares Vendidos', 'Valor Vendido (R$)', 'Período da Coleta']]
                colecoes_exibir.columns = ['Coleção', 'Pares Vendidos', 'Valor Vendido (R$)', 'Período da Coleta']

                # 📋 Exibe na interface
                st.table(colecoes_exibir)






                # TOP 10 LINHAS
                total_vendas_linha = dados_filtrados.groupby(['Codigo Linha', 'Linha'])['Qtd Venda'].sum().reset_index(name='Quantidade Vendida')
                top_linhas = total_vendas_linha.sort_values(by='Quantidade Vendida', ascending=False).head(10)

                st.markdown("👉 **🔮 Top 10 Linhas linhas mais compradas pelo cliente:**")
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

                # Inicializa a barra de progresso
                progress_bar = st.progress(0, text="⏳ Preparando dados para ML (0%)")

                # Etapa 1: preparar dados
                @st.cache_data(ttl=600)
                def preparar_dados_ml(df):
                    df_ml = df.copy()
                    df_ml['Mes Pedido'] = df_ml['Data Cadastro'].dt.month
                    df_ml['Compra'] = df_ml['Qtd Venda'].apply(lambda x: 1 if x > 0 else 0)
                    return df_ml

                dados_ml = preparar_dados_ml(df)
                progress_bar.progress(20, text="✅ Etapa 1: Dados preparados (20%)")

                # Etapa 2: Treinar modelo
                @st.cache_resource
                def treinar_modelo_rf(df_ml):
                    le_grupo = LabelEncoder().fit(df_ml['Codigo Grupo Cliente'])
                    le_cliente = LabelEncoder().fit(df_ml['Codigo Cliente'])
                    le_linha = LabelEncoder().fit(df_ml['Linha'])

                    df_ml['Grupo_Code'] = le_grupo.transform(df_ml['Codigo Grupo Cliente'])
                    df_ml['Cliente_Code'] = le_cliente.transform(df_ml['Codigo Cliente'])
                    df_ml['Linha_Code'] = le_linha.transform(df_ml['Linha'])

                    X = df_ml[['Grupo_Code', 'Cliente_Code', 'Linha_Code', 'Mes Pedido']]
                    y = df_ml['Compra']

                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
                    modelo.fit(X_train, y_train)
                    acc = accuracy_score(y_test, modelo.predict(X_test))

                    return modelo, le_grupo, le_cliente, le_linha, acc

                modelo_rf, le_grupo, le_cliente, le_linha, acc = treinar_modelo_rf(dados_ml)
                progress_bar.progress(50, text="✅ Etapa 2: Modelo treinado (50%)")

#######

                 # 🧾 Comparativo de Linhas - Somente Não Compradas
                st.markdown("### 🧾 Linhas que o Cliente Ainda Não Comprou")

                # 🔽 Carrega CSV com as linhas possíveis
                URL_LINHAS = "https://raw.githubusercontent.com/carlinhosg7/streamlit02/refs/heads/main/DADOS_PREDITIVA_LINHAS.csv"
                linhas_possiveis = pd.read_csv(URL_LINHAS, encoding="latin1", sep=";")

                # 🧹 Normaliza os nomes das colunas
                linhas_possiveis.columns = [col.strip().lower().replace(" ", "_") for col in linhas_possiveis.columns]

                # 🔁 Remove duplicadas por linha
                linhas_possiveis = linhas_possiveis.drop_duplicates(subset=["linha"])

                # ✅ Linhas compradas pelo cliente no período
                linhas_compradas = dados_filtrados[dados_filtrados["Qtd Venda"] > 0]["Linha"].unique()
                linhas_nao_compradas = linhas_possiveis[~linhas_possiveis["linha"].isin(linhas_compradas)]

                # 🧠 Armazena para uso no PDF
                st.session_state["linhas_nao_compradas"] = linhas_nao_compradas[["codigo_linha", "linha"]]

                
                # 🧾 Exibir apenas código da linha e nome da linha
                st.dataframe(
                    linhas_nao_compradas[["codigo_linha", "linha"]].sort_values(by="linha")
                )

                st.info(f"🧠 Acurácia do modelo: {acc:.2%}")
                
                # Etapa 3: Preparar dados para predição
                grupo_id = codigo_grupo_cliente or dados_filtrados['Codigo Grupo Cliente'].iloc[0]
                cliente_id = codigo_cliente or dados_filtrados['Codigo Cliente'].iloc[0]
                linhas_possiveis = df['Linha'].unique()
                mes_atual = datetime.now().month

                try:
                    dados_para_prever = pd.DataFrame({
                        'Grupo_Code': le_grupo.transform([grupo_id] * len(linhas_possiveis)),
                        'Cliente_Code': le_cliente.transform([cliente_id] * len(linhas_possiveis)),
                        'Linha_Code': le_linha.transform(linhas_possiveis),
                        'Mes Pedido': [mes_atual] * len(linhas_possiveis)
                    })
                    progress_bar.progress(70, text="✅ Etapa 3: Dados para predição gerados (70%)")

                    probs = modelo_rf.predict_proba(dados_para_prever)[:, 1]

                    df_preds = pd.DataFrame({
                        'Linha': linhas_possiveis,
                        'Probabilidade de Compra': probs
                    }).sort_values(by='Probabilidade de Compra', ascending=False)

                    progress_bar.progress(100, text="✅ Etapa 4: Predição finalizada (100%)")

                    st.success("🎉 Predição realizada com sucesso!")
                    st.table(df_preds.head(10))

                except ValueError as e:
                    st.warning(f"⚠️ Erro ao prever: {e}. Verifique se o código do cliente ou grupo existe nos dados.")
                    progress_bar.progress(0, text="❌ Erro durante a predição.")

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

            # Função para salvar gráfico com tema colorido
            def salvar_grafico(fig, nome):
                import tempfile
                import os
                import plotly.io as pio
                import plotly.graph_objects as go

                st.write(f"Verificando gráfico: {nome}")

                if not fig.data:
                    st.warning(f"⚠️ O gráfico '{nome}' está vazio e não será incluído no relatório.")
                    return None

                try:
                    # Cria uma nova figura limpa com os mesmos dados
                    nova_fig = go.Figure(data=fig.data)

                    # Reaplica os eixos e layout com estilo claro e fundo branco
                    nova_fig.update_layout(
                        template="plotly_white",
                        title=fig.layout.title,
                        xaxis=fig.layout.xaxis,
                        yaxis=fig.layout.yaxis,
                        font=dict(color="black", size=14),
                        paper_bgcolor="white",
                        plot_bgcolor="white"
                    )

                    caminho = os.path.join(tempfile.gettempdir(), f"{nome}.png")
                    nova_fig.write_image(caminho, format="png", engine="kaleido", scale=2)
                    st.write(f"✅ Gráfico {nome} exportado com sucesso!")
                    return caminho

                except Exception as e:
                    st.error(f"❌ Erro ao salvar gráfico '{nome}': {e}")
                    return None


            # Início do PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(230, 0, 18)
            pdf.cell(0, 10, "Relatório Preditivo Kidy", ln=True)

            pdf.set_font("Arial", size=12)
            pdf.set_text_color(0, 0, 0)
            # Mapeamento dos supervisores (mesmo dicionário do app)
            mapa_supervisores = {
                '9902': 'Centro Oeste',
                '9907': 'Sul',
                '9914': 'Norte / Nordeste',
                '9915': 'REM',
                '9916': 'SPC',
                '9917': 'SPI'
            }

            # Buscar nome do supervisor para PDF
            df_supervisor = st.session_state['dados_filtrados']
            cod_supervisor = df_supervisor['Codigo Supervisor'].astype(str).dropna().unique()
            nome_supervisor = mapa_supervisores.get(cod_supervisor[0], 'Desconhecido') if len(cod_supervisor) > 0 else 'Desconhecido'

            # Cabeçalho PDF com Supervisor
            pdf.cell(0, 10, f"Grupo Cliente: {st.session_state['nome_grupo']}", ln=True)
            pdf.cell(0, 10, f"Lojas Atendidas: {st.session_state['total_lojas']}", ln=True)
            pdf.cell(0, 10, f"Supervisor: {nome_supervisor}", ln=True)
            pdf.cell(0, 10, f"Período Analisado: {st.session_state['periodo_analise']}", ln=True)
            pdf.cell(0, 10, f"Última Compra: {st.session_state['ultima_compra']}", ln=True)

            # RFV
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Métricas RFV", ln=True)
            pdf.set_font("Arial", size=12)
            for key, val in st.session_state['rfv_resultado'].items():
                pdf.cell(0, 10, f"{key}: {val}", ln=True)
            pdf.ln(10)

            # COLEÇÕES
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Vendas das 3 Últimas Coleções", ln=True)
            pdf.set_font("Arial", size=12)

            df_colecoes = st.session_state['dados_filtrados'].copy()

            def identificar_colecao_pdf(data):
                if pd.isnull(data):
                    return None
                ano = data.year
                if 5 <= data.month <= 10:
                    return f"Verão {ano}"
                elif data.month >= 11:
                    return f"Inverno {ano + 1}"
                else:
                    return f"Inverno {ano}"

            df_colecoes['Colecao'] = df_colecoes['Data Cadastro'].apply(identificar_colecao_pdf)
            colecao_vigente = identificar_colecao_pdf(datetime.today())

            vendas_colecao = df_colecoes.groupby('Colecao').agg({
                'Qtd Venda': 'sum',
                'Vlr Venda': 'sum'
            }).reset_index()

            vendas_colecao['Ano'] = vendas_colecao['Colecao'].str.extract(r'(\d{4})').astype(int)
            vendas_colecao = vendas_colecao.sort_values(by='Ano', ascending=False)

            if colecao_vigente not in vendas_colecao['Colecao'].values:
                linha_vigente = pd.DataFrame({
                    'Colecao': [colecao_vigente],
                    'Qtd Venda': [0],
                    'Vlr Venda': [0.0],
                    'Ano': [int(colecao_vigente.split()[1])]
                })
                vendas_colecao = pd.concat([linha_vigente, vendas_colecao], ignore_index=True)

            colecoes_pdf = vendas_colecao.drop(columns='Ano').drop_duplicates('Colecao').head(3)

            for _, row in colecoes_pdf.iterrows():
                nome = row['Colecao']
                pares = int(row['Qtd Venda'])
                valor = f"R$ {row['Vlr Venda']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                pdf.cell(0, 10, f"{nome} - {pares} pares - {valor}", ln=True)
            pdf.ln(10)

            # TOP 10 LINHAS
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Top 10 Linhas Vendidas", ln=True)
            pdf.set_font("Arial", size=12)
            for _, row in st.session_state['top_linhas'].iterrows():
                pdf.cell(0, 10, f"{row['Linha']}: {int(row['Quantidade Vendida'])} unidades", ln=True)
            pdf.ln(10)

            # ➕ Tabela de Linhas Não Compradas
            if "linhas_nao_compradas" in st.session_state:
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "Linhas que o Cliente Ainda Não Comprou", ln=True)
                pdf.set_font("Arial", size=12)

                for _, row in st.session_state["linhas_nao_compradas"].iterrows():
                    cod = str(row["codigo_linha"])
                    nome = str(row["linha"])
                    pdf.cell(0, 10, f"{cod} - {nome}", ln=True)

                pdf.ln(10)



            # GRÁFICOS
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

            # FINALIZAÇÃO
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
