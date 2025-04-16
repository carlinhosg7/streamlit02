import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import tempfile
import os
from PIL import Image

# ✅ Adiciona CSS Customizado
def add_custom_css():
    st.markdown("""
        <style>
        .css-10trblm {
            color: #E60012;
            font-weight: bold;
        }

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

        .css-1d391kg {
            background-color: #F7A400;
        }

        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# ✅ Chama a função para aplicar o CSS
add_custom_css()

# ✅ Configuração da página
st.set_page_config(
    page_title="Dashboard Preditivo Kidy",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ Logo Kidy no topo
logo_kidy = Image.open("logo_kidy.png")
st.image(logo_kidy, width=250)

# ✅ Dicionário dos meses em português
meses_portugues = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# ✅ Carrega dados com cache e TTL de 1 hora
@st.cache_resource(ttl=3600)
def carregar_dados_processados():
    file_path = r"C:/Kidy/PREDITIVA/DADOS_PREDITIVA.xlsx"
    df = pd.read_excel(file_path, sheet_name='DADOS PREDITIVA')
    df['Codigo Grupo Cliente'] = df['Codigo Grupo Cliente'].astype(str).str.upper()
    df['Codigo Cliente'] = df['Codigo Cliente'].astype(str).str.upper()
    df['Data Cadastro'] = pd.to_datetime(df['Data Cadastro'], errors='coerce')
    df['Data Ultima Compra'] = pd.to_datetime(df['Data Ultima Compra'], errors='coerce')
    return df

# ✅ Geração de PDF
def gerar_pdf(nome_grupo, ultima_compra, periodo_analise, melhor_mes_nome, vendas_totais, tabela_top_linhas, top_produtos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt=f"Relatório Grupo Cliente: {nome_grupo}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.cell(200, 10, txt=f"Última Compra: {ultima_compra}", ln=True)
    pdf.cell(200, 10, txt=f"Período da análise: {periodo_analise}", ln=True)
    pdf.cell(200, 10, txt=f"Melhor mês para oferecer produtos: {melhor_mes_nome}", ln=True)
    pdf.cell(200, 10, txt=f"Total de itens vendidos: {vendas_totais:,} unidades", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, txt="Top 10 Linhas de Produtos:", ln=True)
    for _, row in tabela_top_linhas.iterrows():
        pdf.cell(200, 10, txt=f"{row['Linha']} - {row['Quantidade Vendida']}", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, txt="Top 10 Produtos dos Dois Últimos Semestres:", ln=True)
    for _, row in top_produtos.iterrows():
        pdf.cell(200, 10, txt=f"{row['Produto']} - {row['Quantidade Vendida']}", ln=True)

    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, f"Relatorio_{nome_grupo}.pdf")
    pdf.output(pdf_path)

    return pdf_path

# ✅ Carregamento dos dados
df = carregar_dados_processados()

# ✅ Título principal
st.title("📊 Dashboard de Análise Preditiva - Grupo de Clientes Kidy")

# ✅ Sidebar com logo e filtros
st.sidebar.image(logo_kidy, use_column_width=True)
st.sidebar.header("🔧 Filtros de Análise")

codigo_grupo_cliente = st.sidebar.text_input(
    "Código do Grupo de Cliente (Opcional):",
    help="Digite o código do grupo de cliente que deseja analisar."
).strip().upper()

codigo_cliente = st.sidebar.text_input(
    "Código do Cliente (Opcional):",
    help="Digite o código específico do cliente para análise detalhada."
).strip().upper()

data_min = df['Data Cadastro'].min().date()
data_max = df['Data Cadastro'].max().date()

periodo = st.sidebar.date_input(
    "Período da análise:",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max,
    help="Selecione o intervalo de datas para análise dos dados."
)

# ✅ Ação de análise
if st.sidebar.button("🔎 Analisar Grupo/Cliente"):
    if not codigo_grupo_cliente and not codigo_cliente:
        st.sidebar.warning("⚠️ Informe pelo menos um código de grupo de cliente ou código de cliente!")
    else:
        with st.spinner('🔎 Analisando dados...'):
            dados_filtrados = df.copy()

            if codigo_cliente:
                dados_filtrados = dados_filtrados[dados_filtrados['Codigo Cliente'] == codigo_cliente]
            elif codigo_grupo_cliente:
                dados_filtrados = dados_filtrados[dados_filtrados['Codigo Grupo Cliente'] == codigo_grupo_cliente]

            if dados_filtrados.empty:
                st.error("Nenhum dado encontrado para os filtros informados!")
            else:
                dados_filtrados = dados_filtrados[
                    (dados_filtrados['Data Cadastro'] >= pd.to_datetime(periodo[0])) &
                    (dados_filtrados['Data Cadastro'] <= pd.to_datetime(periodo[1]))
                ]

                if dados_filtrados.empty:
                    st.warning("⚠️ Nenhum dado encontrado para o período selecionado!")
                else:
                    nome_grupo = dados_filtrados['Grupo Cliente'].iloc[0]

                    hoje = pd.to_datetime(datetime.today().date())
                    dados_filtrados['Diferenca Dias'] = (hoje - dados_filtrados['Data Ultima Compra']).abs()
                    ultima_data_compra = dados_filtrados.loc[dados_filtrados['Diferenca Dias'].idxmin(), 'Data Ultima Compra']
                    ultima_compra = ultima_data_compra.strftime('%d/%m/%Y') if pd.notnull(ultima_data_compra) else 'Sem compras registradas'

                    primeira_data = dados_filtrados['Data Cadastro'].min()
                    ultima_data = dados_filtrados['Data Cadastro'].max()
                    periodo_analise = f"{primeira_data.strftime('%d/%m/%Y')} até {ultima_data.strftime('%d/%m/%Y')}"

                    vendas_totais = dados_filtrados['Qtd Venda'].sum()
                    total_pedidos = dados_filtrados['Data Cadastro'].nunique()
                    ticket_medio = vendas_totais / total_pedidos if total_pedidos else 0

                    dados_filtrados['Mes Pedido'] = dados_filtrados['Data Cadastro'].dt.month
                    melhor_mes_num = dados_filtrados['Mes Pedido'].mode()[0]
                    melhor_mes_nome = meses_portugues.get(melhor_mes_num, 'Mês inválido')

                    dados_filtrados['Semestre'] = dados_filtrados['Data Cadastro'].dt.month.apply(lambda x: '1º Semestre' if x <= 6 else '2º Semestre')

                    vendas_semestre = dados_filtrados.groupby(['Linha', 'Semestre'])['Qtd Venda'].sum().unstack(fill_value=0).reset_index()
                    total_vendas_linha = dados_filtrados.groupby('Linha')['Qtd Venda'].sum().reset_index(name='Quantidade Vendida Total')
                    top_linhas = pd.merge(total_vendas_linha, vendas_semestre, on='Linha')
                    top_linhas = top_linhas.sort_values(by='Quantidade Vendida Total', ascending=False).head(10)

                    st.subheader(f"📌 Grupo Cliente: {nome_grupo}")
                    col1, col2, col3 = st.columns(3)

                    col1.metric("📅 Última Compra", ultima_compra)
                    col2.metric("🕒 Período da Análise", periodo_analise)
                    col3.metric("📈 Melhor Mês para Oferta", melhor_mes_nome)

                    st.success(f"📦 Total de Itens Vendidos: {vendas_totais:,} unidades")

                    with st.expander("👉 Top 10 Linhas de Produtos para Oferecer"):
                        st.table(
                            top_linhas[['Linha', 'Quantidade Vendida Total']].rename(columns={'Quantidade Vendida Total': 'Quantidade Vendida'})
                        )

                    dados_filtrados['Ano'] = dados_filtrados['Data Cadastro'].dt.year
                    dados_filtrados['SemestreNum'] = dados_filtrados['Data Cadastro'].dt.month.apply(lambda x: 1 if x <= 6 else 2)

                    ultimos_periodos = dados_filtrados[['Ano', 'SemestreNum']].drop_duplicates().sort_values(['Ano', 'SemestreNum'], ascending=[False, False]).head(2)

                    filtro_semestres = pd.merge(dados_filtrados, ultimos_periodos, how='inner', on=['Ano', 'SemestreNum'])

                    top_produtos = filtro_semestres.groupby('Referencia')['Qtd Venda'].sum().reset_index().sort_values(by='Qtd Venda', ascending=False).head(10)

                    # ✅ Renomeia colunas para manter consistência visual
                    top_produtos_renomeado = top_produtos.rename(columns={
                        'Referencia': 'Produto',
                        'Qtd Venda': 'Quantidade Vendida'
                    })

                    st.markdown("👉 **Top 10 Produtos Vendidos nos Dois Últimos Semestres:**")
                    st.table(top_produtos_renomeado)

                    fig_top_produtos = px.bar(
                        top_produtos_renomeado,
                        x='Produto',
                        y='Quantidade Vendida',
                        color='Produto',
                        color_discrete_sequence=px.colors.qualitative.Safe,
                        title='🎯 Top 10 Produtos dos Dois Últimos Semestres'
                    )

                    st.plotly_chart(fig_top_produtos)

                    pdf_path = gerar_pdf(
                        nome_grupo, ultima_compra, periodo_analise, melhor_mes_nome, vendas_totais,
                        top_linhas[['Linha', 'Quantidade Vendida Total']].rename(columns={'Quantidade Vendida Total': 'Quantidade Vendida'}),
                        top_produtos_renomeado
                    )

                    with open(pdf_path, "rb") as f:
                        st.download_button("📥 Baixar Relatório em PDF", f, file_name=os.path.basename(pdf_path), mime="application/pdf")

# ✅ Rodapé
st.sidebar.markdown("---")
st.sidebar.caption(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.markdown("Desenvolvido por [Seu Nome] 🚀")
