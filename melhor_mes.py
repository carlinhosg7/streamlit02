# ----------------------------
# ✅ IMPORTS
# ----------------------------
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
import kaleido  # força o loading do kaleido para evitar erro de exportação
import unicodedata
import numpy as np
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import requests
from io import BytesIO
from docx.shared import RGBColor
from docx.shared import Pt
from docx.shared import RGBColor, Pt
import io


pio.kaleido.scope.default_format = "png"

# ----------------------------
# ✅ CONFIGURAÇÃO INICIAL DA PÁGINA (PRIMEIRO COMANDO DO STREAMLIT)
# ----------------------------
st.set_page_config(
    page_title="Dashboard Analítico",
    page_icon="https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/logo_kidy_icon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# 🖼️ CARREGA LOGO DA KIDY A PARTIR DO GITHUB
# ----------------------------
url_logo = "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/logo_kidy.png"
response = requests.get(url_logo)
logo_kidy = Image.open(BytesIO(response.content))

# ----------------------------
# 📊 TÍTULO E SIDEBAR
# ----------------------------
st.title("📊 Previsão de Clientes")
st.sidebar.image(logo_kidy, width=100)
st.sidebar.header("🔧 Filtros de Análise")


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

# LOGO KIDY (a partir do GitHub)
url_logo = "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/logo_kidy.png"
response = requests.get(url_logo)
logo_kidy = Image.open(BytesIO(response.content))
st.image(logo_kidy, width=150)


# DICIONÁRIO MESES
meses_portugues = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
# URLS DOS ARQUIVOS
URLS_DADOS = [
    "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/DADOS_PREDITIVA_1.csv.gz",
    "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/DADOS_PREDITIVA_2.csv.gz",
    "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/DADOS_PREDITIVA_3.csv.gz",
    "https://raw.githubusercontent.com/carlinhosg7/streamlit02/main/DADOS_PREDITIVA_4.csv.gz"
]
# Carregamento dos dados
df = pd.concat([
    pd.read_csv(url, compression='gzip', encoding='latin1', sep=';')
    for url in URLS_DADOS
], ignore_index=True)

# 🔍 Limpeza avançada
df = df[df['Codigo Cliente'].notna()]  # Remove NaN puros

# Remove linhas onde o campo 'Codigo Cliente' está como string 'nan' ou similar
df = df[~df['Codigo Cliente'].astype(str).str.strip().str.lower().isin(['nan', '', 'total geral'])]

# Remove linhas onde o campo 'Razao Social' contém valores inválidos
df = df[~df['Razao Social'].astype(str).str.upper().str.contains('RAZAO SOCIAL|TOTAL GERAL|DATA CADASTRO|CÓDIGO SUPERVISOR|TIPO PEDIDO', na=False)]



@st.cache_data(ttl=3600)
def carregar_dados_processados():
    try:
        dfs = [
            pd.read_csv(
                url,
                encoding='latin1',       # Corrige erro de encoding
                sep=';',
                compression='gzip',
                low_memory=False,
                dtype={'Prazo Medio': str}  # Evita erro de tipo misto na coluna 12
            )
            for url in URLS_DADOS
        ]
        df = pd.concat(dfs, ignore_index=True)

        # Converte colunas para tipos eficientes
        df['Codigo Representante'] = df['Codigo Representante'].astype(str).str.strip().str.lstrip("0").astype("category")
        df['Codigo Supervisor'] = df['Codigo Supervisor'].astype(str).str.strip().astype("category")
        df['Codigo Grupo Cliente'] = df['Codigo Grupo Cliente'].astype(str).str.upper().astype("category")
        df['Codigo Cliente'] = df['Codigo Cliente'].astype(str).str.upper().astype("category")
        df['Grupo Cliente'] = df['Grupo Cliente'].astype(str).str.strip().astype("category")
        df['Razao Social'] = df['Razao Social'].astype(str).str.strip().astype("category")
        df['Linha'] = df['Linha'].astype(str).str.strip().astype("category")

        df['Data Cadastro'] = pd.to_datetime(df['Data Cadastro'], errors='coerce')
        df['Data Ultima Compra'] = pd.to_datetime(df['Data Ultima Compra'], errors='coerce')

        df['Qtd Venda'] = pd.to_numeric(df['Qtd Venda'], errors='coerce').fillna(0).astype('int32')
        df['Vlr Venda'] = pd.to_numeric(df['Vlr Venda'], errors='coerce').fillna(0).astype('float32')

        # Cálculo vetorizado sem apply
        df['Preço Médio Produto'] = df['Vlr Venda'] / df['Qtd Venda'].replace(0, pd.NA)
        df['Preço Médio Produto'] = df['Preço Médio Produto'].fillna(0).round(2)

        # 🚨 Lógica de perfil
        codigo_representante = str(st.session_state.get('codigo_representante', '')).strip().lower().lstrip('0')
        if codigo_representante and codigo_representante != 'admin':
            df = df[df['Codigo Representante'] == codigo_representante]
            st.markdown(f"🆔 **Representante:** `{codigo_representante.upper()}`")
        else:
            st.markdown("🟢 **Modo Admin: Visualizando todos os dados**")

        return df

    except Exception as e:
        import traceback
        st.error("❌ Erro ao carregar dados:")
        st.code(traceback.format_exc())
        return pd.DataFrame()



# CARREGA DADOS
df = carregar_dados_processados()

if df.empty:
    st.stop()

# ===============================
# 🔮 CLIENTES COM MAIOR PROPENSÃO DE COMPRA
# ===============================
st.sidebar.markdown("### 🔮 Propensão de Compra")

# Lista fixa com nomes dos meses em português
nomes_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
               'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

# Seleção de meses (por nome)
meses_escolhidos = st.sidebar.multiselect(
    "Selecione 2 ou 3 meses:",
    nomes_meses,
    max_selections=3,
    key="multiselect_meses_propensao"
)


# Mapeamento para número do mês
mapa_mes_num = {nome: idx for idx, nome in enumerate(nomes_meses, start=1)}

# Botão com chave única
if st.sidebar.button("📊 Ver Clientes com Propensão", key="btn_propensao"):
    
    if len(meses_escolhidos) not in [2, 3]:
        st.warning("⚠️ Selecione exatamente 2 ou 3 meses.")
    else:
        with st.spinner("🔍 Analisando base histórica..."):

            # Mapeia meses selecionados para número
            meses_numeros = [mapa_mes_num[mes] for mes in meses_escolhidos]

            # Extrai mês da data de cadastro
            df['Mes'] = df['Data Cadastro'].dt.month

            # Filtra apenas os meses selecionados
            dados_propensao = df[df['Mes'].isin(meses_numeros)]

            # 🔧 Limita para teste (remove se for produção)
            dados_propensao = dados_propensao.head(100_000)

            # Agrupa por cliente e soma indicadores
            clientes_freq = dados_propensao.groupby(
                ['Codigo Cliente', 'Razao Social'], observed=True
            ).agg({
                'Qtd Venda': 'sum',
                'Vlr Venda': 'sum',
                'Data Cadastro': 'count'
            }).reset_index()

            # Recupera info de representante e supervisor
            reps_info = dados_propensao[['Codigo Cliente', 'Codigo Representante', 'Codigo Supervisor']] \
                .drop_duplicates('Codigo Cliente')

            # Junta com os dados agrupados
            clientes_freq = clientes_freq.merge(reps_info, on='Codigo Cliente', how='left')

            # Renomeia colunas
            clientes_freq = clientes_freq.rename(columns={
                'Qtd Venda': 'Total de Pares',
                'Vlr Venda': 'Total Vendido (R$)',
                'Data Cadastro': 'Frequência de Compra'
            })

            # Ordena por frequência e quantidade
            clientes_freq = clientes_freq.sort_values(
                by=['Frequência de Compra', 'Total de Pares'],
                ascending=False
            )

            # Salva no session_state para uso posterior
            st.session_state["clientes_freq"] = clientes_freq

            # Mostra resultado
            st.markdown("## 🔮 Clientes com Maior Propensão de Compra")
            st.dataframe(clientes_freq[[ 
                'Codigo Cliente', 'Razao Social', 'Codigo Representante', 'Codigo Supervisor',
                'Total de Pares', 'Total Vendido (R$)', 'Frequência de Compra'
            ]].head(30))

# ------------------------------------
# 📥 Botão de exportação por representante
# ------------------------------------
if "clientes_freq" in st.session_state:
    if st.button("📥 Exportar por Representante", key="btn_exportar_rep"):
        with st.spinner("🔄 Gerando arquivos Excel por representante..."):
            clientes_freq = st.session_state["clientes_freq"]
            representantes_unicos = clientes_freq['Codigo Representante'].dropna().unique()

            for rep in representantes_unicos:
                df_rep = clientes_freq[clientes_freq['Codigo Representante'] == rep]

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_rep.to_excel(writer, index=False, sheet_name='Clientes')
                output.seek(0)

                nome_arquivo = f"clientes_representante_{rep}.xlsx"
                st.download_button(
                    label=f"⬇️ Baixar: Representante {rep}",
                    data=output,
                    file_name=nome_arquivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


                               
# RODAPÉ
st.sidebar.markdown("---")
st.sidebar.caption(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.markdown("Desenvolvido por Kidy Data Team 🚀")
