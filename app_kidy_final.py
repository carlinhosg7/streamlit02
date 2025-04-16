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

# ✅ CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Dashboard Preditivo Kidy",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ CSS CUSTOMIZADO
def add_custom_css():
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #E60012;
            color: white;
            border-radius: 8px;
            height: 3em;
            width: 100%;
            font-weight: bold;
            border: none;
        }
        div.stButton > button:hover {
            background-color: #A3000B;
            color: #ffffff;
        }
        footer {visibility: hidden;}
        div[data-testid="metric-container"] label {
            font-size: 12px !important;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-size: 16px !important;
        }
        </style>
    """, unsafe_allow_html=True)

add_custom_css()

# ✅ LOGO NO TOPO
logo_kidy = Image.open("logo_kidy.png")
st.image(logo_kidy, width=100)

# ✅ DICIONÁRIO DE MESES
meses_portugues = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# ✅ FUNÇÃO PARA CARREGAR DADOS
@st.cache_resource(ttl=3600)
def carregar_dados_processados():
    try:
        file_path = r"C:/Kidy/PREDITIVA/DADOS_PREDITIVA.xlsx"
        df = pd.read_excel(file_path, sheet_name='DADOS PREDITIVA')
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

    df['Codigo Grupo Cliente'] = df['Codigo Grupo Cliente'].astype(str).str.upper()
    df['Codigo Cliente'] = df['Codigo Cliente'].astype(str).str.upper()
    df['Data Cadastro'] = pd.to_datetime(df['Data Cadastro'], errors='coerce')
    df['Data Ultima Compra'] = pd.to_datetime(df['Data Ultima Compra'], errors='coerce')
    df['Preço Médio Produto'] = df.apply(lambda row: row['Vlr Venda'] / row['Qtd Venda'] if row['Qtd Venda'] > 0 else 0, axis=1)
    return df

# ✅ FUNÇÃO RFV INDIVIDUAL COM SCORE
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
