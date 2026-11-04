"""AI-Powered Notification Assistant - Streamlit UI.   Run:  python -m streamlit run app.py"""
import html
from datetime import datetime
import pandas as pd
import streamlit as st

from core import db
from core.categorize import Categorizer, urgency_score
from core.recommend import Recommender
from core.schedule import ACTIONS, LABELS, due_time
from core.simulator import random_notification, persona_action, random_time

st.set_page_config(page_title="Notification Assistant", page_icon="🔔", layout="wide")

CAT_STYLE = {  # emoji, text colour, background
    "work": ("", "#2D5BFF", "#E6ECFF"), "family": ("", "#D6336C", "#FFE3EE"),
    "shopping": ("", "#E67700", "#FFF0D9"), "college": ("", "#7048E8", "#EEE6FF"),
    "finance": ("", "#0B8A5F", "#DDF6EA"), "social": ("", "#0C8599", "#DDF4F8"),
}
ACTION_ICON = {"1h": "", "tonight": "", "tomorrow": "", "important": "", "ignore": ""}

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1100px;}
.hero {background:#E63946; border-radius: 20px; padding: 26px 30px; color: white; margin-bottom: 18px;
       box-shadow: 0 8px 24px rgba(230,57,70,.28);}
.hero h1 {margin:0; font-size: 2rem; color:white;}
.hero p {margin:6px 0 0; opacity:.92; font-size:1rem;}
.pill {display:inline-block; padding:4px 12px; border-radius:999px; font-size:.78rem;
       font-weight:600; margin-right:6px;}
.card {background:white; border-radius:16px; padding:18px 20px; margin-top:14px;
       box-shadow: 0 2px 12px rgba(31,36,48,.07); border:1px solid #ECEEF5;}
.card .msg {font-size:1.08rem; font-weight:600; color:#1F2430; margin:8px 0 4px;}
.card .meta {color:#7A8194; font-size:.82rem;}
.sugg {margin-top:12px; padding:12px 14px; background:#F6F4FF; border-radius:12px;
       border:1px dashed #C9C0FA; color:#3B2FA0; font-size:.95rem;}
.bar {height:6px; border-radius:6px; background:#E8E6F7; margin-top:4px; overflow:hidden;}
.bar > div {height:100%; background:linear-gradient(90deg,#6C5CE7,#4DA3FF);}
.stButton > button {border-radius:10px; font-weight:600; border:1px solid #DCDFF0;}
.stButton > button:hover {border-color:#6C5CE7; color:#6C5CE7;}
.stat {background:white; border-radius:14px; padding:14px 18px; border:1px solid #ECEEF5;
       box-shadow:0 2px 8px rgba(31,36,48,.05);}
.stat b {font-size:1.5rem; color:#6C5CE7;} .stat span {color:#7A8194; font-size:.82rem; display:block;}
[data-testid="stSidebar"] {background:#FFFFFF; border-right:1px solid #ECEEF5;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_categorizer():
    return Categorizer()

c = db.conn()
cat_model = get_categorizer()
rec = Recommender().fit(db.user_choices_df(c))

def badge(cat):
    e, fg, bg = CAT_STYLE.get(cat, ("", "#444", "#EEE"))
    return f'<span class="pill" style="color:{fg};background:{bg}">{cat}</span>'

def act(n, action, source="user"):
    now = datetime.now()
    db.log_choice(c, n["id"], n["category"], n["app"], now, n["urgency"], action, source)
    due = due_time(action, now)
    if due:
        db.add_reminder(c, n["id"], due, n["text"])
    db.set_status(c, n["id"], "ignored" if action == "ignore" else "snoozed")
    st.rerun()

# ---------------- hero ----------------
mode = (f"Learning from {rec.n} of your choices · trust {rec.trust:.0%}" if rec.pipe
        else f"Cold start · using starter rules ({rec.n}/12 choices to begin learning)")
st.markdown(f'<div class="hero"><h1>Notification Assistant</h1>'
            f'<p>Less interruption, without missing what matters.</p>'
            f'<p style="margin-top:12px"><span class="pill" style="background:rgba(255,255,255,.22);color:white">{mode}</span></p></div>',
            unsafe_allow_html=True)

n_pending = len(db.pending(c)); n_rem = len(db.reminders(c)); n_ch = len(db.user_choices_df(c))
s1, s2, s3 = st.columns(3)
s1.markdown(f'<div class="stat"><b>{n_pending}</b><span>Pending notifications</span></div>', unsafe_allow_html=True)
s2.markdown(f'<div class="stat"><b>{n_rem}</b><span>Active reminders</span></div>', unsafe_allow_html=True)
s3.markdown(f'<div class="stat"><b>{n_ch}</b><span>Choices learned from</span></div>', unsafe_allow_html=True)

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown("### Send a notification")
    with st.form("new", clear_on_submit=False):
        text = st.text_input("Message", "Can you send me the document today?")
        app_name = st.text_input("App", "Slack")
        sender = st.text_input("Sender", "Manager")
        if st.form_submit_button("Send", type="primary", use_container_width=True):
            cat, _ = cat_model.predict(text)
            db.add_notification(c, app_name, sender, text, cat, urgency_score(text))
            st.rerun()
    if st.button("Random notification", use_container_width=True):
        _, a, t = random_notification()
        pc, _ = cat_model.predict(t)
        db.add_notification(c, a, "random", t, pc, urgency_score(t)); st.rerun()
    st.divider()
    st.markdown("### Demo helpers")
    n_sim = st.slider("Simulated decisions", 20, 200, 60, 10)
    if st.button("Train with simulated user", use_container_width=True):
        for _ in range(n_sim):
            tc, a, t = random_notification()
            pc, _ = cat_model.predict(t)
            u, ts = urgency_score(t), random_time()
            nid = db.add_notification(c, a, "sim", t, pc, u, ts)
            db.log_choice(c, nid, pc, a, ts, u, persona_action(tc, ts.hour, u), "user")
            db.set_status(c, nid, "snoozed")
        st.rerun()
    if st.button("Reset all data", use_container_width=True):
        db.reset(c); st.rerun()

tab1, tab2, tab3 = st.tabs(["Inbox", "Reminders", "What it learned"])

# ---------------- inbox ----------------
with tab1:
    items = db.pending(c)
    if not items:
        st.info("Inbox zero. Send a notification from the sidebar.")
    for n in items:
        now = datetime.now()
        probs, state = rec.predict(n["category"], n["app"], n["urgency"], now)
        top = rec.best(probs)
        ranked = sorted(probs.items(), key=lambda kv: -kv[1])[:3]
        bars = "".join(
            f'<div style="margin-top:8px;font-size:.82rem">{LABELS[a]} · {p:.0%}'
            f'<div class="bar"><div style="width:{p*100:.0f}%"></div></div></div>' for a, p in ranked)
        st.markdown(
            f'<div class="card">{badge(n["category"])}'
            f'<span class="pill" style="color:#7A8194;background:#F1F2F7">{html.escape(n["app"])}</span>'
            f'<div class="msg">{html.escape(n["text"])}</div>'
            f'<div class="meta">from {html.escape(n["sender"])} · urgency {n["urgency"]:.2f}</div>'
            f'<div class="sugg"><b>Suggested: {LABELS[top]}</b> <span style="opacity:.7">({state})</span>{bars}</div></div>',
            unsafe_allow_html=True)
        cols = st.columns(len(ACTIONS) + 1)
        for col, a in zip(cols, ACTIONS):
            if col.button(f"{LABELS[a]}", key=f"{n['id']}_{a}",
                          type="primary" if a == top else "secondary", use_container_width=True):
                act(n, a)
        if cols[-1].button("Let AI decide", key=f"{n['id']}_ai", use_container_width=True):
            act(n, top, source="ai")

# ---------------- reminders ----------------
with tab2:
    rs = db.reminders(c)
    if not rs:
        st.info("No active reminders.")
    for r in rs:
        due = datetime.fromisoformat(r["due_ts"])
        overdue = due <= datetime.now()
        colr = "#D6336C" if overdue else "#6C5CE7"
        a, b = st.columns([6, 1])
        a.markdown(f'<div class="card" style="margin-top:8px;border-left:5px solid {colr}">'
                   f'<span class="pill" style="color:{colr};background:#F6F4FF">{"Due now" if overdue else "" + due.strftime("%a %d %b, %H:%M")}</span>'
                   f'<div class="msg">{html.escape(r["text"])}</div></div>', unsafe_allow_html=True)
        if b.button("Done", key=f"done{r['id']}", use_container_width=True):
            db.complete_reminder(c, r["id"]); st.rerun()

# ---------------- insights ----------------
with tab3:
    df = db.user_choices_df(c)
    if df.empty:
        st.info("Make some choices, or click 'Train with simulated user', to see patterns.")
    else:
        st.markdown("#### Your habits: category × action")
        st.dataframe(pd.crosstab(df["category"], df["action"]), use_container_width=True)
        st.markdown("#### Average hour you act on each category")
        st.bar_chart(df.groupby("category")["hour"].mean(), color="#6C5CE7")
        st.markdown("#### Try it: what would it suggest?")
        col1, col2, col3 = st.columns(3)
        cat = col1.selectbox("Category", list(df["category"].unique()))
        hr = col2.slider("Hour", 0, 23, 15)
        urg = col3.slider("Urgency", 0.0, 1.0, 0.2, 0.05)
        probs, state = rec.predict(cat, "Slack", urg, datetime.now().replace(hour=hr))
        st.bar_chart(pd.Series({LABELS[k]: v for k, v in probs.items()}), color="#4DA3FF")
        st.caption(state)
