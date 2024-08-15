''' Autenticação '''
import streamlit as st
import os
from dotenv import load_dotenv

# Carregar as variáveis do arquivo .env
load_dotenv()

# Dicionário de usuários e senhas usando as variáveis do .env
USER_CREDENTIALS = {
    os.getenv("USER_1"): {"password": os.getenv("PASSWORD_1"), "role": "visitor", },
    os.getenv("USER_2"): {"password": os.getenv("PASSWORD_2"), "role": "admin"}
}


# Função de autenticação

def login():
    ''' Funcionalidade de login '''
    st.sidebar.title("Autenticação")
    username = st.sidebar.text_input("Usuário")
    password = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Login"):
        user = USER_CREDENTIALS.get(username)
        if user and user["password"] == password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["role"] = user["role"]
            st.sidebar.success("Login bem-sucedido!")
        else:
            st.sidebar.error("Usuário ou senha incorretos.")

        # Depuração: Mostrar se o login foi bem-sucedido
        # st.write("Autenticação após login:", st.session_state["authenticated"])
