import plotly.express as px
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd

# Carregando os dados
df = pd.read_csv('Hub Financeiro.csv')

# Limpeza de dados
df['Status'] = df['Status'].fillna('Não Definido')
df['Prioridade'] = df['Prioridade'].fillna('Não Definida')
df['Responsável'] = df['Responsável'].fillna('Não Definido')

# Iniciando a aplicação Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout da aplicação
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard Financeiro"), className="mb-2 mt-2")
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='filtro_tarefa',
                options=[{'label': tarefa, 'value': tarefa}
                         for tarefa in df['Tarefa'].unique()],
                placeholder='Selecione uma tarefa',
                multi=True  # Permite selecionar múltiplas tarefas
            ),
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Tarefas Concluídas", className="card-title"),
                    html.H2(id="tarefas_concluidas", className="card-text"),
                ])
            ], className="mb-4")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Tarefas por Prioridade", className="card-title"),
                    dcc.Graph(id="grafico_prioridade")
                ])
            ], className="mb-4")
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Tarefas por Status", className="card-title"),
                    dcc.Graph(id="grafico_status")
                ])
            ], className="mb-4")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Tarefas por Responsável", className="card-title"),
                    dcc.Graph(id="grafico_responsavel")
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
                    dcc.Graph(id="grafico_projeto")
                ])
            ], className="mb-4")
        ], width=12)
    ])
], fluid=True)

# Callback para atualizar os gráficos e KPIs com base no filtro


@app.callback(
    [Output('tarefas_concluidas', 'children'),
     Output('grafico_prioridade', 'figure'),
     Output('grafico_status', 'figure'),
     Output('grafico_responsavel', 'figure'),
     Output('grafico_projeto', 'figure')],
    [Input('filtro_tarefa', 'value')]
)
def atualizar_dashboard(tarefas_selecionadas):
    # Filtrando os dados
    if tarefas_selecionadas:
        df_filtrado = df[df['Tarefa'].isin(tarefas_selecionadas)]
    else:
        df_filtrado = df

    # Atualizando KPI 1: Quantidade de Tarefas Concluídas
    tarefas_concluidas = df_filtrado[df_filtrado['Status']
                                     == 'Concluída'].shape[0]

    # Atualizando gráfico de tarefas por prioridade
    tarefas_por_prioridade = df_filtrado['Prioridade'].value_counts(
    ).reset_index()
    tarefas_por_prioridade.columns = ['Prioridade', 'Contagem']
    fig_prioridade = px.bar(tarefas_por_prioridade, x='Prioridade', y='Contagem',
                            labels={'Prioridade': 'Prioridade',
                                    'Contagem': 'Quantidade'},
                            title="Distribuição por Prioridade")

    # Atualizando gráfico de tarefas por status
    tarefas_por_status = df_filtrado['Status'].value_counts().reset_index()
    tarefas_por_status.columns = ['Status', 'Contagem']
    fig_status = px.pie(tarefas_por_status, names='Status', values='Contagem',
                        title="Distribuição por Status")

    # Atualizando gráfico de tarefas por responsável
    tarefas_por_responsavel = df_filtrado['Responsável'].value_counts(
    ).reset_index()
    tarefas_por_responsavel.columns = ['Responsável', 'Contagem']
    fig_responsavel = px.bar(tarefas_por_responsavel, x='Responsável', y='Contagem',
                             labels={'Responsável': 'Responsável',
                                     'Contagem': 'Quantidade'},
                             title="Distribuição por Responsável")

    # Atualizando gráfico de tarefas por projeto
    tarefas_por_projeto = df_filtrado['Projeto'].value_counts().reset_index()
    tarefas_por_projeto.columns = ['Projeto', 'Contagem']
    fig_projeto = px.bar(tarefas_por_projeto, x='Projeto', y='Contagem',
                         labels={'Projeto': 'Projeto',
                                 'Contagem': 'Quantidade'},
                         title="Distribuição por Projeto")

    return tarefas_concluidas, fig_prioridade, fig_status, fig_responsavel, fig_projeto


# Rodando a aplicação localmente
if __name__ == '__main__':
    app.run_server(debug=True)
