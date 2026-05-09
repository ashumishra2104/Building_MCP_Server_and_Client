import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from src.database import get_dashboard_stats

USER_EMAIL = "demo@nomail.com"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Account")
    st.write(f"Logged in as: **{USER_EMAIL}**")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ("authenticated", "resume_text", "candidate_name", "active_profile",
                    "resume_analyzed", "resume_summary", "skill_gaps"):
            st.session_state.pop(key, None)
        st.rerun()

# ── Page ───────────────────────────────────────────────────────────────────────
st.title("📊 Dashboard")
st.caption("Your job search at a glance.")

# ── Load stats ─────────────────────────────────────────────────────────────────
if st.button("🔄 Refresh", key="dash_refresh"):
    st.session_state.pop("dash_stats", None)

if "dash_stats" not in st.session_state:
    with st.spinner("Loading stats…"):
        st.session_state["dash_stats"] = get_dashboard_stats(USER_EMAIL)

stats = st.session_state.get("dash_stats")
if not stats:
    st.error("Could not load dashboard data. Check your database connection.")
    st.stop()

totals        = stats["totals"]
new_wk        = stats["new_this_week"]
applied_total = stats["applied_total"]
applied_wk    = stats["applied_this_wk"]
by_src        = stats["applied_by_src"]
day_counts    = stats["day_counts"]
dow_counts    = stats["dow_counts"]
top_companies = stats["top_companies"]

db_total    = totals["linkedin"] + totals["naukri"] + totals["indeed"]
pending     = db_total - applied_total
new_total   = new_wk["linkedin"] + new_wk["naukri"] + new_wk["indeed"]
apply_rate  = round((applied_total / db_total * 100), 1) if db_total else 0

CARD_CSS = """
<style>
.kpi-card {
    background: #fff; border-radius: 14px; padding: 20px 24px;
    border: 1px solid #e1e4e8; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    text-align: center;
}
.kpi-value { font-size: 32px; font-weight: 800; color: #1B3A6B; line-height: 1.1; }
.kpi-label { font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase;
             letter-spacing: 0.8px; margin-top: 6px; }
.kpi-sub   { font-size: 12px; color: #C8861A; font-weight: 600; margin-top: 4px; }

.src-card {
    background: #fff; border-radius: 12px; padding: 16px 20px;
    border: 1px solid #e1e4e8; box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}
.src-title { font-size: 13px; font-weight: 700; color: #1B3A6B; margin-bottom: 10px; }
.src-row   { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }
.src-num   { font-weight: 700; color: #1a1a1a; }
.src-muted { color: #888; }
.progress-bar-bg { background: #f0f0f0; border-radius: 6px; height: 8px; margin-top: 8px; }
.progress-bar-fill { height: 8px; border-radius: 6px; }
</style>
"""
st.markdown(CARD_CSS, unsafe_allow_html=True)

# ── KPI Row ────────────────────────────────────────────────────────────────────
st.markdown("### Overview")
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{db_total:,}</div>
        <div class="kpi-label">Total Jobs in DB</div>
        <div class="kpi-sub">+{new_total} this week</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value" style="color:#166534;">{applied_total}</div>
        <div class="kpi-label">Applied</div>
        <div class="kpi-sub">+{applied_wk} this week</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value" style="color:#C8861A;">{pending:,}</div>
        <div class="kpi-label">Pending</div>
        <div class="kpi-sub">yet to apply</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value" style="color:#1967d2;">{apply_rate}%</div>
        <div class="kpi-label">Apply Rate</div>
        <div class="kpi-sub">of all jobs</div>
    </div>""", unsafe_allow_html=True)

with k5:
    top_src = max(by_src, key=by_src.get) if any(by_src.values()) else "—"
    top_src_label = top_src.capitalize() if top_src != "—" else "—"
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value" style="font-size:22px;padding-top:6px;">{top_src_label}</div>
        <div class="kpi-label">Top Source</div>
        <div class="kpi-sub">{by_src.get(top_src,0)} applications</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Source breakdown ───────────────────────────────────────────────────────────
st.markdown("### Source Breakdown")

src_colors = {"linkedin": "#0077b5", "naukri": "#ff751a", "indeed": "#2557a7"}
src_icons  = {"linkedin": "🏢", "naukri": "💼", "indeed": "🔵"}

s1, s2, s3 = st.columns(3)
for col, src in zip([s1, s2, s3], ["linkedin", "naukri", "indeed"]):
    total_src   = totals[src]
    applied_src = by_src[src]
    pending_src = total_src - applied_src
    pct         = round(applied_src / total_src * 100, 1) if total_src else 0
    color       = src_colors[src]
    with col:
        st.markdown(f"""<div class="src-card">
<div class="src-title">{src_icons[src]} {src.capitalize()}</div>
<div class="src-row"><span class="src-muted">Total in DB</span><span class="src-num">{total_src:,}</span></div>
<div class="src-row"><span class="src-muted">Applied</span><span class="src-num" style="color:#166534;">{applied_src}</span></div>
<div class="src-row"><span class="src-muted">Pending</span><span class="src-num" style="color:#C8861A;">{pending_src:,}</span></div>
<div class="src-row"><span class="src-muted">Apply Rate</span><span class="src-num">{pct}%</span></div>
<div class="progress-bar-bg">
  <div class="progress-bar-fill" style="width:{pct}%;background:{color};"></div>
</div>
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row 1: Day-wise + Donut ────────────────────────────────────────────
st.markdown("### Application Activity")
chart1, chart2 = st.columns([3, 2])

with chart1:
    st.markdown("**📈 Day-wise Applications**")
    if day_counts:
        # Fill in missing dates with 0
        if day_counts:
            all_dates = sorted(day_counts.keys())
            start     = datetime.strptime(all_dates[0], "%Y-%m-%d")
            end       = datetime.today()
            date_range = [(start + timedelta(days=i)).strftime("%Y-%m-%d")
                          for i in range((end - start).days + 1)]
            filled = {d: day_counts.get(d, 0) for d in date_range}
        else:
            filled = {}

        df_day = pd.DataFrame({"Date": list(filled.keys()), "Applications": list(filled.values())})
        fig_bar = go.Figure(go.Bar(
            x=df_day["Date"],
            y=df_day["Applications"],
            marker_color="#1B3A6B",
            marker_line_width=0,
            hovertemplate="%{x}<br>Applications: %{y}<extra></extra>",
        ))
        fig_bar.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=260,
            plot_bgcolor="#fff",
            paper_bgcolor="#fff",
            xaxis=dict(type="category", showgrid=False, tickfont=dict(size=10),
                       tickangle=-30),
            yaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickfont=dict(size=10),
                       dtick=1, rangemode="tozero"),
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No applications yet — start applying to see your activity chart.")

with chart2:
    st.markdown("**🍩 By Source**")
    src_labels = ["LinkedIn", "Naukri", "Indeed"]
    src_values = [by_src["linkedin"], by_src["naukri"], by_src["indeed"]]
    if sum(src_values) > 0:
        fig_donut = go.Figure(go.Pie(
            labels=src_labels,
            values=src_values,
            hole=0.55,
            marker_colors=["#0077b5", "#ff751a", "#2557a7"],
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            textfont=dict(size=12),
        ))
        fig_donut.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=260,
            paper_bgcolor="#fff",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(size=11)),
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No applications yet.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row 2: Day-of-week + Top Companies ──────────────────────────────────
st.markdown("### Patterns & Leaders")
chart3, chart4 = st.columns([2, 3])

with chart3:
    st.markdown("**📅 Day-of-Week Pattern**")
    dow_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dow_values = [dow_counts.get(i, 0) for i in range(7)]
    if sum(dow_values) > 0:
        fig_dow = go.Figure(go.Bar(
            x=dow_labels,
            y=dow_values,
            marker_color=["#C8861A" if v == max(dow_values) else "#d0daea" for v in dow_values],
            marker_line_width=0,
            hovertemplate="%{x}: %{y} applications<extra></extra>",
        ))
        fig_dow.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=240,
            plot_bgcolor="#fff",
            paper_bgcolor="#fff",
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="#f0f0f0", dtick=1,
                       rangemode="tozero", tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_dow, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No applications yet.")

with chart4:
    st.markdown("**🏢 Top Companies Applied To**")
    if top_companies:
        df_co = pd.DataFrame(top_companies, columns=["Company", "Applications"])
        fig_co = go.Figure(go.Bar(
            x=df_co["Applications"],
            y=df_co["Company"],
            orientation="h",
            marker_color="#1B3A6B",
            marker_line_width=0,
            hovertemplate="%{y}: %{x} applications<extra></extra>",
        ))
        fig_co.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=240,
            plot_bgcolor="#fff",
            paper_bgcolor="#fff",
            xaxis=dict(showgrid=True, gridcolor="#f0f0f0", dtick=1,
                       rangemode="tozero", tickfont=dict(size=10)),
            yaxis=dict(showgrid=False, tickfont=dict(size=11),
                       categoryorder="total ascending"),
        )
        st.plotly_chart(fig_co, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Apply to some jobs to see your top companies.")

# ── New jobs this week detail ──────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🆕 New Jobs Added This Week")
n1, n2, n3 = st.columns(3)
for col, src, icon in zip([n1, n2, n3],
                           ["linkedin", "naukri", "indeed"],
                           ["🏢", "💼", "🔵"]):
    with col:
        st.metric(label=f"{icon} {src.capitalize()}", value=new_wk[src],
                  delta=f"of {totals[src]:,} total")
