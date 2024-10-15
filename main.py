import plotly.express as px
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd

df = pd.read_csv('Hub Financeiro.csv')

# Limpeza de dados
df['Status'] = df['Status'].fillna('Não Definido')
df['Prioridade'] = df['Prioridade'].fillna('Não Definida')
df['Responsável'] = df['Responsável'].fillna('Não Definido')

# KPI 1: Quantidade de Tarefas Concluídas
tarefas_concluidas = df[df['Status'] == 'Concluída'].shape[0]

# KPI 2: Tarefas por Prioridade
tarefas_por_prioridade = df['Prioridade'].value_counts().reset_index()
tarefas_por_prioridade.columns = ['Prioridade', 'Contagem']

# KPI 3: Tarefas por Status
tarefas_por_status = df['Status'].value_counts().reset_index()
tarefas_por_status.columns = ['Status', 'Contagem']

# KPI 4: Tarefas por Responsável
tarefas_por_responsavel = df['Responsável'].value_counts().reset_index()
tarefas_por_responsavel.columns = ['Responsável', 'Contagem']

# KPI 5: Distribuição por Projeto
tarefas_por_projeto = df['Projeto'].value_counts().reset_index()
tarefas_por_projeto.columns = ['Projeto', 'Contagem']

# Iniciando a aplicação Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout da aplicação
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard Financeiro"), className="mb-2 mt-2")
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Tarefas Concluídas", className="card-title"),
                    html.H2(f"{tarefas_concluidas}", className="card-text"),
                ])
            ], className="mb-4")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Tarefas por Prioridade", className="card-title"),
                    dcc.Graph(
                        figure=px.bar(tarefas_por_prioridade, x='Prioridade', y='Contagem',
                                      labels={'Prioridade': 'Prioridade',
                                              'Contagem': 'Quantidade'},
                                      title="Distribuição por Prioridade")
                    )
                ])
            ], className="mb-4")
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Tarefas por Status", className="card-title"),
                    dcc.Graph(
                        figure=px.pie(tarefas_por_status, names='Status', values='Contagem',
                                      title="Distribuição por Status")
                    )
                ])
            ], className="mb-4")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Tarefas por Responsável", className="card-title"),
                    dcc.Graph(
                        figure=px.bar(tarefas_por_responsavel, x='Responsável', y='Contagem',
                                      labels={'Responsável': 'Responsável',
                                              'Contagem': 'Quantidade'},
                                      title="Distribuição por Responsável")
                    )
                ])
            ], className="mb-4")
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Distribuição por Projeto",
                            className="card-title"),
                    dcc.Graph(
                        figure=px.bar(tarefas_por_projeto, x='Projeto', y='Contagem',
                                      labels={'Projeto': 'Projeto',
                                              'Contagem': 'Quantidade'},
                                      title="Distribuição por Projeto")
                    )
                ])
            ], className="mb-4")
        ], width=12)
    ])
], fluid=True)

# Rodando a aplicação localmente
if __name__ == '__main__':
    app.run_server(debug=True)
