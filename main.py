import plotly.express as px
import streamlit as st
import pandas as pd

# Carregando os dados
df = pd.read_csv('Projetos.csv')

# Limpeza de dados
df['Status'] = df['Status'].fillna('Não Definido')
df['Prioridade'] = df['Prioridade'].fillna('Não Definida')
df['Atualizado por'] = df['Atualizado por'].fillna('Não Definido')
df['Data de Início'] = df['Data de Início'].fillna('Não informado')
df['Data de Término'] = pd.to_datetime(df['Data de Término'], errors='coerce')
df['Ano de Término'] = df['Data de Término'].dt.year.fillna('Não informado')

# Configuração do Streamlit
st.set_page_config(page_title="Dashboard de Projetos", layout="wide")

# Título do dashboard
st.title("📊 Dashboard de Projetos")

# Filtro por projeto
projetos_selecionados = st.multiselect("Selecione um projeto", df['Projeto'].unique())

# Filtro por data de término
min_date = df['Data de Término'].min().date()
max_date = df['Data de Término'].max().date()
data_inicio, data_fim = st.slider(
    "Selecione o período de término dos projetos",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="DD-MM-YYYY"
)

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

# Projetos por Ano de Término
ano_counts = df_filtrado['Ano de Término'].value_counts().reset_index()
ano_counts.columns = ['Ano', 'Quantidade']
fig_ano = px.bar(ano_counts, x='Ano', y='Quantidade',
                 labels={'Ano': 'Ano', 'Quantidade': 'Quantidade'},
                 title="Projetos por Ano de Término")
col4.plotly_chart(fig_ano, use_container_width=True)

# Exibição da tabela filtrada
st.subheader("📋 Dados Detalhados")
st.dataframe(df_filtrado)