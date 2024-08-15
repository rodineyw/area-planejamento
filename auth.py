import streamlit as st
import os
from dotenv import load_dotenv

# Carregar as variáveis do arquivo .env
load_dotenv()

# Dicionário de usuários e senhas usando as variáveis do .env
USER_CREDENTIALS = {
    os.getenv("USER_1"): os.getenv("PASSWORD_1"),
    os.getenv("USER_2"): os.getenv("PASSWORD_2")
}


# Função de autenticação

def login():
    st.sidebar.title("Autenticação")
    username = st.sidebar.text_input("Usuário")
    password = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Login"):
        if USER_CREDENTIALS.get(username) == password:
            st.session_state["authenticated"] = True
            st.sidebar.success("Login bem-sucedido!")
        else:
            st.sidebar.error("Usuário ou senha incorretos.")

        # Depuração: Mostrar se o login foi bem-sucedido
        st.write("Autenticação após login:", st.session_state["authenticated"])
