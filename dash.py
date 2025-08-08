import plotly.express as px
import streamlit as st
import pandas as pd

# Carregando os dados
df = pd.read_csv('proje.csv')

# Limpeza de dados
df['Status'] = df['Status'].fillna('Não Definido')
df['Prioridade'] = df['Prioridade'].fillna('Não Definida')
df['Atualizado por'] = df['Atualizado por'].fillna('Não Definido')
df['Data de Início'] = df['Data de Início'].fillna('Não informado')
df['Data de Término'] = pd.to_datetime(df['Data de Término'], errors='coerce')
df['Ano de Término'] = pd.to_numeric(df['Data de Término'].dt.year, errors='coerce').fillna(0).astype(int)
df['Mês de Término'] = df['Data de Término'].dt.to_period('M').astype(str)

# Configuração do Streamlit
st.set_page_config(page_title="Dashboard de Projetos", page_icon="assets/favicon.ico", layout="wide")

# Título do dashboard
st.title("📊 Dashboard de Projetos")

# Filtro por projeto e data
col_filtro1, col_filtro2 = st.columns([2, 2])
with col_filtro1:
    projetos_selecionados = st.multiselect("Selecione um projeto", df['Projeto'].unique())
with col_filtro2:
    data_inicio = st.date_input("Data de Início", df['Data de Término'].min().date())
    data_fim = st.date_input("Data de Fim", df['Data de Término'].max().date())

# Botão para limpar filtros
if st.button("Limpar Filtros"):
    projetos_selecionados = []
    data_inicio = df['Data de Término'].min().date()
    data_fim = df['Data de Término'].max().date()

# Aplicar filtros
df_filtrado = df.copy()
if projetos_selecionados:
    df_filtrado = df_filtrado[df_filtrado['Projeto'].isin(projetos_selecionados)]
df_filtrado = df_filtrado[(df_filtrado['Data de Término'].dt.date >= data_inicio) & (df_filtrado['Data de Término'].dt.date <= data_fim)]

# KPIs
col1, col2 = st.columns(2)
col1.metric("📌 Total de Projetos", df_filtrado.shape[0])
col2.metric("✅ Projetos Concluídos", df_filtrado[df_filtrado['Status'] == 'Concluído'].shape[0])

# Gráficos
st.subheader("📌 Distribuição de Projetos")
col1, col2 = st.columns(2)

# Projetos por Prioridade
prioridade_counts = df_filtrado['Prioridade'].value_counts().reset_index()
prioridade_counts.columns = ['Prioridade', 'Quantidade']
fig_prioridade = px.bar(prioridade_counts, x='Prioridade', y='Quantidade',
                        labels={'Prioridade': 'Prioridade', 'Quantidade': 'Quantidade'},
                        title="Projetos por Prioridade")
col1.plotly_chart(fig_prioridade, use_container_width=True)

# Projetos por Status
status_counts = df_filtrado['Status'].value_counts().reset_index()
status_counts.columns = ['Status', 'Quantidade']
fig_status = px.pie(status_counts, names='Status', values='Quantidade',
                    title="Distribuição por Status")
col2.plotly_chart(fig_status, use_container_width=True)

# Gráficos adicionais
st.subheader("📌 Outras Análises")
col3, col4 = st.columns(2)

# Projetos por Setor
setor_counts = df_filtrado['Setor'].value_counts().reset_index()
setor_counts.columns = ['Setor', 'Quantidade']
fig_setor = px.bar(setor_counts, x='Setor', y='Quantidade',
                   labels={'Setor': 'Setor', 'Quantidade': 'Quantidade'},
                   title="Projetos por Setor")
col3.plotly_chart(fig_setor, use_container_width=True)

# Evolução Mensal de Projetos
mes_counts = df_filtrado['Mês de Término'].value_counts().reset_index()
mes_counts.columns = ['Mês', 'Quantidade']
mes_counts = mes_counts.sort_values(by='Mês')
fig_mes = px.line(mes_counts, x='Mês', y='Quantidade', markers=True,
                  labels={'Mês': 'Mês', 'Quantidade': 'Quantidade'},
                  title="Evolução Mensal de Projetos")
col4.plotly_chart(fig_mes, use_container_width=True)

# Exibição da tabela filtrada
st.subheader("📋 Dados Detalhados")
st.dataframe(df_filtrado)