# app.py
from pathlib import Path
import os, re, logging
from logging.handlers import RotatingFileHandler
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
from notion_client import Client
from notion_client.errors import APIResponseError
from dotenv import load_dotenv, find_dotenv

# ============== STREAMLIT ==============
st.set_page_config(page_title="Dashboard de Projetos", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
html, body, [class*="css"]{font-family:Inter,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}
.block-container{padding-top:1rem;padding-bottom:.5rem} h1,h2,h3{letter-spacing:.2px}
.kpi{background:#fff;border:1px solid #e9ecef;border-radius:14px;padding:16px 18px;box-shadow:0 2px 10px rgba(0,0,0,.04)}
.kpi .label{color:#6c757d;font-size:.85rem;margin-bottom:6px}
.kpi .value{font-weight:700;font-size:1.6rem;color:#212529}
@media (prefers-color-scheme: dark){
  .kpi{background:#121212;border-color:#2a2a2a;box-shadow:0 2px 14px rgba(0,0,0,.5)}
  .kpi .label{color:#b0b0b0} .kpi .value{color:#f1f3f5}
}
.section-title{margin-top:.8rem;margin-bottom:.2rem;font-weight:700;font-size:1.05rem;color:#495057;text-transform:uppercase;letter-spacing:.06em}
@media (prefers-color-scheme: dark){.section-title{color:#d0d4d9}}
[data-testid="stDataFrame"] div[role="gridcell"]{font-size:.9rem}
</style>
""", unsafe_allow_html=True)

# ============== LOGGING ==============
LOG_PATH = Path("dashboard.log")
logger = logging.getLogger("proj_dash"); logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
log = logger.info

# ============== ENV / NOTION (robusto) ==============
_ = load_dotenv(find_dotenv(usecwd=True), override=False)

def get_cred(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        try:
            v = (st.secrets[name] or "").strip()
        except Exception:
            v = ""
    return v

def sanitize_db_id(raw: str) -> str:
    if not raw: return ""
    m = re.search(r"[0-9a-fA-F]{32}", raw.replace("-", ""))
    return m.group(0) if m else ""

NOTION_TOKEN = get_cred("NOTION_TOKEN")
NOTION_DB    = sanitize_db_id(get_cred("NOTION_DATABASE_ID"))

if not NOTION_TOKEN or not NOTION_DB:
    st.error("Configure NOTION_TOKEN e NOTION_DATABASE_ID (apenas 32 hex).")
    st.stop()

# valida token e DB
try:
    _client = Client(auth=NOTION_TOKEN)
    _ = _client.users.me()
except APIResponseError as e:
    st.error(f"Token inválido ou sem permissão. Reemita e cole exatamente como fornecido pelo Notion.\nDetalhe: {e}")
    st.stop()

try:
    _client.databases.retrieve(database_id=NOTION_DB)
except APIResponseError as e:
    st.error("Falha ao acessar o **Database**. Confira:\n"
             "• ID é do **database** (não page) e tem 32 hex (sem `?v=`)\n"
             "• No Notion: DB → **Add connections** → selecione sua integração\n"
             f"Detalhe: {e}")
    st.stop()

# ============== MAPA DE PROPRIEDADES ==============
PROP_MAP = {
    "Projeto": ["Projeto", "Nome", "Title"],
    "Status": ["Status"],
    "Prioridade": ["Prioridade"],
    "Atualizado por": ["Atualizado por", "Responsável", "Owner"],
    "Setor": ["Setor", "Área"],
    "Data de Início": ["Data de Início", "Inicio", "Start"],
    "Data de Término": ["Data de Término", "Termino", "Fim", "End"],
}

# ============== HELPERS ==============
def _match_prop(props, aliases):
    for name in props.keys():
        if name in aliases: return name
    lower = {k.lower(): k for k in props.keys()}
    for alias in aliases:
        if alias.lower() in lower: return lower[alias.lower()]
    return None

def _get_text(rich):
    if not isinstance(rich, list) or not rich: return None
    return "".join([t.get("plain_text") or "" for t in rich]).strip() or None

def _get_people(p):
    if not isinstance(p, list) or not p: return None
    names = [(u.get("name") or "").strip() for u in p if (u.get("name") or "").strip()]
    return ", ".join(names) if names else None

def _to_date(d):
    if not isinstance(d, dict): return None, None
    def _p(x):
        try: return pd.to_datetime(x).date() if x else None
        except Exception: return None
    return _p(d.get("start")), _p(d.get("end"))

def get_date_bounds(df):
    if "Data de Término" in df.columns and df["Data de Término"].notna().any():
        return df["Data de Término"].min().date(), df["Data de Término"].max().date()
    return date(2000,1,1), date.today()

def ensure_filter_state(df):
    data_min, data_max = get_date_bounds(df)
    ss = st.session_state
    ss.setdefault("k_status", sorted(df["Status"].dropna().unique().tolist()) if "Status" in df.columns else [])
    ss.setdefault("k_prioridade", sorted(df["Prioridade"].dropna().unique().tolist()) if "Prioridade" in df.columns else [])
    ss.setdefault("k_setor", sorted(df["Setor"].dropna().unique().tolist()) if "Setor" in df.columns else [])
    ss.setdefault("k_texto", "")
    ss.setdefault("k_dataini", data_min)
    ss.setdefault("k_datafim", data_max)
    ss.setdefault("k_incluir_sem_data", True)
    # clamp
    ss.k_dataini = max(min(ss.k_dataini, data_max), data_min)
    ss.k_datafim = max(min(ss.k_datafim, data_max), data_min)
    if ss.k_dataini > ss.k_datafim:
        ss.k_dataini, ss.k_datafim = data_min, data_max
    return data_min, data_max

# ============== LOAD FROM NOTION ==============
@st.cache_data(show_spinner=True, ttl=300)
def load_from_notion(db_id: str) -> pd.DataFrame:
    rows, start_cursor = [], None
    while True:
        resp = _client.databases.query(database_id=db_id, start_cursor=start_cursor) if start_cursor \
               else _client.databases.query(database_id=db_id)
        rows.extend(resp.get("results", []))
        if not resp.get("has_more"): break
        start_cursor = resp.get("next_cursor")

    recs = []
    for it in rows:
        props = it.get("properties", {})
        p_Projeto = _match_prop(props, PROP_MAP["Projeto"])
        p_Status  = _match_prop(props, PROP_MAP["Status"])
        p_Prior   = _match_prop(props, PROP_MAP["Prioridade"])
        p_Atual   = _match_prop(props, PROP_MAP["Atualizado por"])
        p_Setor   = _match_prop(props, PROP_MAP["Setor"])
        p_DataI   = _match_prop(props, PROP_MAP["Data de Início"])
        p_DataT   = _match_prop(props, PROP_MAP["Data de Término"])

        projeto = None
        if p_Projeto and props[p_Projeto]["type"] == "title":
            projeto = _get_text(props[p_Projeto]["title"]) or "(Sem nome)"

        def _val(prop):
            if not prop or prop not in props: return None
            t = props[prop]["type"]
            if t == "select":       return (props[prop]["select"] or {}).get("name")
            if t == "status":       return (props[prop]["status"] or {}).get("name")
            if t == "multi_select": return ", ".join([x.get("name","") for x in (props[prop]["multi_select"] or []) if x.get("name")])
            if t == "rich_text":    return _get_text(props[prop]["rich_text"])
            if t == "people":       return _get_people(props[prop]["people"])
            return None

        status = _val(p_Status) or "Não Definido"
        prioridade = _val(p_Prior) or "Não Definida"
        atualizado_por = _val(p_Atual) or "Não Definido"
        setor = _val(p_Setor) or "Não Definido"

        di, dt = None, None
        if p_DataI and props[p_DataI]["type"] == "date":
            di, _ = _to_date(props[p_DataI]["date"])
        if p_DataT and props[p_DataT]["type"] == "date":
            stt, end = _to_date(props[p_DataT]["date"])
            dt = end or stt

        recs.append({
            "Projeto": projeto or "(Sem nome)",
            "Status": status,
            "Prioridade": prioridade,
            "Atualizado por": atualizado_por,
            "Setor": setor,
            "Data de Início": pd.to_datetime(di) if di else pd.NaT,
            "Data de Término": pd.to_datetime(dt) if dt else pd.NaT,
        })

    df = pd.DataFrame.from_records(recs)
    if not df.empty:
        df["Ano de Término"] = df["Data de Término"].dt.year
        df["PeriodoMes"] = df["Data de Término"].dt.to_period("M")
        try: df["Mês de Término Nome"] = df["Data de Término"].dt.month_name(locale="pt_BR")
        except Exception: df["Mês de Término Nome"] = df["Data de Término"].dt.month_name()
    else:
        df["Ano de Término"] = pd.NA; df["PeriodoMes"] = pd.NA; df["Mês de Término Nome"] = pd.NA

    log(f"Notion: linhas={len(df)} | projetos únicos={df['Projeto'].nunique() if not df.empty else 0} | NaT término={df['Data de Término'].isna().sum() if 'Data de Término' in df.columns else '-'}")
    return df

# botão atualizar (limpa só cache de dados)
if st.sidebar.button("🔄 Atualizar do Notion agora"):
    load_from_notion.clear()
    st.rerun()

# carrega
df = load_from_notion(NOTION_DB)

# ============== SIDEBAR (filtros) ==============
st.sidebar.markdown("## ⚙️ Filtros")
# garante estado SEMPRE antes de acessar keys
data_min, data_max = ensure_filter_state(df)

status_opts = sorted(df["Status"].dropna().unique().tolist()) if "Status" in df.columns else []
priori_opts = sorted(df["Prioridade"].dropna().unique().tolist()) if "Prioridade" in df.columns else []
setor_opts  = sorted(df["Setor"].dropna().unique().tolist()) if "Setor" in df.columns else []

status_sel = st.sidebar.multiselect("Status", options=status_opts, key="k_status")
priori_sel = st.sidebar.multiselect("Prioridade", options=priori_opts, key="k_prioridade")
setor_sel  = st.sidebar.multiselect("Setor", options=setor_opts, key="k_setor")
texto_busca = st.sidebar.text_input("Buscar (campo 'Atualizado por')", key="k_texto")
data_ini = st.sidebar.date_input("Data inicial (Término)", min_value=data_min, max_value=data_max, key="k_dataini")
data_fim = st.sidebar.date_input("Data final (Término)",   min_value=data_min, max_value=data_max, key="k_datafim")
incluir_sem_data = st.sidebar.checkbox("Incluir itens sem Data de Término", key="k_incluir_sem_data")

if st.sidebar.button("♻️ Limpar filtros"):
    st.session_state.k_status = status_opts.copy()
    st.session_state.k_prioridade = priori_opts.copy()
    st.session_state.k_setor = setor_opts.copy()
    st.session_state.k_texto = ""
    st.session_state.k_dataini, st.session_state.k_datafim = data_min, data_max
    st.session_state.k_incluir_sem_data = True
    st.rerun()

# ============== FILTROS ==============
df_f = df.copy()
if status_sel: df_f = df_f[df_f["Status"].isin(status_sel)]
if priori_sel: df_f = df_f[df_f["Prioridade"].isin(priori_sel)]
if setor_sel:  df_f = df_f[df_f["Setor"].isin(setor_sel)]
if texto_busca.strip() and "Atualizado por" in df_f.columns:
    t = texto_busca.strip().lower()
    df_f = df_f[df_f["Atualizado por"].astype(str).str.lower().str.contains(t, na=False)]

if "Data de Término" in df_f.columns:
    with_data = df_f["Data de Término"].notna()
    if incluir_sem_data:
        df_f = df_f[(~with_data) | ((df_f["Data de Término"].dt.date >= data_ini) & (df_f["Data de Término"].dt.date <= data_fim))]
    else:
        df_f = df_f[with_data & (df_f["Data de Término"].dt.date >= data_ini) & (df_f["Data de Término"].dt.date <= data_fim)]

log(f"após filtros: linhas={len(df_f)} | incluir_sem_data={incluir_sem_data}")

# ============== CABEÇALHO + KPIs ==============
st.title("📊 Dashboard de Projetos — Notion")
st.caption("Dados do Notion (botão ‘Atualizar’ na sidebar). Datas em pt-BR e visual estilo Power BI.")

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

# ============== GRÁFICOS ==============
px.defaults.template = "plotly_white"
PALETA = px.colors.qualitative.Set2

g1, g2 = st.columns(2)
if "Prioridade" in df_f.columns and not df_f.empty:
    p_counts = df_f["Prioridade"].value_counts(dropna=False).reset_index()
    p_counts.columns = ["Prioridade", "Quantidade"]
    fig_p = px.bar(p_counts, x="Prioridade", y="Quantidade", color="Prioridade", color_discrete_sequence=PALETA, title="Projetos por Prioridade")
    fig_p.update_layout(showlegend=False, margin=dict(l=10,r=10,t=60,b=10))
    g1.plotly_chart(fig_p, use_container_width=True)
else:
    g1.info("Sem dados de Prioridade.")

if "Status" in df_f.columns and not df_f.empty:
    s_counts = df_f["Status"].value_counts(dropna=False).reset_index()
    s_counts.columns = ["Status", "Quantidade"]
    fig_s = px.pie(s_counts, names="Status", values="Quantidade", hole=.5, color="Status", color_discrete_sequence=PALETA, title="Distribuição por Status")
    fig_s.update_traces(textposition="inside", textinfo="percent+label")
    fig_s.update_layout(margin=dict(l=10,r=10,t=60,b=10))
    g2.plotly_chart(fig_s, use_container_width=True)
else:
    g2.info("Sem dados de Status.")

st.markdown('<div class="section-title">Análise por Setor</div>', unsafe_allow_html=True)
if {"Setor","Status"}.issubset(df_f.columns) and not df_f.empty:
    ct = (df_f.groupby(["Setor","Status"]).size().reset_index(name="Quantidade"))
    fig_st = px.bar(ct, x="Setor", y="Quantidade", color="Status", barmode="stack", color_discrete_sequence=PALETA, title="Projetos por Setor (Empilhado por Status)")
    fig_st.update_layout(xaxis={'categoryorder':'total descending'}, margin=dict(l=10,r=10,t=60,b=10))
    st.plotly_chart(fig_st, use_container_width=True)
else:
    st.info("Sem dados suficientes para Setor x Status.")

st.markdown('<div class="section-title">Evolução Mensal (Data de Término)</div>', unsafe_allow_html=True)
df_mes = df_f.dropna(subset=["PeriodoMes"]).copy()
if not df_mes.empty:
    mc = df_mes.groupby("PeriodoMes").size().reset_index(name="Quantidade")
    mc["Label"] = mc["PeriodoMes"].dt.strftime("%Y-%m")
    mc = mc.sort_values("PeriodoMes")
    fig_m = px.line(mc, x="Label", y="Quantidade", markers=True, title="Quantidade por Mês de Término")
    fig_m.update_layout(margin=dict(l=10,r=10,t=60,b=10))
    st.plotly_chart(fig_m, use_container_width=True)
else:
    st.info("Sem datas de término para série temporal.")

st.markdown('<div class="section-title">Timeline (Gantt)</div>', unsafe_allow_html=True)
if {"Projeto","Data de Início","Data de Término"}.issubset(df_f.columns):
    gantt = df_f.dropna(subset=["Data de Início","Data de Término"]).copy()
    gantt = gantt[gantt["Data de Término"] >= gantt["Data de Início"]]
    if not gantt.empty:
        fig_g = px.timeline(gantt, x_start="Data de Início", x_end="Data de Término", y="Projeto", color="Status" if "Status" in gantt.columns else None, color_discrete_sequence=PALETA, title="Cronograma dos Projetos")
        fig_g.update_yaxes(autorange="reversed")
        fig_g.update_layout(margin=dict(l=10,r=10,t=60,b=10), height=520)
        st.plotly_chart(fig_g, use_container_width=True)
    else:
        st.info("Nenhum projeto com início e término válidos.")
else:
    st.info("Faltam colunas para montar o Gantt (Projeto, Data de Início, Data de Término).")

st.markdown('<div class="section-title">Dados Detalhados</div>', unsafe_allow_html=True)
df_view = df_f.copy()
for col in ["Data de Início", "Data de Término"]:
    if col in df_view.columns:
        df_view[col] = pd.to_datetime(df_view[col], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y").fillna("")
cols_exibir = [c for c in ["Projeto","Status","Prioridade","Setor","Atualizado por","Data de Início","Data de Término","Ano de Término","Mês de Término Nome"] if c in df_view.columns]
if cols_exibir:
    st.dataframe(df_view[cols_exibir], use_container_width=True, height=420)
else:
    st.info("Sem colunas para exibir nessa visão.")
