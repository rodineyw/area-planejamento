# app.py  |  streamlit run app.py
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Dashboard de Projetos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# TEMA/ESTILO (CSS simples p/ “cara de produto”)
# =========================
st.markdown("""
<style>
/* fonte e cores suaves */
html, body, [class*="css"]  { font-family: Inter, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }
.block-container { padding-top: 1rem; padding-bottom: 0.5rem; }
h1, h2, h3 { letter-spacing: 0.2px; }

/* cards de KPI */
.kpi {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 2px 10px rgba(0,0,0,.04);
}
.kpi .label { color: #6c757d; font-size: 0.85rem; margin-bottom: 6px; }
.kpi .value { font-weight: 700; font-size: 1.6rem; }

/* subtítulo seção */
.section-title {
  margin-top: 0.8rem; margin-bottom: 0.2rem;
  font-weight: 700; font-size: 1.05rem; color: #495057;
  text-transform: uppercase; letter-spacing: .06em;
}

/* tabela mais compacta */
[data-testid="stDataFrame"] div[role="gridcell"] { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# =========================
# LOGGING
# =========================
LOG_PATH = Path("dashboard.log")
logger = logging.getLogger("proj_dash")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = RotatingFileHandler(LOG_PATH, maxBytes=800_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
log = logger.info

# =========================
# LOAD
# =========================
@st.cache_data(show_spinner=True)
def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype="object", keep_default_na=True)

    # nomes canônicos (ajuste se seu CSV variar)
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

    # limpeza texto padrão
    for col in ["Projeto", "Status", "Prioridade", "Atualizado por", "Setor"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": None, "None": None, "": None})
            df[col] = df[col].fillna("Não Definido")

    # projeto sem nome não some do filtro
    if "Projeto" in df.columns:
        df["Projeto"] = df["Projeto"].replace({"Não Definido": "(Sem nome)"})

    # datas como datetime (sem strings enfiadas na coluna)
    for dcol in ["Data de Início", "Data de Término"]:
        if dcol in df.columns:
            df[dcol] = pd.to_datetime(df[dcol], errors="coerce", dayfirst=True)

    # campos auxiliares
    if "Data de Término" in df.columns:
        df["Ano de Término"] = df["Data de Término"].dt.year
        df["PeriodoMes"] = df["Data de Término"].dt.to_period("M")
        try:
            df["Mês de Término Nome"] = df["Data de Término"].dt.month_name(locale="pt_BR")
        except Exception:
            df["Mês de Término Nome"] = df["Data de Término"].dt.month_name()
    else:
        df["Ano de Término"] = pd.NA
        df["PeriodoMes"] = pd.NA
        df["Mês de Término Nome"] = pd.NA

    # logs
    log(f"carregado: {len(df)} linhas | projetos únicos={df['Projeto'].nunique() if 'Projeto' in df.columns else 0} | NaT término={df['Data de Término'].isna().sum() if 'Data de Término' in df.columns else '-'}")
    return df

CSV_PATH = "projetos.csv"
df = load_data(CSV_PATH)

# =========================
# SIDEBAR (FILTROS)
# =========================
st.sidebar.markdown("## ⚙️ Filtros")

# projetos (com “selecionar tudo”)
projetos_unicos = sorted(df["Projeto"].dropna().unique().tolist()) if "Projeto" in df.columns else []
sel_all = st.sidebar.checkbox("Selecionar todos os projetos", value=True)
if sel_all:
    projetos_sel = st.sidebar.multiselect("Projetos", options=projetos_unicos, default=projetos_unicos)
else:
    projetos_sel = st.sidebar.multiselect("Projetos", options=projetos_unicos, default=[])

# filtros adicionais (tipo Power BI)
status_opts = sorted(df["Status"].dropna().unique().tolist()) if "Status" in df.columns else []
priori_opts = sorted(df["Prioridade"].dropna().unique().tolist()) if "Prioridade" in df.columns else []
setor_opts  = sorted(df["Setor"].dropna().unique().tolist()) if "Setor" in df.columns else []

status_sel   = st.sidebar.multiselect("Status", options=status_opts, default=status_opts)
priori_sel   = st.sidebar.multiselect("Prioridade", options=priori_opts, default=priori_opts)
setor_sel    = st.sidebar.multiselect("Setor", options=setor_opts, default=setor_opts)

# busca textual
texto_busca = st.sidebar.text_input("Buscar (Projeto / Atualizado por)", "")

# período (data de término)
if "Data de Término" in df.columns and df["Data de Término"].notna().any():
    data_min = df["Data de Término"].min().date()
    data_max = df["Data de Término"].max().date()
else:
    data_min, data_max = pd.Timestamp("2000-01-01").date(), pd.Timestamp.today().date()

data_ini = st.sidebar.date_input("Data inicial (Término)", value=data_min, min_value=data_min, max_value=data_max)
data_fim = st.sidebar.date_input("Data final (Término)", value=data_max, min_value=data_min, max_value=data_max)

incluir_sem_data = st.sidebar.checkbox("Incluir itens sem Data de Término", value=True)

# botão reset
if st.sidebar.button("♻️ Limpar filtros"):
    st.cache_data.clear()
    st.experimental_rerun()

# =========================
# APLICA FILTROS
# =========================
df_f = df.copy()

if projetos_sel:
    df_f = df_f[df_f["Projeto"].isin(projetos_sel)]

if status_sel:
    df_f = df_f[df_f["Status"].isin(status_sel)]

if priori_sel:
    df_f = df_f[df_f["Prioridade"].isin(priori_sel)]

if setor_sel:
    df_f = df_f[df_f["Setor"].isin(setor_sel)]

if texto_busca.strip():
    t = texto_busca.strip().lower()
    mask = False
    cols_busca = [c for c in ["Projeto", "Atualizado por"] if c in df_f.columns]
    for c in cols_busca:
        m = df_f[c].astype(str).str.lower().str.contains(t, na=False)
        mask = m if isinstance(mask, bool) else (mask | m)
    df_f = df_f[mask]

if "Data de Término" in df_f.columns:
    with_data = df_f["Data de Término"].notna()
    if incluir_sem_data:
        df_f = df_f[(~with_data) | ((df_f["Data de Término"].dt.date >= data_ini) & (df_f["Data de Término"].dt.date <= data_fim))]
    else:
        df_f = df_f[with_data & (df_f["Data de Término"].dt.date >= data_ini) & (df_f["Data de Término"].dt.date <= data_fim)]

log(f"após filtros: {len(df_f)} linhas | proj={len(projetos_sel)}/{len(projetos_unicos)} | incluir_sem_data={incluir_sem_data}")

# =========================
# CABEÇALHO
# =========================
st.title("📊 Dashboard de Projetos")
st.caption("Visual analítica com filtros estilo Power BI, datas em pt-BR e gráficos organizados.")

# =========================
# KPIs (cards)
# =========================
c1, c2, c3, c4 = st.columns(4)
total_reg = len(df_f)
proj_unicos = df_f["Projeto"].nunique() if "Projeto" in df_f.columns else 0
concl = (df_f["Status"] == "Concluído").sum() if "Status" in df_f.columns else 0
taxa_conc = (concl / total_reg * 100) if total_reg else 0.0
ult_termino = df_f["Data de Término"].max() if "Data de Término" in df_f.columns else pd.NaT
ult_termino_br = ult_termino.strftime("%d/%m/%Y") if pd.notna(ult_termino) else "—"

for col, label, value in [
    (c1, "Total de Registros", f"{total_reg:,}".replace(",", ".")),
    (c2, "Projetos Únicos", f"{proj_unicos:,}".replace(",", ".")),
    (c3, "Concluídos", f"{concl:,}".replace(",", ".")),
    (c4, "Taxa de Conclusão", f"{taxa_conc:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")),
]:
    with col:
        st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

st.markdown(f'<div class="section-title">Última Data de Término: {ult_termino_br}</div>', unsafe_allow_html=True)

# =========================
# PALETA/ESTILO PLOTLY
# =========================
px.defaults.template = "plotly_white"
PALETA = px.colors.qualitative.Set2

# =========================
# VISUAL 1: Prioridade (barra)
# =========================
g1, g2 = st.columns(2)
if "Prioridade" in df_f.columns and not df_f.empty:
    p_counts = df_f["Prioridade"].value_counts(dropna=False).reset_index()
    p_counts.columns = ["Prioridade", "Quantidade"]
    fig_p = px.bar(p_counts, x="Prioridade", y="Quantidade", color="Prioridade",
                   color_discrete_sequence=PALETA, title="Projetos por Prioridade")
    fig_p.update_layout(showlegend=False, margin=dict(l=10,r=10,t=60,b=10))
    g1.plotly_chart(fig_p, use_container_width=True)
else:
    g1.info("Sem dados de Prioridade.")

# =========================
# VISUAL 2: Status (pizza/donut)
# =========================
if "Status" in df_f.columns and not df_f.empty:
    s_counts = df_f["Status"].value_counts(dropna=False).reset_index()
    s_counts.columns = ["Status", "Quantidade"]
    fig_s = px.pie(s_counts, names="Status", values="Quantidade",
                   hole=.5, color="Status", color_discrete_sequence=PALETA,
                   title="Distribuição por Status")
    fig_s.update_traces(textposition="inside", textinfo="percent+label")
    fig_s.update_layout(margin=dict(l=10,r=10,t=60,b=10))
    g2.plotly_chart(fig_s, use_container_width=True)
else:
    g2.info("Sem dados de Status.")

# =========================
# VISUAL 3: Setor x Status (barra empilhada)
# =========================
st.markdown('<div class="section-title">Análise por Setor</div>', unsafe_allow_html=True)
if {"Setor","Status"}.issubset(df_f.columns) and not df_f.empty:
    ct = (df_f.groupby(["Setor","Status"]).size().reset_index(name="Quantidade"))
    fig_st = px.bar(ct, x="Setor", y="Quantidade", color="Status",
                    barmode="stack", color_discrete_sequence=PALETA,
                    title="Projetos por Setor (Empilhado por Status)")
    fig_st.update_layout(xaxis={'categoryorder':'total descending'}, margin=dict(l=10,r=10,t=60,b=10))
    st.plotly_chart(fig_st, use_container_width=True)
else:
    st.info("Sem dados suficientes para Setor x Status.")

# =========================
# VISUAL 4: Evolução mensal
# =========================
st.markdown('<div class="section-title">Evolução Mensal (Data de Término)</div>', unsafe_allow_html=True)
df_mes = df_f.dropna(subset=["PeriodoMes"]).copy()
if not df_mes.empty:
    mc = df_mes.groupby("PeriodoMes").size().reset_index(name="Quantidade")
    mc["Label"] = mc["PeriodoMes"].dt.strftime("%Y-%m")
    mc = mc.sort_values("PeriodoMes")
    fig_m = px.line(mc, x="Label", y="Quantidade", markers=True,
                    title="Quantidade por Mês de Término")
    fig_m.update_layout(margin=dict(l=10,r=10,t=60,b=10))
    st.plotly_chart(fig_m, use_container_width=True)
else:
    st.info("Sem datas de término para série temporal.")

# =========================
# VISUAL 5: Timeline / Gantt (Início x Término)
# =========================
st.markdown('<div class="section-title">Timeline (Gantt)</div>', unsafe_allow_html=True)
if {"Projeto","Data de Início","Data de Término"}.issubset(df_f.columns):
    gantt = df_f.dropna(subset=["Data de Início","Data de Término"]).copy()
    # evita linhas invertidas
    gantt = gantt[gantt["Data de Término"] >= gantt["Data de Início"]]
    if not gantt.empty:
        fig_g = px.timeline(
            gantt,
            x_start="Data de Início", x_end="Data de Término",
            y="Projeto", color="Status" if "Status" in gantt.columns else None,
            color_discrete_sequence=PALETA, title="Cronograma dos Projetos"
        )
        fig_g.update_yaxes(autorange="reversed")
        fig_g.update_layout(margin=dict(l=10,r=10,t=60,b=10), height=520)
        st.plotly_chart(fig_g, use_container_width=True)
    else:
        st.info("Nenhum projeto com início e término válidos.")
else:
    st.info("Faltam colunas para montar o Gantt (Projeto, Data de Início, Data de Término).")

# =========================
# TABELA FINAL (datas em DD/MM/AAAA)
# =========================
st.markdown('<div class="section-title">Dados Detalhados</div>', unsafe_allow_html=True)
df_view = df_f.copy()
for col in ["Data de Início", "Data de Término"]:
    if col in df_view.columns:
        df_view[col] = pd.to_datetime(df_view[col], errors="coerce", dayfirst=True)\
                          .dt.strftime("%d/%m/%Y").fillna("")

cols_exibir = [c for c in ["Projeto","Status","Prioridade","Setor","Atualizado por",
                           "Data de Início","Data de Término","Ano de Término","Mês de Término"]
               if c in df_view.columns]

if cols_exibir:
    st.dataframe(df_view[cols_exibir], use_container_width=True, height=420)
    # download filtrado
    # csv_bytes = df_view[cols_exibir].to_csv(index=False).encode("utf-8-sig")
    # st.download_button("⬇️ Baixar CSV filtrado", data=csv_bytes, file_name="projetos_filtrado.csv", mime="text/csv")
else:
    st.info("Sem colunas para exibir nessa visão.")

# =========================
# LOGS (opcional)
# =========================
# with st.expander("Ver últimos logs"):
#     try:
#         st.code(Path(LOG_PATH).read_text(encoding="utf-8")[-4000:])
#     except Exception:
#         st.write("Sem logs ainda.")
