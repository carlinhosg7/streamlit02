# ✅ IMPORTS E CONFIGURAÇÃO INICIAL
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import plotly.io as pio
import unicodedata
import numpy as np
import requests
import gc

pio.kaleido.scope.default_format = "png"

# ----------------------------
# 🔐 AUTENTICAÇÃO
# ----------------------------
@st.cache_data
def carregar_usuarios(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo, engine="openpyxl")
    df.columns = [
        unicodedata.normalize('NFKD', col).encode('ascii', errors='ignore').decode('utf-8').strip().lower().replace(" ", "_")
        for col in df.columns
    ]
    df['usuario'] = df['usuario'].astype(str).str.strip()
    df['senha'] = df['senha'].astype(str).str.strip()
    return df

def autenticar_usuario():
    usuarios = carregar_usuarios("auth.xlsx")
    st.session_state['autenticado'] = st.session_state.get('autenticado', False)

    if not st.session_state['autenticado']:
        with st.sidebar:
            st.markdown("### 🔐 Login")
            usuario = st.text_input("Usuário").strip()
            senha = st.text_input("Senha", type="password").strip()

            if st.button("Entrar"):
                if usuario in usuarios['usuario'].values:
                    senha_valida = usuarios[usuarios['usuario'] == usuario]['senha'].values[0]
                    if senha == senha_valida:
                        st.session_state['autenticado'] = True
                        st.session_state['codigo_representante'] = usuario
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta.")
    if not st.session_state['autenticado']:
        st.stop()

# ----------------------------
# 🚀 CARREGAMENTO DE DADOS
# ----------------------------
@st.cache_data(ttl=3600)
def carregar_dados_parquet():
    base_path = "C:/preditiva/streamlit02"
    arquivos = [f"{base_path}/DADOS_PREDITIVA_{i}.parquet" for i in range(1, 7)]
    dfs = []
    for arq in arquivos:
        dfs.append(pd.read_parquet(arq))
    gc.collect()  # limpa após cada leitura
    df = pd.concat(dfs, ignore_index=True)
    del dfs
    gc.collect()


    df['Codigo Representante'] = df['Codigo Representante'].astype(str).str.strip().str.lstrip("0").astype("category")
    df['Codigo Supervisor'] = df['Codigo Supervisor'].astype(str).str.strip().astype("category")
    df['Codigo Grupo Cliente'] = df['Codigo Grupo Cliente'].astype(str).str.upper().astype("category")
    df['Codigo Cliente'] = df['Codigo Cliente'].astype(str).str.upper().astype("category")
    df['Grupo Cliente'] = df['Grupo Cliente'].astype(str).str.strip().astype("category")
    df['Razao Social'] = df['Razao Social'].astype(str).str.strip().astype("category")
    df['Linha'] = df['Linha'].astype(str).str.strip().astype("category")
    df['Data Cadastro'] = pd.to_datetime(df['Data Cadastro'], errors='coerce')
    df['Qtd Venda'] = pd.to_numeric(df['Qtd Venda'], errors='coerce').fillna(0).astype('int16')
    df['Vlr Venda'] = pd.to_numeric(df['Vlr Venda'], errors='coerce').fillna(0).astype('float32')  # ok manter float32
    #df['Preço Médio Produto'] = (df['Vlr Venda'] / df['Qtd Venda'].replace(0, pd.NA)).fillna(0).round(2).astype('float32')

    return df

# ----------------------------
# 🌐 CONFIGURAÇÃO STREAMLIT
# ----------------------------
st.set_page_config(
    page_title="Dashboard Analítico",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def carregar_logo():
    caminho = "C:/preditiva/streamlit02/logo_kidy.png"
    try:
        return Image.open(caminho)
    except:
        return None

# ----------------------------
# 📊 INICIALIZAÇÃO
# ----------------------------
autenticar_usuario()
logo = carregar_logo()
if logo:
    st.sidebar.image(logo, width=100)
    st.image(logo, width=150)

st.title("📊 Dashboard Analítico")

df = carregar_dados_parquet()

# 🔐 Filtra se não for admin
usuario = st.session_state.get("codigo_representante", "admin").strip().lower()
if usuario != "admin":
    df = df[df['Codigo Representante'] == usuario]
    st.markdown(f"🆔 Representante: `{usuario.upper()}`")
else:
    st.markdown("🟢 Modo Admin: Visualizando todos os dados")

del usuario
gc.collect()

# ----------------------------
# 🎯 FILTROS DE ANÁLISE
# ----------------------------
with st.sidebar:
    st.markdown("### 🛠️ Filtros de Análise")
    grupo_selecionado = st.selectbox("🔍 Buscar Grupo Cliente:", options=sorted(df['Grupo Cliente'].dropna().unique()))

    clientes_opcoes = df[df['Grupo Cliente'] == grupo_selecionado]['Codigo Cliente'].dropna().unique()
    cliente_selecionado = st.selectbox("🔎 Buscar Cliente:", options=sorted(clientes_opcoes))

    data_inicio = st.date_input("Período da análise:", value=datetime(2024, 1, 1), key="data_inicio")
    data_fim = st.date_input(" ", value=datetime.now(), key="data_fim")

    aplicar_filtros = st.button("🔴 Analisar Grupo/Cliente")

# ----------------------------
# ✅ FILTRAGEM CONDICIONAL
# ----------------------------
df_filtrado = df

if aplicar_filtros:
    df_filtrado = df[
        (df['Grupo Cliente'] == grupo_selecionado) &
        (df['Codigo Cliente'] == cliente_selecionado) &
        (df['Data Cadastro'].between(pd.to_datetime(data_inicio), pd.to_datetime(data_fim)))
    ]

    lojas = df_filtrado['Codigo Cliente'].nunique()
    reps = df_filtrado['Codigo Representante'].nunique()
    supervisor = df_filtrado['Codigo Supervisor'].iloc[0] if not df_filtrado.empty else "-"
    ultima_compra = df_filtrado[df_filtrado['Qtd Venda'] > 0]['Data Cadastro'].max()
    periodo_inicio = df_filtrado['Data Cadastro'].min()
    periodo_fim = df_filtrado['Data Cadastro'].max()

    st.markdown(f"## 📍 Grupo Cliente: **{grupo_selecionado}** | 🏬 Lojas: {lojas} | 🆔 Representante(s): {reps}")
    st.markdown(f"### 👨‍💼 Supervisor: {supervisor}")

    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Última Compra", ultima_compra.strftime('%d/%m/%Y') if pd.notnull(ultima_compra) else "Sem compras")
    col2.metric("📆 Período da Análise", f"{periodo_inicio.strftime('%d/%m/%Y')} até {periodo_fim.strftime('%d/%m/%Y')}")

    # Melhor mês de oferta baseado em histórico
    mes_mais_comprado = (
        df_filtrado[df_filtrado['Qtd Venda'] > 0]
        .groupby(df_filtrado['Data Cadastro'].dt.month)['Qtd Venda']
        .sum()
        .idxmax()
        if not df_filtrado.empty else None
    )
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    col3.metric("📌 Melhor Mês para Oferta", meses[mes_mais_comprado - 1] if mes_mais_comprado else "-")

# ----------------------------
# 📊 KPIs GERAIS
# ----------------------------
col1, col2, col3, col4 = st.columns(4)
clientes_ativos = df_filtrado['Codigo Cliente'].nunique()
qtd_total = df_filtrado['Qtd Venda'].sum()
vlr_total = df_filtrado['Vlr Venda'].sum()
ticket_medio = vlr_total / qtd_total if qtd_total > 0 else 0
col1.metric("🧾 Clientes Ativos", clientes_ativos)
col2.metric("📦 Qtd Vendida", f"{qtd_total:,.0f}".replace(",", "."))
col3.metric("💰 Valor Total (R$)", f"R$ {vlr_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# ----------------------------
# 📈 GRÁFICOS ANALÍTICOS
# ----------------------------
st.markdown("### 📈 Vendas por Mês")
if not df_filtrado.empty:
    df_filtrado['AnoMes'] = df_filtrado['Data Cadastro'].dt.to_period('M')
    df_agrupado = df_filtrado.groupby(df_filtrado['AnoMes']).agg({
        'Qtd Venda': 'sum',
        'Vlr Venda': 'sum'
    }).reset_index()
    df_agrupado['AnoMes'] = df_agrupado['AnoMes'].dt.to_timestamp()
    fig = px.bar(df_agrupado, x='AnoMes', y='Qtd Venda', title='Quantidade Vendida por Mês')
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.line(df_agrupado, x='AnoMes', y='Vlr Venda', title='Valor Vendido por Mês (R$)')
    st.plotly_chart(fig2, use_container_width=True)

# ----------------------------
# 🔟 TOP 10 LINHAS
# ----------------------------
st.markdown("### 🔟 Top 10 Linhas Mais Vendidas")
df_top_linhas = df_filtrado.groupby("Linha")["Qtd Venda"].sum().sort_values(ascending=False).head(10).reset_index()
fig_top_linhas = px.bar(df_top_linhas, x="Qtd Venda", y="Linha", orientation="h", title="Top 10 Linhas", color="Linha")
st.plotly_chart(fig_top_linhas, use_container_width=True)

# ----------------------------
# 🤖 PREVISÃO COM RANDOM FOREST
# ----------------------------
st.markdown("### 🤖 Previsão de Compra com Random Forest")
try:
    df_modelo = df_filtrado.copy()
    df_modelo['Comprou'] = (df_modelo['Qtd Venda'] > 0).astype(int)
    df_modelo['Mes'] = df_modelo['Data Cadastro'].dt.month.astype("int")
    df_modelo['Ano'] = df_modelo['Data Cadastro'].dt.year.astype("int")
    features = ['Mes', 'Ano']
    df_modelo = df_modelo.dropna(subset=features + ['Comprou'])
    X = df_modelo[features]
    y = df_modelo['Comprou']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)
    acc = modelo.score(X_test, y_test)
    st.success(f"🔍 Acurácia do modelo: {acc * 100:.2f}%")
except Exception as e:
    st.warning(f"⚠️ Modelo não pôde ser treinado: {e}")

# ----------------------------
# 📄 EXPORTAÇÃO
# ----------------------------
if not df_filtrado.empty:
    if st.download_button("⬇️ Exportar CSV Filtrado", data=df_filtrado.to_csv(index=False).encode("utf-8"), file_name="dados_filtrados.csv", mime="text/csv"):
        st.success("Arquivo CSV gerado com sucesso!")

# ----------------------------
# 📌 RODAPÉ
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.caption(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.markdown("Desenvolvido por Kidy Data Team 🚀")
