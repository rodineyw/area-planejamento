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

# Aplicar filtro
if projetos_selecionados:
    df_filtrado = df[df['Projeto'].isin(projetos_selecionados)]
else:
    df_filtrado = df

# KPIs
col1, col2 = st.columns(2)
col1.metric("📌 Total de Projetos", df_filtrado.shape[0])
col2.metric("✅ Projetos Concluídos", df_filtrado[df_filtrado['Status'] == 'Concluído'].shape[0])

# Gráficos
st.subheader("📌 Distribuição de Projetos")
col1, col2 = st.columns(2)

# Projetos por Prioridade
fig_prioridade = px.bar(df_filtrado['Prioridade'].value_counts().reset_index(),
                        x='index', y='Prioridade',
                        labels={'index': 'Prioridade', 'Prioridade': 'Quantidade'},
                        title="Projetos por Prioridade")
col1.plotly_chart(fig_prioridade, use_container_width=True)

# Projetos por Status
fig_status = px.pie(df_filtrado['Status'].value_counts().reset_index(),
                    names='index', values='Status',
                    title="Distribuição por Status")
col2.plotly_chart(fig_status, use_container_width=True)

# Gráficos adicionais
st.subheader("📌 Outras Análises")
col3, col4 = st.columns(2)

# Projetos por Setor
fig_setor = px.bar(df_filtrado['Setor'].value_counts().reset_index(),
                   x='index', y='Setor',
                   labels={'index': 'Setor', 'Setor': 'Quantidade'},
                   title="Projetos por Setor")
col3.plotly_chart(fig_setor, use_container_width=True)

# Projetos por Ano de Término
fig_ano = px.bar(df_filtrado['Ano de Término'].value_counts().reset_index(),
                 x='index', y='Ano de Término',
                 labels={'index': 'Ano', 'Ano de Término': 'Quantidade'},
                 title="Projetos por Ano de Término")
col4.plotly_chart(fig_ano, use_container_width=True)

# Exibição da tabela filtrada
st.subheader("📋 Dados Detalhados")
st.dataframe(df_filtrado)
