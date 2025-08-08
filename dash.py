# streamlit run app.py
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

# =========================
# CONFIG STREAMLIT (sempre no topo)
# =========================
st.set_page_config(page_title="Dashboard de Projetos", page_icon="📊", layout="wide")

# =========================
# LOGGING
# =========================
LOG_PATH = Path("dashboard.log")
logger = logging.getLogger("proj_dash")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = RotatingFileHandler(LOG_PATH, maxBytes=512_000, backupCount=2, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

def log(msg):
    logger.info(msg)

# =========================
# CARREGAMENTO DE DADOS
# =========================
@st.cache_data(show_spinner=False)
def load_data(csv_path: str) -> pd.DataFrame:
    # Ajuste encoding/sep se necessário
    df = pd.read_csv(
        csv_path,
        dtype="object",                  # lê tudo como texto inicialmente
        keep_default_na=True,
    )

    # Normalização de colunas esperadas (renomeie aqui se seu CSV tiver variação)
    colmap = {
        "Projeto": "Projeto",
        "Status": "Status",
        "Prioridade": "Prioridade",
        "Atualizado por": "Atualizado por",
        "Setor": "Setor",
        "Data de Início": "Data de Início",
        "Data de Término": "Data de Término",
    }
    df = df.rename(columns=colmap)

    # Limpeza de texto básico
    for col in ["Projeto", "Status", "Prioridade", "Atualizado por", "Setor"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": None, "None": None})
            df[col] = df[col].fillna("Não Definido")

    # Projeto sem nome vira "(Sem nome)" para não sumir do multiselect
    if "Projeto" in df.columns:
        df["Projeto"] = df["Projeto"].replace({"Não Definido": "(Sem nome)"})

    # Parse de datas (sem enfiar string em coluna de data)
    for dcol in ["Data de Início", "Data de Término"]:
        if dcol in df.columns:
            # tenta parsear pt-BR (dia/mes/ano). Se vier ISO também dá certo.
            df[dcol] = pd.to_datetime(df[dcol], errors="coerce", dayfirst=True)

    # Colunas auxiliares para análise
    if "Data de Término" in df.columns:
        # Ano e período (para ordenação por mês)
        df["Ano de Término"] = df["Data de Término"].dt.year
        # Período mensal para ordenar corretamente
        df["PeriodoMes"] = df["Data de Término"].dt.to_period("M")
        # Nome do mês em PT-BR (Exibição)
        try:
            df["Mês de Término"] = df["Data de Término"].dt.month_name(locale="pt_BR")
        except Exception:
            # Fallback caso o locale falhe por algum motivo bizarro
            df["Mês de Término"] = df["Data de Término"].dt.month_name()

        # Formato BR para exibição
        df["Data de Término_BR"] = df["Data de Término"].dt.strftime("%d/%m/%Y")
    else:
        df["Ano de Término"] = pd.NA
        df["PeriodoMes"] = pd.NA
        df["Mês de Término"] = pd.NA
        df["Data de Término_BR"] = pd.NA

    if "Data de Início" in df.columns:
        df["Data de Início_BR"] = df["Data de Início"].dt.strftime("%d/%m/%Y")
    else:
        df["Data de Início_BR"] = pd.NA

    # Logs úteis
    total = len(df)
    nat_termino = df["Data de Término"].isna().sum() if "Data de Término" in df.columns else 0
    projetos_unicos = df["Projeto"].nunique() if "Projeto" in df.columns else 0
    log(f"Linhas totais: {total} | NaT(Data de Término): {nat_termino} | Projetos únicos: {projetos_unicos}")

    return df

CSV_PATH = "proje.csv"
df = load_data(CSV_PATH)

# =========================
# TÍTULO
# =========================
st.title("📊 Dashboard de Projetos")

# =========================
# FILTROS
# =========================
col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 1])

# Multiselect com TODOS os projetos possíveis (do df completo)
todos_projetos = sorted(df["Projeto"].dropna().unique().tolist())
with col_filtro1:
    projetos_selecionados = st.multiselect(
        "Selecione projetos (vazio = todos):",
        options=todos_projetos,
        default=[],
    )

# Range de datas baseado apenas em linhas com Data de Término válida
if "Data de Término" in df.columns:
    df_com_data = df.dropna(subset=["Data de Término"]).copy()
    if df_com_data.empty:
        # sem nenhuma data válida
        data_min = pd.Timestamp("2000-01-01")
        data_max = pd.Timestamp.today().normalize()
    else:
        data_min = df_com_data["Data de Término"].min().date()
        data_max = df_com_data["Data de Término"].max().date()
else:
    data_min = pd.Timestamp("2000-01-01").date()
    data_max = pd.Timestamp.today().normalize().date()

with col_filtro2:
    data_inicio = st.date_input("Data de Início (Filtro por Término)", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = st.date_input("Data de Fim (Filtro por Término)", value=data_max, min_value=data_min, max_value=data_max)

with col_filtro3:
    incluir_sem_data = st.checkbox("Incluir sem data", value=True)

# Botão limpar
if st.button("Limpar Filtros"):
    projetos_selecionados = []
    data_inicio = data_min
    data_fim = data_max
    incluir_sem_data = True
    st.experimental_rerun()

# =========================
# APLICAÇÃO DOS FILTROS
# =========================
df_filtrado = df.copy()

# Filtro de projetos
if projetos_selecionados:
    df_filtrado = df_filtrado[df_filtrado["Projeto"].isin(projetos_selecionados)]

# Filtro de data de término
mask_com_data = df_filtrado["Data de Término"].notna()
mask_intervalo = False
if mask_com_data.any():
    mask_intervalo = (
        (df_filtrado["Data de Término"].dt.date >= data_inicio) &
        (df_filtrado["Data de Término"].dt.date <= data_fim)
    )

if incluir_sem_data:
    # Mantém as linhas sem data + as dentro do intervalo
    if isinstance(mask_intervalo, bool) and not mask_intervalo:
        df_filtrado = df_filtrado  # nenhuma com data válida; mantém só sem data
    else:
        df_filtrado = df_filtrado[(~mask_com_data) | mask_intervalo]
else:
    # Só linhas com data dentro do intervalo
    if isinstance(mask_intervalo, bool) and not mask_intervalo:
        df_filtrado = df_filtrado.iloc[0:0]  # vazio
    else:
        df_filtrado = df_filtrado[mask_com_data & mask_intervalo]

log(f"Após filtro: linhas={len(df_filtrado)} | projetos selecionados={len(projetos_selecionados)} | incluir_sem_data={incluir_sem_data}")

# =========================
# KPIs
# =========================
k1, k2, k3 = st.columns(3)
k1.metric("📌 Total de Registros", len(df_filtrado))
k2.metric("🧩 Projetos Únicos", df_filtrado["Projeto"].nunique())
k3.metric("✅ Concluídos", (df_filtrado["Status"] == "Concluído").sum())

# =========================
# GRÁFICOS
# =========================
st.subheader("📌 Distribuição de Projetos")
g1, g2 = st.columns(2)

# Prioridade
if "Prioridade" in df_filtrado.columns and not df_filtrado.empty:
    prioridade_counts = (df_filtrado["Prioridade"]
                         .value_counts(dropna=False)
                         .reset_index())
    prioridade_counts.columns = ["Prioridade", "Quantidade"]
    fig_prioridade = px.bar(
        prioridade_counts, x="Prioridade", y="Quantidade",
        labels={"Prioridade": "Prioridade", "Quantidade": "Quantidade"},
        title="Projetos por Prioridade"
    )
    g1.plotly_chart(fig_prioridade, use_container_width=True)
else:
    g1.info("Sem dados de Prioridade após os filtros.")

# Status
if "Status" in df_filtrado.columns and not df_filtrado.empty:
    status_counts = (df_filtrado["Status"]
                     .value_counts(dropna=False)
                     .reset_index())
    status_counts.columns = ["Status", "Quantidade"]
    fig_status = px.pie(
        status_counts, names="Status", values="Quantidade",
        title="Distribuição por Status"
    )
    g2.plotly_chart(fig_status, use_container_width=True)
else:
    g2.info("Sem dados de Status após os filtros.")

st.subheader("📌 Outras Análises")
g3, g4 = st.columns(2)

# Setor
if "Setor" in df_filtrado.columns and not df_filtrado.empty:
    setor_counts = (df_filtrado["Setor"]
                    .value_counts(dropna=False)
                    .reset_index())
    setor_counts.columns = ["Setor", "Quantidade"]
    fig_setor = px.bar(
        setor_counts, x="Setor", y="Quantidade",
        labels={"Setor": "Setor", "Quantidade": "Quantidade"},
        title="Projetos por Setor"
    )
    g3.plotly_chart(fig_setor, use_container_width=True)
else:
    g3.info("Sem dados de Setor após os filtros.")

# Evolução Mensal (ordenada cronologicamente)
df_mes = df_filtrado.dropna(subset=["PeriodoMes"]).copy()
if not df_mes.empty:
    mes_counts = (df_mes.groupby("PeriodoMes")
                  .size()
                  .reset_index(name="Quantidade"))
    mes_counts["Mês"] = mes_counts["PeriodoMes"].dt.strftime("%Y-%m")  # para eixo legível
    mes_counts = mes_counts.sort_values("PeriodoMes")
    fig_mes = px.line(
        mes_counts, x="Mês", y="Quantidade", markers=True,
        labels={"Mês": "Mês", "Quantidade": "Quantidade"},
        title="Evolução Mensal de Projetos (por Data de Término)"
    )
    g4.plotly_chart(fig_mes, use_container_width=True)
else:
    g4.info("Sem datas de término suficientes para evolução mensal.")

# =========================
# TABELA (com datas em pt-BR)
# =========================
st.subheader("📋 Dados Detalhados")
cols_exibir = []
for c in ["Projeto", "Status", "Prioridade", "Setor", "Atualizado por", "Data de Início_BR", "Data de Término_BR"]:
    if c in df_filtrado.columns:
        cols_exibir.append(c)

if cols_exibir:
    st.dataframe(df_filtrado[cols_exibir], use_container_width=True)
else:
    st.info("Sem colunas para exibir nessa visão.")

# =========================
# LOGS (opcional)
# =========================
with st.expander("Ver últimos logs"):
    try:
        st.code(Path(LOG_PATH).read_text(encoding="utf-8")[-4000:])
    except Exception:
        st.write("Sem logs ainda.")
