import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from io import BytesIO

# >>> PRIMEIRO COMANDO STREAMLIT <<<
st.set_page_config(page_title="Previsão de Compras", layout="wide")

# URLs dos arquivos
URL1 = "https://raw.githubusercontent.com/carlinhosg7/streamlit02/2de64c019746e62779ad101e8d508093625d5ac8/DADOS_PREDITIVA_1.csv"
URL2 = "https://raw.githubusercontent.com/carlinhosg7/streamlit02/2de64c019746e62779ad101e8d508093625d5ac8/DADOS_PREDITIVA_2.csv"

@st.cache_data
def carregar_dados():
    df1 = pd.read_csv(URL1, delimiter=",")
    df2 = pd.read_csv(URL2, delimiter=",")
    df = pd.concat([df1, df2], ignore_index=True)
    return df

# Carrega os dados
with st.spinner('Carregando dados...'):
    df = carregar_dados()

# Título
st.title("Análise Preditiva de Compras por Cliente")

# Filtros de período (Mês, Bimestre, Trimestre)
TIPOS = ["Mensal", "Bimestral", "Trimestral"]
tipo_periodo = st.sidebar.selectbox("Selecione o tipo de período", TIPOS)
MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

if tipo_periodo == "Mensal":
    idx = st.sidebar.selectbox("Selecione o mês", range(12), format_func=lambda i: MESES[i])
    meses_escolhidos = [idx]
    texto_periodo = f"{MESES[idx]}"
elif tipo_periodo == "Bimestral":
    bimestres = [(i, i+1) for i in range(0, 12, 2)]
    idx = st.sidebar.selectbox(
        "Selecione o bimestre", range(6),
        format_func=lambda i: f"{MESES[bimestres[i][0]]} - {MESES[bimestres[i][1]]}"
    )
    meses_escolhidos = [bimestres[idx][0], bimestres[idx][1]]
    texto_periodo = f"{MESES[bimestres[idx][0]]} - {MESES[bimestres[idx][1]]}"
elif tipo_periodo == "Trimestral":
    trimestres = [(i, i+1, i+2) for i in range(0, 12, 3)]
    idx = st.sidebar.selectbox(
        "Selecione o trimestre", range(4),
        format_func=lambda i: f"{MESES[trimestres[i][0]]} - {MESES[trimestres[i][2]]}"
    )
    meses_escolhidos = [trimestres[idx][0], trimestres[idx][1], trimestres[idx][2]]
    texto_periodo = f"{MESES[trimestres[idx][0]]} - {MESES[trimestres[idx][2]]}"

st.write(f"Período selecionado: {texto_periodo}")

# Filtro por Supervisor
mapa_supervisor = {
    9902: "Centro Oeste",
    9907: "Sul",
    9914: "Norte / Nordeste",
    9915: "REM",
    9916: "SPC",
    9917: "SPI"
}
if 'Codigo Supervisor' in df.columns:
    df['Supervisor Nome'] = df['Codigo Supervisor'].map(mapa_supervisor)
else:
    df['Supervisor Nome'] = None

supervisores_disponiveis = sorted(df['Supervisor Nome'].dropna().unique())
supervisor_escolhido = st.sidebar.selectbox(
    "Filtrar por Supervisor", ["Todos"] + list(supervisores_disponiveis)
)

# Tratamento das datas
coluna_data_ultima_compra = 'Data Ultima Compra'
df[coluna_data_ultima_compra] = pd.to_datetime(df[coluna_data_ultima_compra], dayfirst=True, errors='coerce')

# Definição de coleção
def identificar_colecao(data):
    if pd.isnull(data):
        return None
    if data.month >= 11 or data.month <= 4:
        return 'Inverno'
    else:
        return 'Verão'
df['Colecao'] = df['Data Ultima Compra'].apply(identificar_colecao)

# Filtros de Supervisor e Período
if supervisor_escolhido != "Todos":
    df = df[df['Supervisor Nome'] == supervisor_escolhido]
if 'Data Ultima Compra' in df.columns:
    meses_filtro = [m+1 for m in meses_escolhidos]  # pandas: janeiro=1
    df = df[df['Data Ultima Compra'].dt.month.isin(meses_filtro)]

# Preparação para ML
df_ml = df.dropna(subset=['Codigo Grupo Cliente', 'Qtd Venda', 'Vlr Venda', 'Colecao'])
le = LabelEncoder()
df_ml['Colecao_encoded'] = le.fit_transform(df_ml['Colecao'])

X = df_ml[['Qtd Venda', 'Vlr Venda', 'Colecao_encoded']]
y = (df_ml['Qtd Venda'] > 0).astype(int)  # Se teve venda, classifica como potencial comprador

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)

# Predição de probabilidade
probabilidades = modelo.predict_proba(X)[:, 1]
df_ml['Probabilidade Compra (%)'] = (probabilidades * 100).round(2)

# ===== EXIBIÇÃO DA TABELA COM ML AGREGADA POR GRUPO CLIENTE =====
colunas_para_manter = [
    'Codigo Grupo Cliente', 'Grupo Cliente', 'Razao Social', 
    'Qtd Venda', 'Vlr Venda', 'Data Ultima Compra', 
    'Codigo Representante', 'Supervisor Nome', 'Probabilidade Compra (%)'
]

# Copiar as colunas para o DataFrame
df_tabela = df_ml[colunas_para_manter].copy()

# Remover NaN nas colunas que estamos comparando
df_tabela = df_tabela.dropna(subset=['Probabilidade Compra (%)', 'Qtd Venda'])

# Resetando os índices para garantir que as duas colunas estão alinhadas corretamente
df_tabela = df_tabela.reset_index(drop=True)

# Agrupar por 'Grupo Cliente' e agregar as informações
df_tabela_grouped = df_tabela.groupby('Grupo Cliente').agg({
    'Qtd Venda': 'sum',  # Somar as quantidades de vendas por grupo cliente
    'Vlr Venda': 'sum',  # Somar os valores das vendas por grupo cliente
    'Probabilidade Compra (%)': 'mean',  # Média da probabilidade de compra por grupo cliente
    'Supervisor Nome': 'first',  # Manter o primeiro supervisor do grupo
}).reset_index()

# Exibir a tabela agregada sem duplicação de colunas
st.write('Tabela agrupada por Grupo Cliente com previsão de compra:')
st.dataframe(df_tabela_grouped.sort_values('Probabilidade Compra (%)', ascending=False).head(30))

#Função para gerar o arquivo Excel e permitir o download
def gerar_excel(df):
    # Criar um arquivo Excel em memória
    with BytesIO() as buffer:
        # Salvar o DataFrame no arquivo Excel
        df.to_excel(buffer, index=False)
        buffer.seek(0)  # Voltar para o início do arquivo para leitura
        return buffer.read()  # Retornar o conteúdo lido para o download

# Bloco para criar o botão de download
st.markdown("### Baixar a Tabela como Excel")

# Gerar o arquivo Excel
excel_data = gerar_excel(df_tabela_grouped)

# Criar o botão de download
st.download_button(
    label="Baixar Tabela Agregada como Excel",
    data=excel_data,
    file_name="tabela_agrupada_com_probabilidade.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)