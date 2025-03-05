import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Input, Output

# Carregando os dados
df = pd.read_csv('Projetos.csv')

# Limpeza de dados
df['Status'] = df['Status'].fillna('Não Definido')
df['Prioridade'] = df['Prioridade'].fillna('Não Definida')
df['Atualizado por'] = df['Atualizado por'].fillna('Não Definido')
df['Data de Início'] = df['Data de Início'].fillna('Não informado')

df['Data de Término'] = pd.to_datetime(df['Data de Término'], errors='coerce')

df['Ano de Término'] = df['Data de Término'].dt.year.fillna('Não informado')

# Iniciando a aplicação Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout da aplicação
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Projetos"), className="mb-2 mt-2")
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='filtro_projeto',
                options=[{'label': projeto, 'value': projeto} for projeto in df['Projeto'].unique()],
                placeholder='Selecione um projeto',
                multi=True  # Permite selecionar múltiplos projetos
            ),
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Projetos Concluídos", className="card-title"),
                    html.H2(id="projetos_concluidos", className="card-text"),
                ])
            ], className="mb-4")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Projetos por Prioridade", className="card-title"),
                    dcc.Graph(id="grafico_prioridade")
                ])
            ], className="mb-4")
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Projetos por Status", className="card-title"),
                    dcc.Graph(id="grafico_status")
                ])
            ], className="mb-4")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Projetos por Setor", className="card-title"),
                    dcc.Graph(id="grafico_setor")
                ])
            ], className="mb-4")
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Distribuição por Ano de Término", className="card-title"),
                    dcc.Graph(id="grafico_ano")
                ])
            ], className="mb-4")
        ], width=12)
    ])
], fluid=True)

# Callback para atualizar os gráficos e KPIs com base no filtro
@app.callback(
    [Output('projetos_concluidos', 'children'),
     Output('grafico_prioridade', 'figure'),
     Output('grafico_status', 'figure'),
     Output('grafico_setor', 'figure'),
     Output('grafico_ano', 'figure')],
    [Input('filtro_projeto', 'value')]
)
def atualizar_dashboard(projetos_selecionados):
    # Filtrando os dados
    if projetos_selecionados:
        df_filtrado = df[df['Projeto'].isin(projetos_selecionados)]
    else:
        df_filtrado = df

    # Quantidade de Projetos Concluídos
    projetos_concluidos = df_filtrado[df_filtrado['Status'] == 'Concluído'].shape[0]

    # Gráfico de projetos por prioridade
    fig_prioridade = px.bar(df_filtrado['Prioridade'].value_counts().reset_index(),
                            x='index', y='Prioridade',
                            labels={'index': 'Prioridade', 'Prioridade': 'Quantidade'},
                            title="Projetos por Prioridade")

    # Gráfico de projetos por status
    fig_status = px.pie(df_filtrado['Status'].value_counts().reset_index(),
                        names='index', values='Status',
                        title="Projetos por Status")

    # Gráfico de projetos por setor
    fig_setor = px.bar(df_filtrado['Setor'].value_counts().reset_index(),
                       x='index', y='Setor',
                       labels={'index': 'Setor', 'Setor': 'Quantidade'},
                       title="Projetos por Setor")

    # Gráfico de distribuição por ano de término
    fig_ano = px.bar(df_filtrado['Ano de Término'].value_counts().reset_index(),
                     x='index', y='Ano de Término',
                     labels={'index': 'Ano', 'Ano de Término': 'Quantidade'},
                     title="Projetos por Ano de Término")

    return projetos_concluidos, fig_prioridade, fig_status, fig_setor, fig_ano

# Rodando a aplicação
if __name__ == '__main__':
    app.run_server(debug=True)
