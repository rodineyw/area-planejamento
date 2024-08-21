import pandas as pd
import streamlit as st
import plotly.express as px
from auth import login
import schedule
import time
from threading import Thread

# Configurar o dashboard em modo wide
st.set_page_config(
    page_title="Tarefas - Preâmbulo Financeiro",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para atualizar os dados


def atualizar_dados():
    try:
        df = pd.read_csv('Hub Financeiro.csv')
        st.session_state['df'] = df
        print('Dados Atualizados')
    except FileNotFoundError:
        st.error(
            "O arquivo 'Hub Financeiro.csv' não foi encontrado. Verifique o caminho do arquivo.")


# Funçaõ para rodar o scheduler em um thread separado
def run_scheduler():
    schedule.every(30).minutes.do(atualizar_dados)
    while True:
        schedule.run_pending()
        time.sleep(1)


# Inicia o schedule em segundo plano
def start_scheduler():
    t = Thread(target=run_scheduler)
    t.daemon = True
    t.start()


# Verificar se o usuário está autenticado
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Depuração: Mostrar o estado de autenticação antes de carregar o dashboard
# st.write("Autenticação antes do dashboard:", st.session_state["authenticated"])

# Se o usuário está autenticado, exibir o dashboard
if st.session_state["authenticated"]:
    st.title(f"Bem-vindo, {st.session_state['username']}!")

    # Acesso limitado para usuários com diferentes permissões
    if st.session_state["role"] == "admin":
        st.subheader("Painel de Controle")
        st.write("Aqui estão as opções de gerenciamento do app...")
    else:
        st.write("Você está no modo de visualização como Visitante.")

    file_path = 'Hub Financeiro.csv'
    try:
        df = pd.read_csv(file_path)

        # Quantidade de tarefas por o status
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Contagem']

        # Layout de duas colunas
        col1, col2 = st.columns(2)

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
                             title='Proporção das Tarefas por Setor',
                             color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie)

        # Filtro de tarefas por status
        st.subheader('Filtrar Tarefas por Status')
        status_filter = st.selectbox(
            'Selecione o Status', df['Status'].unique())
        filtered_tasks = df[df['Status'] == status_filter]
        st.write(filtered_tasks)

    except FileNotFoundError:
        st.error(
            "O arquivo 'Hub Financeiro.csv' não foi encontrado. Verifique o caminho do arquivo.")

else:
    # Se o usuário não está autenticado, chamar a função de login
    login()

    # Depuração: Exibir o estado de autenticação para verificar se está sendo alterado
    # st.write("Autenticação após tentativa de login:",
    #          st.session_state["authenticated"])
