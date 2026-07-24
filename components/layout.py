import streamlit as st


APP_VERSION = "Lumyra v1.2"


def inject_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root {
  --erp-bg:#f7f8fb; --erp-panel:#ffffff; --erp-text:#181210; --erp-muted:#6b6475;
  --erp-border:#e6ddf8; --erp-gold:#b88937; --erp-gold-2:#f8e7b1; --erp-soft:#f1ecff;
  --erp-success:#027a48; --erp-warning:#b54708; --erp-danger:#b42318; --erp-info:#175cd3;
  --erp-shadow:0 18px 45px rgba(30,41,59,.07);
}
html, body, [class*="css"] { font-family:'Inter', sans-serif; }
.stApp { background: radial-gradient(circle at top left,rgba(139,92,246,.16) 0,rgba(241,236,255,.72) 28%,#f7f8fb 100%); color:var(--erp-text); }
.block-container { max-width:1500px; padding-top:1.1rem; padding-bottom:3rem; }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#ffffff 0,#f6f1ff 100%); border-right:1px solid var(--erp-border); }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin-bottom:.25rem; }
h1,h2,h3 { color:var(--erp-text); letter-spacing:-.035em; }
.stTabs [data-baseweb="tab-list"] { gap:8px; }
.stTabs [data-baseweb="tab"] { border-radius:999px; padding:8px 14px; background:#fff; border:1px solid #e6ddf8; }
.stTabs [aria-selected="true"] { background:#4B1D95 !important; color:#fff !important; }
.stButton>button, .stDownloadButton>button { border-radius:13px !important; font-weight:800 !important; border:1px solid #B88937 !important; box-shadow:0 8px 18px rgba(143,95,52,.08); }
.stButton>button[kind="primary"] { background:#4B1D95 !important; color:#fff !important; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--erp-border); border-radius:18px; padding:14px 16px; box-shadow:0 10px 24px rgba(17,24,39,.045); }
[data-testid="stMetricValue"] { color:#4B1D95; font-weight:900; }
[data-testid="stDataFrame"] { border-radius:18px; overflow:hidden; border:1px solid #eee1d2; }
.erp-hero { background:linear-gradient(135deg,#181210,#4B1D95 58%,#B88937); color:white; border-radius:28px; padding:26px 28px; box-shadow:0 24px 60px rgba(17,24,39,.18); margin-bottom:20px; position:relative; overflow:hidden; }
.erp-hero:after { content:""; position:absolute; width:220px; height:220px; right:-70px; top:-70px; background:rgba(255,255,255,.14); border-radius:50%; }
.erp-title { font-size:1.85rem; font-weight:900; color:white; position:relative; z-index:1; }
.erp-sub { color:rgba(255,255,255,.88); margin-top:6px; font-weight:500; position:relative; z-index:1; }
.card { background:rgba(255,255,255,.96); border:1px solid var(--erp-border); border-radius:24px; padding:20px; box-shadow:var(--erp-shadow); margin-bottom:18px; }
.card-title { font-size:1.05rem; font-weight:900; color:var(--erp-text); padding-bottom:12px; margin-bottom:14px; border-bottom:1px solid #f0e7dc; }
.kpi { background:#fff; border:1px solid var(--erp-border); border-radius:20px; padding:17px; box-shadow:0 12px 28px rgba(17,24,39,.05); margin-bottom:13px; }
.kpi-label { color:var(--erp-muted); font-weight:800; font-size:.74rem; text-transform:uppercase; letter-spacing:.075em; }
.kpi-value { color:#4B1D95; font-weight:900; font-size:2rem; line-height:1.1; }
.badge,.ui-status { display:inline-flex; align-items:center; gap:6px; padding:5px 10px; border-radius:999px; font-size:.76rem; font-weight:850; border:1px solid transparent; }
.badge-ok,.ui-status-success { background:#ecfdf3; border-color:#abefc6; color:#067647; }
.badge-warn,.ui-status-warning { background:#fffaeb; border-color:#fedf89; color:#b54708; }
.badge-danger,.ui-status-danger { background:#fef3f2; border-color:#fecdca; color:#b42318; }
.ui-status-info { background:#eff8ff; border-color:#b2ddff; color:#175cd3; }
.small-muted { color:var(--erp-muted); font-size:.9rem; }
.exec-strip { background:linear-gradient(135deg,#111827,#4B1D95); color:white; border-radius:24px; padding:22px; margin-bottom:18px; box-shadow:0 20px 48px rgba(17,24,39,.16); }
.exec-strip h3 { color:white; margin:0 0 6px; }
.exec-strip p { margin:0; opacity:.92; }
.brain-card,.ui-insight-card { background:#fff; border:1px solid var(--erp-border); border-radius:18px; padding:16px; margin-bottom:12px; box-shadow:0 10px 24px rgba(17,24,39,.045); }
.brain-card-critical,.ui-insight-danger { border-left:7px solid #d92d20; }
.brain-card-warning,.ui-insight-warning { border-left:7px solid #f79009; }
.brain-card-info,.ui-insight-info { border-left:7px solid #2e90fa; }
.ui-insight-success { border-left:7px solid #12b76a; }
.brain-title,.ui-insight-title { font-weight:900; font-size:1rem; color:var(--erp-text); margin-bottom:7px; }
.brain-message,.ui-insight-message { color:#344054; line-height:1.48; margin-bottom:8px; }
.brain-rec,.ui-insight-action { color:#667085; font-size:.92rem; }
.ui-pill { float:right; background:#f2f4f7; color:#344054; padding:2px 8px; border-radius:999px; font-size:.75rem; }
.ui-metric-card { background:#fff; border:1px solid var(--erp-border); border-radius:24px; padding:18px; min-height:126px; box-shadow:var(--erp-shadow); margin-bottom:14px; position:relative; overflow:hidden; }
.ui-metric-card:after { content:""; position:absolute; right:-22px; top:-28px; width:88px; height:88px; border-radius:50%; background:#f1ecff; }
.ui-metric-top { display:flex; gap:8px; align-items:center; color:#667085; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; font-weight:850; position:relative; z-index:1; }
.ui-metric-icon { font-size:1rem; }
.ui-metric-value { color:#4B1D95; font-weight:950; font-size:2.1rem; line-height:1.05; margin-top:12px; position:relative; z-index:1; }
.ui-metric-caption { color:#667085; font-size:.88rem; margin-top:6px; position:relative; z-index:1; }
.ui-card-success:after { background:#ecfdf3; } .ui-card-warning:after { background:#fffaeb; } .ui-card-danger:after { background:#fef3f2; } .ui-card-info:after { background:#eff8ff; } .ui-card-premium:after { background:#f1ecff; }
.ui-section-header { margin:22px 0 12px; }
.ui-section-title { font-size:1.16rem; font-weight:950; letter-spacing:-.025em; color:#101828; }
.ui-section-subtitle { color:#667085; margin-top:3px; }
.ui-empty-state { background:#fff; border:1px dashed #B88937; border-radius:26px; padding:30px 24px; text-align:center; box-shadow:0 14px 34px rgba(17,24,39,.045); margin:14px 0; }
.ui-empty-icon { font-size:2.4rem; margin-bottom:10px; }
.ui-empty-title { font-weight:950; font-size:1.22rem; color:#101828; }
.ui-empty-desc { color:#667085; margin-top:6px; }
.ui-progress-card { background:#fff; border:1px solid var(--erp-border); border-radius:24px; padding:19px; box-shadow:var(--erp-shadow); margin-bottom:14px; }
.ui-progress-head { display:flex; justify-content:space-between; gap:10px; color:#101828; margin-bottom:12px; align-items:center; }
.ui-progress-track { height:13px; background:#f2f4f7; border-radius:999px; overflow:hidden; }
.ui-progress-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#4B1D95,#B88937); }
.ui-progress-caption { color:#667085; margin-top:9px; font-size:.92rem; }
.ui-banner { display:flex; gap:14px; align-items:flex-start; border-radius:22px; padding:16px 18px; margin:13px 0; border:1px solid var(--erp-border); box-shadow:0 12px 28px rgba(17,24,39,.045); }
.ui-banner-icon { font-size:1.4rem; }
.ui-banner-title { font-weight:950; color:#101828; }
.ui-banner-msg { color:#475467; margin-top:2px; }
.ui-banner-info { background:#eff8ff; border-color:#b2ddff; } .ui-banner-success { background:#ecfdf3; border-color:#abefc6; } .ui-banner-warning { background:#fffaeb; border-color:#fedf89; } .ui-banner-danger { background:#fef3f2; border-color:#fecdca; } .ui-banner-premium { background:#f1ecff; border-color:#f8e7b1; }
.ui-action-card { display:grid; grid-template-columns:76px 1fr 96px; gap:14px; align-items:center; background:#fff; border:1px solid var(--erp-border); border-radius:20px; padding:14px; margin-bottom:10px; box-shadow:0 10px 24px rgba(17,24,39,.04); }
.ui-action-step { font-weight:950; color:#4B1D95; background:#f1ecff; border-radius:14px; padding:10px; text-align:center; }
.ui-action-body b { display:block; color:#101828; } .ui-action-body span { display:block; color:#667085; margin-top:2px; }
.ui-action-marker { justify-self:end; font-size:.78rem; font-weight:900; border-radius:999px; padding:5px 9px; background:#fffaeb; color:#b54708; }
.ui-action-done .ui-action-marker { background:#ecfdf3; color:#067647; }
.sidebar-brand { padding:12px 4px 8px; }
.sidebar-title { font-size:1.2rem; font-weight:950; color:#101828; }
.sidebar-subtitle { color:#667085; font-size:.86rem; }
.sidebar-profile { background:#fff; border:1px solid #e6ddf8; border-radius:18px; padding:12px; margin:10px 0; box-shadow:0 8px 20px rgba(17,24,39,.04); }
.sidebar-category { color:#4B1D95; font-size:.72rem; letter-spacing:.11em; font-weight:950; margin:18px 0 6px; text-transform:uppercase; }
.sidebar-footer { color:#98a2b3; font-size:.78rem; text-align:center; padding:16px 0 6px; }
@media (max-width: 768px) {
  .block-container { padding-left:1rem; padding-right:1rem; }
  .erp-title { font-size:1.45rem; }
  .ui-action-card { grid-template-columns:1fr; }
  .ui-action-marker { justify-self:start; }
  .ui-metric-value { font-size:1.72rem; }
  .card { padding:16px; border-radius:20px; }
}
</style>
""",
        unsafe_allow_html=True,
    )


def header(title: str, subtitle: str) -> None:
    st.markdown(f"""
    <div class='erp-hero'>
      <div class='erp-title'>{title}</div>
      <div class='erp-sub'>{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def card_open(title: str) -> None:
    st.markdown(f"<div class='card'><div class='card-title'>{title}</div>", unsafe_allow_html=True)


def card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)
