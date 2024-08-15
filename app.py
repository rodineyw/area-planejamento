import pandas as pd
import streamlit as st
import plotly.express as px

file_path = 'Hub Financeiro.csv'
df = pd.read_csv(file_path)

# Quantidade de tarefas para o status
status_counts = df['Status'].value_counts().reset_index()
status_counts.columns = ['Status', 'Contagem']

# Titulo da aplicação
st.title("Dashboard de Andamento de Tarefas")

# Layout de duas colunas
col1, col2 = st.columns(2)

# # Exibir os dados em uma tabela
# st.subheader('Tabela de Tarefas')
# st.dataframe(df)

# Gráfico de barras interativo
with col1:
 st.subheader('Distribuição de Tarefas por Status')
 fig_bar = px.bar(status_counts, x='Status', y='Contagem',
                  color='Status', title='Distribuição de Tarefas',
                  labels={'Contagem': 'Número de Tarefas'})
 st.plotly_chart(fig_bar)


# Gráfico de Pizza interativo
with col2:
 st.subheader('Proporção de Tarefas por Status')
 fig_pie = px.pie(status_counts, values='Contagem', names='Status',
                  title='Proporção das Tarefas',
                  color_discrete_sequence=px.colors.sequential.RdBu)
 st.plotly_chart(fig_pie)

# Filtro de tarefas pos status
st.subheader('Filtrar Tarefas por Status')
status_filter = st.selectbox('Selecione o Status', df['Status'].unique())
filtered_tasks = df[df['Status'] == status_filter]
st.write(filtered_tasks)