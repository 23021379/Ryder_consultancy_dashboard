import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
from datetime import datetime

st.set_page_config(page_title="Jebex - Nursing Workstation", layout="wide")

# same CSS pattern as the solar dashboard - light cards on a soft background
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.05);
        background: #ffffff;
        border: 1px solid #eaeaea;
        padding: 10px 15px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2b3a55;
    }
    .stApp {
        background-color: #f7f9fc;
        color: #1a2b4c;
    }
    p, span, label, div.stMarkdown, div.stText {
        color: #1a2b4c;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATA
# =============================================================================
PATIENTS = [
    {"id": "P-4012", "name": "M. Almasi",   "age": 68, "sex": "M", "room": "412",
     "dx": "Post-op day 1, hip arthroplasty",
     "hr": 78,  "bp": "128/82", "spo2": 97, "rr": 16, "temp": 37.1, "risk": 32, "trend": "stable"},
    {"id": "P-4018", "name": "C. Okonkwo",  "age": 54, "sex": "F", "room": "418",
     "dx": "CHF exacerbation, IV diuretics",
     "hr": 102, "bp": "154/96", "spo2": 92, "rr": 22, "temp": 37.6, "risk": 71, "trend": "rising"},
    {"id": "P-4023", "name": "J. Lindqvist","age": 81, "sex": "F", "room": "423",
     "dx": "Pneumonia, day 3 IV abx",
     "hr": 118, "bp": "92/58",  "spo2": 88, "rr": 26, "temp": 38.7, "risk": 88, "trend": "critical"},
    {"id": "P-4007", "name": "R. Patel",    "age": 45, "sex": "M", "room": "407",
     "dx": "Cholecystectomy, day 0",
     "hr": 84,  "bp": "132/80", "spo2": 98, "rr": 14, "temp": 36.9, "risk": 18, "trend": "stable"},
    {"id": "P-4031", "name": "S. Diallo",   "age": 72, "sex": "M", "room": "431",
     "dx": "COPD, oxygen therapy",
     "hr": 92,  "bp": "138/86", "spo2": 90, "rr": 20, "temp": 37.2, "risk": 54, "trend": "watch"},
    {"id": "P-4029", "name": "E. Kowalski", "age": 33, "sex": "F", "room": "429",
     "dx": "Cellulitis, IV abx",
     "hr": 88,  "bp": "118/74", "spo2": 99, "rr": 16, "temp": 37.9, "risk": 26, "trend": "stable"},
]

NURSES = [
    {"id": "N1", "name": "Aicha Ndiaye",  "role": "RN - Charge", "ratio": 4},
    {"id": "N2", "name": "Jordan Mehta",  "role": "RN",          "ratio": 5},
    {"id": "N3", "name": "Sara Lindgren", "role": "RN",          "ratio": 6},
    {"id": "N4", "name": "Tomas Rivera",  "role": "LPN",         "ratio": 7},
]

TASKS = [
    {"id": "T1", "patient": "P-4023", "text": "Recheck SpO2, escalate if <90%",        "urgency": 95, "type": "critical", "assigned": "N1"},
    {"id": "T2", "patient": "P-4018", "text": "Administer IV furosemide 40mg",         "urgency": 82, "type": "critical", "assigned": "N2"},
    {"id": "T3", "patient": "P-4012", "text": "Post-op pain reassessment",             "urgency": 60, "type": "warn",     "assigned": "N3"},
    {"id": "T4", "patient": "P-4031", "text": "Reposition, skin assessment",           "urgency": 45, "type": "warn",     "assigned": "N4"},
    {"id": "T5", "patient": "P-4007", "text": "Discharge teaching - wound care",       "urgency": 38, "type": "ok",       "assigned": "N3"},
    {"id": "T6", "patient": "P-4029", "text": "Antibiotic dose due 14:00",             "urgency": 70, "type": "warn",     "assigned": "N2"},
    {"id": "T7", "patient": "P-4012", "text": "Hourly fluid intake check",             "urgency": 30, "type": "ok",       "assigned": "N1"},
    {"id": "T8", "patient": "P-4007", "text": "Update care plan",                      "urgency": 22, "type": "ok",       "assigned": "N4"},
]

INVENTORY = [
    {"name": "Sterile gloves (M)",    "sku": "GL-M-01",   "qty": 14,  "par": 80,  "loc": "Supply A-3"},
    {"name": "0.9% Saline 1L",        "sku": "SAL-1L",    "qty": 9,   "par": 24,  "loc": "Pharmacy"},
    {"name": "Insulin syringe 0.5mL", "sku": "IS-05",     "qty": 142, "par": 200, "loc": "Med room"},
    {"name": "Paracetamol 500mg",     "sku": "APAP-500",  "qty": 38,  "par": 120, "loc": "Med cart"},
    {"name": "PPE gown",              "sku": "PPE-GN",    "qty": 6,   "par": 50,  "loc": "Anteroom"},
    {"name": "IV cannula 20G",        "sku": "IV-20",     "qty": 88,  "par": 150, "loc": "Procedure rm"},
]

EQUIPMENT = [
    {"name": "Bladder scanner #2",      "last": "Room 418 - 11:24",  "status": "in-use"},
    {"name": "IV pump #14",             "last": "Storage B - 09:10", "status": "available"},
    {"name": "Vital signs monitor #7",  "last": "Room 423",          "status": "in-use"},
    {"name": "EKG machine",             "last": "Cardiology cart",   "status": "available"},
    {"name": "Pulse oximeter (port.)",  "last": "Nurse station",     "status": "available"},
]

FAQ = {
    "When can I eat after my surgery?":
        "Most patients can resume a clear liquid diet 4-6 hours after general anaesthetic, "
        "advancing to soft foods as tolerated. Your surgical team will confirm based on your specific procedure.",
    "How often should I take my medication?":
        "Your discharge sheet lists each medication's dose and frequency. Setting a phone alarm is one of the most "
        "effective reminders. I can send a reminder schedule to your phone if you'd like.",
    "When can I shower?":
        "Generally 24-48 hours after surgery, keeping the dressing dry. No bathing or swimming until your incision "
        "has fully healed (typically 10-14 days). Your discharge instructions are specific to your case.",
    "What are my warning signs?":
        "Call your nurse or seek urgent care if you have: fever above 38.5C, increasing redness or pus at the "
        "incision, chest pain, shortness of breath, or worsening pain unrelieved by your medication.",
    "What's my pain medication called?":
        "I cannot prescribe or change medications. Your current schedule is on your discharge sheet. "
        "For a clinical question, I'll page your nurse.",
}

ALERT_FEED = [
    {"type":"crit", "ts":"12:48", "patient":"J. Lindqvist", "msg":"NEWS2 = 9 - persistent hypoxia + tachypnoea"},
    {"type":"warn", "ts":"12:39", "patient":"C. Okonkwo",   "msg":"BP trending down - 154/96 to 138/82 over 2h"},
    {"type":"info", "ts":"12:31", "patient":"M. Almasi",    "msg":"Pain score 4 - PRN analgesia given"},
    {"type":"muted","ts":"12:28", "patient":"S. Diallo",    "msg":"AI flag: SpO2 transient dip - non-actionable"},
    {"type":"muted","ts":"12:14", "patient":"E. Kowalski",  "msg":"AI flag: HR variability - non-actionable"},
    {"type":"warn", "ts":"12:02", "patient":"J. Lindqvist", "msg":"Lactate 3.4 mmol/L - sepsis bundle?"},
    {"type":"info", "ts":"11:55", "patient":"R. Patel",     "msg":"Discharge orders ready"},
    {"type":"muted","ts":"11:48", "patient":"M. Almasi",    "msg":"AI flag: posture change - non-actionable"},
]


# =============================================================================
# Common Plotly styling for the light theme
# =============================================================================
def style_plotly(fig, height=300):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="#f7f9fc",
        font=dict(family="-apple-system, system-ui, sans-serif", size=11, color="#1a2b4c"),
        margin=dict(l=40, r=20, t=30, b=40),
        height=height,
        legend=dict(orientation="h", y=-0.2, font=dict(size=10, color="#1a2b4c")),
    )
    fig.update_xaxes(gridcolor="#eaeaea", linecolor="#cdd2dc")
    fig.update_yaxes(gridcolor="#eaeaea", linecolor="#cdd2dc")
    return fig


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
st.sidebar.title("Jebex")
st.sidebar.caption("AI-Augmented Nursing Workstation")

section = st.sidebar.radio(
    "Module",
    [
        "01 - Documentation",
        "02 - Patient monitoring",
        "03 - Task prioritisation",
        "04 - Staffing & rostering",
        "05 - Routine automation",
        "06 - Decision support",
        "07 - Patient communication",
        "08 - Staff wellbeing",
        "Trust & safety - Known limitations",
    ],
)

st.sidebar.divider()
ai_on = st.sidebar.toggle("AI features", value=True)
compare = st.sidebar.toggle("Compare AI vs manual", value=False)
st.sidebar.divider()
st.sidebar.caption(f"Shift: Day - 07:00-19:00")
st.sidebar.caption(f"Local time: {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.caption("Ward: 4-North - User: Aicha N. (RN, Charge)")

# =============================================================================
# SECTION 1 - DOCUMENTATION
# =============================================================================
def render_documentation():
    st.title("Clinical Documentation")
    st.markdown("Voice-driven note capture with auto-populated vitals from the patient monitor. "
                "Drafts must be reviewed and signed by the responsible nurse - no chart entry is final without explicit human verification.")

    col_controls, col_display = st.columns([1, 3])

    with col_controls:
        st.subheader("Controls")
        patient_options = [f"{p['name']} - Rm {p['room']}" for p in PATIENTS]
        selected_patient = st.selectbox("Patient", options=patient_options, index=0)
        sig_required = st.checkbox("Require co-signature", value=False)
        flag_low_conf = st.checkbox("Flag low-confidence terms", value=True)

        st.divider()
        st.markdown("**Auto-populated vitals**")
        vitals = [("Heart rate","82 bpm"),("BP","128/82"),("SpO2","97 %"),
                  ("RR","16"),("Temp","37.1 C"),("Pain","- manual -")]
        for label, value in vitals:
            st.text(f"{label:<12} {value}")

    with col_display:
        st.subheader("Draft Note")

        if "doc_transcript" not in st.session_state:
            st.session_state.doc_transcript = ""
        if "doc_note" not in st.session_state:
            st.session_state.doc_note = ""

        b1, b2 = st.columns([1, 4])
        with b1:
            if st.button("Start dictation", type="primary", use_container_width=True):
                st.session_state.doc_transcript = (
                    "Patient seen on rounds at oh-eight-fifteen. Reports pain four out of ten at the "
                    "surgical site. Vital signs reviewed and within expected post-operative range. "
                    "Wound dressing intact, no exudate noted. Patient ambulated with assistance to chair. "
                    "Tolerated mobilisation with mild discomfort. Will reassess pain in thirty minutes "
                    "following analgesia."
                )
                st.session_state.doc_note = (
                    "S: Patient reports pain 4/10 at surgical site, otherwise no new complaints.\n\n"
                    "O: Vital signs stable: HR 82, BP 128/82, SpO2 97%, RR 16, T 37.1 C.\n"
                    "   Wound dressing intact, no exudate noted.\n"
                    "   Patient ambulated with assistance to chair, tolerated with mild discomfort.\n\n"
                    "A: Post-op day 1 progressing as expected. Pain controlled with PRN analgesia.\n\n"
                    "P: Continue mobilisation per order set. Reassess pain 30 min post-PRN.\n"
                    "   Continue DVT prophylaxis. Review with surgical team on AM round."
                )
        with b2:
            transcript_display = st.session_state.doc_transcript or "Live transcript will appear here once dictation starts."
            st.info(transcript_display)

        st.session_state.doc_note = st.text_area(
            "Draft nursing note (AI-generated)",
            value=st.session_state.doc_note,
            height=240,
            placeholder="Draft note will populate after dictation...",
        )

        st.divider()
        st.write("### Documentation Metrics")

        with st.container(border=True):
            st.markdown("**Time savings & verification**")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Time per chart entry", "3.2 min", "-72% vs unaided")
            m2.metric("Unaided baseline",     "11.4 min")
            m3.metric("Low-conf terms",       "3 flagged")
            m4.metric("Sig. status",          "Unsigned")

        with st.container(border=True):
            st.markdown("**AI Suggested care plan (model conf 78%)**")
            st.markdown(
                "- Hourly neuro checks x4\n"
                "- Mobilise to chair within 24h post-op\n"
                "- DVT prophylaxis: enoxaparin per protocol\n"
                "- Pain reassessment 30 min post-analgesia"
            )

        bb1, bb2, bb3 = st.columns(3)
        with bb1:
            if st.button("Discard draft", use_container_width=True):
                st.session_state.doc_note = ""
                st.session_state.doc_transcript = ""
                st.rerun()
        with bb2:
            if st.button("Save unsigned", use_container_width=True):
                st.toast("Draft saved (unsigned)")
        with bb3:
            if st.button("Review & sign", type="primary", use_container_width=True):
                st.toast("Note signed and committed to chart")

        st.divider()
        st.warning("**Verification required.** Speech-to-text models mishear roughly 1 in 80 medical terms in noisy "
                   "ward environments. Review every entry before signing.")
        st.error("**Limitation seen in trials.** Generative drafts can fabricate plausible-sounding observations "
                 "the patient did not have. Read every line before signing.")
        if compare:
            st.info("**Compare mode.** A 2023 study at four UK trusts found ambient documentation tools cut nurse "
                    "charting time by 38-72% - but added 2-4 min/chart of *review* time. Net gain depends on "
                    "disciplined verification habits.")


# =============================================================================
# SECTION 2 - PATIENT MONITORING
# =============================================================================
def render_monitoring():
    st.title("Patient Monitoring & Deterioration Risk")
    st.markdown("Continuous vital sign analysis with NEWS2-anchored AI risk scoring. The system surfaces patterns "
                "earlier than thresholds alone - but at the cost of false positives that, unchecked, drive alert fatigue.")

    col_controls, col_display = st.columns([1, 3])

    with col_controls:
        st.subheader("Controls")
        risk_filter = st.select_slider("Min risk to display", options=[0, 25, 50, 70, 90], value=0)
        sort_by     = st.radio("Sort by", ["Risk (high to low)", "Room number", "Trend"])
        mute_fp     = st.checkbox("Bundle low-priority alerts hourly", value=True)
        show_muted  = st.checkbox("Show muted AI flags in feed", value=True)

    with col_display:
        st.subheader("Ward 4-North Overview")

        with st.container(border=True):
            st.markdown("**Surveillance KPIs**")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Active patients",       "6",   "across ward 4-North")
            k2.metric("High-risk now",         "2",   "EWS >= 7 or AI risk >= 70")
            k3.metric("Alerts last 8h",        "47",  "31 actionable")
            k4.metric("False-positive rate",   "34%", "8h rolling")

        st.warning("**Alert fatigue is the #1 documented harm** from clinical AI surveillance systems. "
                   "Jebex bundles low-priority signals into hourly digests rather than pinging in real time.")

        st.divider()
        st.write("### Patients")

        # Sort and filter
        plist = [p for p in PATIENTS if p["risk"] >= risk_filter]
        if sort_by == "Risk (high to low)":
            plist = sorted(plist, key=lambda p: -p["risk"])
        elif sort_by == "Room number":
            plist = sorted(plist, key=lambda p: p["room"])
        else:
            order = {"critical": 0, "rising": 1, "watch": 2, "stable": 3}
            plist = sorted(plist, key=lambda p: order.get(p["trend"], 99))

        for i in range(0, len(plist), 2):
            cols = st.columns(2)
            for j, c in enumerate(cols):
                if i + j >= len(plist):
                    continue
                p = plist[i + j]
                with c, st.container(border=True):
                    risk_label = "critical" if p["risk"] >= 70 else "elevated" if p["risk"] >= 50 else "low"
                    st.markdown(f"**{p['name']}** - Rm {p['room']} ({p['sex']}, {p['age']})")
                    st.caption(p["dx"])
                    v1, v2, v3, v4, v5, v6 = st.columns(6)
                    v1.metric("HR",   p["hr"])
                    v2.metric("BP",   p["bp"])
                    v3.metric("SpO2", p["spo2"])
                    v4.metric("RR",   p["rr"])
                    v5.metric("Temp", p["temp"])
                    v6.metric("Risk", f"{p['risk']}", risk_label)

        st.divider()
        st.write("### Live alert feed")
        feed = [a for a in ALERT_FEED if show_muted or a["type"] != "muted"]
        for a in feed:
            line = f"`{a['ts']}` - **{a['patient']}** - {a['msg']}"
            if a["type"] == "crit":
                st.error(line)
            elif a["type"] == "warn":
                st.warning(line)
            elif a["type"] == "info":
                st.info(line)
            else:
                st.caption(line)


# =============================================================================
# SECTION 3 - TASK PRIORITISATION
# =============================================================================
def render_tasks():
    st.title("Task Prioritisation Across the Shift")
    st.markdown("AI re-ranks the ward worklist by clinical urgency, time-criticality, and assigned nurse load. "
                "Toggle between manual and AI-assisted views - the difference is sometimes subtle, sometimes dramatic.")

    col_controls, col_display = st.columns([1, 3])

    with col_controls:
        st.subheader("Controls")
        mode      = st.radio("View mode", ["AI-assisted", "Manual"])
        nurse_pick = st.selectbox("Filter by nurse", options=["All"] + [n["name"] for n in NURSES])
        min_urg   = st.slider("Min urgency", 0, 100, 0, 5)

    with col_display:
        st.subheader(f"Worklist - ward 4-North ({mode})")

        st.info("**Watch for automation bias.** When AI lists tasks in order, clinicians complete them in that "
                "order 84% of the time - even when their own judgement disagrees.")

        nurse_lookup = {n["id"]: n["name"] for n in NURSES}
        tlist = [t for t in TASKS if t["urgency"] >= min_urg]
        if nurse_pick != "All":
            tlist = [t for t in tlist if nurse_lookup[t["assigned"]] == nurse_pick]

        if mode == "AI-assisted":
            tlist = sorted(tlist, key=lambda t: -t["urgency"])
        else:
            tlist = sorted(tlist, key=lambda t: t["id"])

        with st.container(border=True):
            st.markdown("**Active tasks**")
            df = pd.DataFrame([{
                "ID":       t["id"],
                "Task":     t["text"],
                "Patient":  t["patient"],
                "Nurse":    nurse_lookup[t["assigned"]],
                "Urgency":  t["urgency"],
                "Type":     t["type"],
            } for t in tlist])
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.caption("AI ranks by composite of: NEWS2 trajectory, medication time-window, documentation gaps, "
                   "and nurse availability. It does *not* see psychosocial context.")

        st.divider()
        st.write("### Workload Distribution")

        load_by_nurse = {}
        for t in TASKS:
            load_by_nurse[t["assigned"]] = load_by_nurse.get(t["assigned"], 0) + t["urgency"]
        max_load = max(load_by_nurse.values()) if load_by_nurse else 1

        with st.container(border=True):
            st.markdown("**Estimated load per nurse**")
            cols = st.columns(len(NURSES))
            for col, n in zip(cols, NURSES):
                load = load_by_nurse.get(n["id"], 0)
                pct = int((load / max_load) * 100) if max_load else 0
                col.metric(n["name"], f"{load} pts", f"{pct}% of busiest")
                col.caption(n["role"])

        st.info("**Suggested rebalance:** move task `T6` from Jordan (over capacity) to Aicha.")
        if st.button("Apply rebalance", type="primary"):
            st.toast("Rebalance applied - T6 reassigned to Aicha")


# =============================================================================
# SECTION 4 - STAFFING & ROSTERING
# =============================================================================
def render_staffing():
    st.title("Staffing & Predictive Rostering")
    st.markdown("Forecasts patient acuity from historic admission patterns and current ward state. "
                "Use the sliders to plan the next shift - the system flags unsafe nurse-to-patient ratios immediately.")

    col_controls, col_display = st.columns([1, 3])

    with col_controls:
        st.subheader("Controls")
        st.markdown("**Adjust roster (next shift)**")
        rn  = st.slider("RN - day shift",  2, 8, 5)
        lpn = st.slider("LPN - day shift", 0, 4, 2)
        hca = st.slider("HCA - day shift", 0, 4, 2)
        st.divider()
        ward_patients = st.number_input("Forecast patient census", min_value=10, max_value=60, value=27, step=1)

    with col_display:
        st.subheader("Forecast & Roster Outcome")

        ratio = ward_patients / rn if rn else 99

        with st.container(border=True):
            st.markdown("**Workforce KPIs**")
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Current ratio",   "1 : 4.5",      "RN to patient avg")
            k2.metric("Predicted peak",  "17:00-19:00", "+3 admits expected")
            k3.metric("Sick-call risk",  "12%",         "90-day pattern")
            k4.metric("Acuity trend",    "Stable",      "vs 4-week baseline")
            k5.metric("Projected ratio", f"1 : {ratio:.1f}",
                      "safe" if ratio <= 5 else "upper limit" if ratio <= 6 else "UNSAFE")

        st.divider()
        st.write("### Predicted Demand vs Scheduled Staff")

        hours     = [f"{h:02d}:00" for h in range(24)]
        demand    = [max(8, round(18 + 12 * math.sin((h - 6) * math.pi / 12) + (3 if 16 <= h <= 19 else 0))) for h in range(24)]
        scheduled = [(rn + lpn + hca) if 7 <= h < 19 else max(3, rn // 2) for h in range(24)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hours, y=demand, mode="lines", name="Predicted demand",
                                 line=dict(color="#2b3a55", width=2.5),
                                 fill="tozeroy", fillcolor="rgba(43,58,85,0.10)"))
        fig.add_trace(go.Scatter(x=hours, y=scheduled, mode="lines+markers", name="Scheduled staff",
                                 line=dict(color="#5fa4d8", width=2, dash="dash"),
                                 marker=dict(size=5)))
        st.plotly_chart(style_plotly(fig, height=320), use_container_width=True, config={"displayModeBar": False})

        if ratio <= 5:
            st.success(f"**Projected ratio: 1:{ratio:.1f}** - within safe range for med-surg ward (target <= 1:6).")
        elif ratio <= 6:
            st.warning(f"**Projected ratio: 1:{ratio:.1f}** - acceptable but at upper safe limit.")
        else:
            st.error(f"**Projected ratio: 1:{ratio:.1f}** - UNSAFE. Increase RN coverage.")

        st.info("**Ethical note.** Predictive rostering must never be used to justify chronic understaffing by "
                "treating the model's forecast as an upper bound on safe staffing.")

        st.caption("Demand forecasting models systematically under-predict surges driven by external events "
                   "(e.g. flu outbreaks, local disasters). Always cross-check with bed manager reports.")


# =============================================================================
# SECTION 5 - ROUTINE AUTOMATION
# =============================================================================
def render_routine():
    st.title("Automation of Routine Tasks")
    st.markdown("Inventory monitoring, equipment location, and supply reordering - the ambient layer that gives "
                "nurses back the minutes lost to fetching, hunting, and counting.")

    col_controls, col_display = st.columns([1, 3])

    with col_controls:
        st.subheader("Controls")
        show_low      = st.checkbox("Show only low-stock (<50% par)", value=False)
        show_avail    = st.radio("Equipment status", ["All", "Available only", "In-use only"])
        loc_filter    = st.selectbox("Inventory location",
                                     options=["All"] + sorted({i["loc"] for i in INVENTORY}))

    with col_display:
        st.subheader("Logistics Overview")

        with st.container(border=True):
            st.markdown("**Operational KPIs**")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Interruptions avoided", "42",    "approx 1h 24m saved")
            k2.metric("Doses logged today",    "312",   "0 manual re-entries")
            k3.metric("Hand-hygiene",          "71%",   "target 85%")
            k4.metric("Specimen tracking",     "98.4%", "no losses since 14 March")

        st.divider()
        st.write("### Inventory & Supplies (auto-tracked)")

        inv = INVENTORY
        if show_low:
            inv = [i for i in inv if i["qty"] / i["par"] < 0.5]
        if loc_filter != "All":
            inv = [i for i in inv if i["loc"] == loc_filter]

        with st.container(border=True):
            df = pd.DataFrame([{
                "Item":     i["name"],
                "SKU":      i["sku"],
                "Qty":      i["qty"],
                "Par":      i["par"],
                "% of par": round(i["qty"] / i["par"] * 100, 0),
                "Location": i["loc"],
            } for i in inv])
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "% of par": st.column_config.ProgressColumn(
                        "% of par", min_value=0, max_value=100, format="%d%%"
                    ),
                },
            )
        st.warning("**Limitation:** RFID tags fail in roughly 3% of items per month. Periodic physical audits are still required.")

        st.divider()
        st.write("### Equipment Finder (RTLS)")

        eq = EQUIPMENT
        if show_avail == "Available only":
            eq = [e for e in eq if e["status"] == "available"]
        elif show_avail == "In-use only":
            eq = [e for e in eq if e["status"] == "in-use"]

        with st.container(border=True):
            df_eq = pd.DataFrame([{
                "Equipment":     e["name"],
                "Last seen":     e["last"],
                "Status":        e["status"],
            } for e in eq])
            st.dataframe(df_eq, use_container_width=True, hide_index=True)

        st.caption("Last-known location is not current location. The system can tell you where it was 30 seconds "
                   "ago, not whether it is clean, charged, or actually working.")


# =============================================================================
# SECTION 6 - CLINICAL DECISION SUPPORT
# =============================================================================
def render_cdss():
    st.title("Clinical Decision Support")
    st.markdown("Medication interaction checks, abnormal lab flags, and a consultable AI second opinion. None of "
                "these replace clinical judgement; all are designed to be explainable and dismissible.")

    col_controls, col_display = st.columns([1, 3])

    with col_controls:
        st.subheader("Controls")
        sev_filter = st.multiselect("Severity to display", options=["critical", "warning", "info"],
                                    default=["critical", "warning", "info"])
        show_meds = st.checkbox("Medication alerts", value=True)
        show_labs = st.checkbox("Abnormal lab flags", value=True)
        show_ai   = st.checkbox("AI second opinion",   value=True)

    with col_display:
        st.subheader("Active Decision Support")

        st.error("**AI supports decisions - final judgement remains with the clinician.** Every recommendation here "
                 "can be overridden. Overrides are logged for audit but do not require justification - protecting "
                 "clinician autonomy is part of safe deployment.")

        with st.container(border=True):
            st.markdown("**CDSS KPIs**")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Active alerts",      "8",   "+2 last hour")
            k2.metric("Severe interactions","1",   "blocked at order entry")
            k3.metric("Override rate",      "31%", "last 7 days")
            k4.metric("Avg response time",  "94 s", "from alert to action")

        st.divider()

        if show_meds:
            st.write("### Active medication alerts")
            with st.container(border=True):
                if "critical" in sev_filter:
                    st.error("**Drug interaction - severe (BLOCK)**\n\nSpironolactone + lisinopril in patient "
                             "with eGFR 38 - risk of hyperkalaemia. Consider potassium check before next dose. "
                             "_Patient C. Okonkwo, order entered 11:42_")
                if "warning" in sev_filter:
                    st.warning("**Renal dosing (VERIFY)**\n\nVancomycin dosing for J. Lindqvist (CrCl 42) - "
                               "current order assumes normal renal function.")
                if "info" in sev_filter:
                    st.info("**Allergy reconciliation (INFO)**\n\nPenicillin allergy on file - currently ordered "
                            "cephalosporin. Documented as 'rash, age 7': cross-reactivity risk < 1%. _Patient R. Patel_")

        if show_labs:
            st.divider()
            st.write("### Abnormal lab flags")
            with st.container(border=True):
                if "critical" in sev_filter:
                    st.error("**K+ 5.9 mmol/L - Critical high**\n\nPatient C. Okonkwo - up from 4.3 (24h). "
                             "ECG indicated. Hold spironolactone.")
                if "warning" in sev_filter:
                    st.warning("**Lactate 3.4 mmol/L - High**\n\nPatient J. Lindqvist - sepsis bundle suggested if "
                               "not initiated.")
                if "info" in sev_filter:
                    st.info("**Hb 10.2 g/dL - Trending down**\n\nPatient M. Almasi - post-op day 1. Within expected "
                            "range, flagged for trend awareness only.")

        if show_ai:
            st.divider()
            st.write("### AI second opinion (consult)")
            with st.container(border=True):
                st.markdown(
                    "**Query 12:14**\n\n"
                    "_Patient with rising RR (16-26 over 4h), SpO2 88% on 2L NC, T 38.7. Already on day 3 IV "
                    "abx for CAP. Differential?_\n\n"
                    "**AI response (reasoning confidence 68%)**\n\n"
                    "Trajectory consistent with clinical worsening despite treatment. Differentials to consider: "
                    "**treatment failure** (resistant organism / wrong antibiotic), **complication** (empyema, "
                    "ARDS), **secondary process** (PE, MI, sepsis). Recommend: arterial blood gas, repeat CXR, "
                    "lactate, blood cultures, and rapid review by medical team."
                )
                b1, b2 = st.columns(2)
                with b1: st.button("Disagree / log", use_container_width=True, key="cdss_dis")
                with b2: st.button("Page MRP", type="primary", use_container_width=True, key="cdss_pg")

        st.info("**Why AI sometimes underperforms in CDSS:** models trained on US/EU data may misread populations "
                "they were not trained on. Always check whether your hospital validated the model on patients "
                "like yours before trusting confidence scores.")


# =============================================================================
# SECTION 7 - PATIENT COMMUNICATION
# =============================================================================
def render_communication():
    st.title("Patient Communication & Chatbot")
    st.markdown("A bedside FAQ assistant for non-clinical questions, discharge instruction summaries, and "
                "medication reminders. Hands clinical questions back to a human nurse, every time.")

    col_controls, col_display = st.columns([1, 3])

    with col_controls:
        st.subheader("Controls")
        st.markdown("**Quick FAQ chips**")
        for i, q in enumerate(FAQ.keys()):
            if st.button(q, key=f"chip_{i}", use_container_width=True):
                if "chat_msgs" not in st.session_state:
                    st.session_state.chat_msgs = []
                st.session_state.chat_msgs.append({"role": "user", "text": q})
                st.session_state.chat_msgs.append({"role": "bot", "text": FAQ[q]})
                st.rerun()

        st.divider()
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.chat_msgs = []
            st.rerun()

    with col_display:
        st.subheader("Bedside Assistant (AI - scoped)")

        with st.container(border=True):
            st.markdown("**Communication KPIs**")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Interruptions / shift", "-36%", "vs pre-deployment baseline")
            k2.metric("Avg response time",     "2.1 s","from question to answer")
            k3.metric("Out-of-scope rate",     "12%",  "auto-escalated to nurse")
            k4.metric("Patient satisfaction",  "4.4/5","30-day rolling")

        st.divider()
        st.write("### Conversation")

        if "chat_msgs" not in st.session_state:
            st.session_state.chat_msgs = [
                {"role": "bot", "text": "Hello - I'm a digital assistant for non-medical questions about your "
                                        "stay. For anything clinical, I'll page your nurse straight away."},
            ]

        with st.container(border=True):
            for m in st.session_state.chat_msgs:
                if m["role"] == "user":
                    with st.chat_message("user"):
                        st.write(m["text"])
                else:
                    with st.chat_message("assistant"):
                        st.write(m["text"])

        user_q = st.chat_input("Ask a question about your stay...")
        if user_q:
            st.session_state.chat_msgs.append({"role": "user", "text": user_q})
            matched = None
            for q, a in FAQ.items():
                if q.lower() == user_q.lower():
                    matched = a
                    break
            if matched is None:
                lq = user_q.lower()
                if   any(w in lq for w in ["eat", "food", "drink"]):           matched = FAQ["When can I eat after my surgery?"]
                elif any(w in lq for w in ["medic", "drug", "pill", "dose"]):   matched = FAQ["How often should I take my medication?"]
                elif any(w in lq for w in ["shower", "bath", "wash"]):          matched = FAQ["When can I shower?"]
                elif any(w in lq for w in ["warning", "emergency", "urgent"]):  matched = FAQ["What are my warning signs?"]
                else:
                    matched = ("That sounds clinical - I'm not allowed to answer that. I'll page your nurse now. "
                               "If urgent, please use the call bell.")
            st.session_state.chat_msgs.append({"role": "bot", "text": matched})
            st.rerun()

        st.error("**Hard limitation:** chatbots have hallucinated wrong dosing instructions in real deployments. "
                 "This system answers only from a curated, hospital-approved knowledge base - and refuses everything else.")

        st.divider()
        st.write("### Discharge & Reminders")
        with st.container(border=True):
            st.markdown("**Discharge instructions (summarised - R. Patel, 45 M, post-cholecystectomy)**")
            st.markdown(
                "- Rest for 24h, no heavy lifting (>5 kg) for 2 weeks\n"
                "- Keep wound dry & covered for 48h, then daily clean dressings\n"
                "- Paracetamol 1g QDS PRN; ibuprofen 400mg TDS PRN with food\n"
                "- Follow-up: GP in 7 days, surgical clinic in 4 weeks\n"
                "- Return urgently if: fever >38.5C, persistent vomiting, increasing abdominal pain, jaundice"
            )
            st.info("Reading-level adjusted to patient's preferred language (English) and literacy level (12y). "
                    "Simplified version available on request.")

        with st.container(border=True):
            st.markdown("**Medication reminder schedule**")
            df = pd.DataFrame([
                {"Time": "08:00", "Medication": "Paracetamol 1g",                       "Status": "Taken"},
                {"Time": "12:00", "Medication": "Paracetamol 1g",                       "Status": "Taken"},
                {"Time": "16:00", "Medication": "Paracetamol 1g + Ibuprofen 400mg",     "Status": "Due in 3h"},
                {"Time": "20:00", "Medication": "Paracetamol 1g",                       "Status": "Scheduled"},
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)


# =============================================================================
# SECTION 8 - STAFF WELLBEING
# =============================================================================
def render_wellbeing():
    st.title("Staff Wellbeing Dashboard")
    st.markdown("Aggregate, anonymised metrics on workload distribution and time spent on documentation. "
                "Surface-level - designed to support managers, never to surveil individual staff.")

    col_controls, col_display = st.columns([1, 3])

    with col_controls:
        st.subheader("Controls")
        time_range  = st.selectbox("Time range", ["Last 7 days", "Last 30 days", "Last 90 days"], index=0)
        ward_choice = st.selectbox("Ward", ["4-North", "4-South", "5-North", "All wards"], index=0)
        st.caption("All views are aggregated. No individual staff data is shown.")

    with col_display:
        st.subheader("Wellbeing Overview")

        st.info("**Privacy by design.** All metrics are aggregated to ward level. No nurse-identifiable data is "
                "shown. This must remain non-negotiable: turning a wellbeing tool into a productivity surveillance "
                "tool destroys trust irrecoverably.")

        with st.container(border=True):
            st.markdown("**Improvement metrics** (since AI rollout)")
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Charting time / shift", "-38%")
            k2.metric("Missed med doses",      "-12%")
            k3.metric("Late breaks",           "-21%")
            k4.metric("Overtime hours",        "+4%", delta_color="inverse")
            k5.metric("Self-reported burnout", "-9 pts")

        st.divider()

        g_col, doc_col = st.columns(2)

        with g_col:
            with st.container(border=True):
                st.markdown("**Ward stress index**")
                gfig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=5.2,
                    number={"suffix": " / 10", "font": {"size": 36, "color": "#2b3a55"}},
                    gauge={
                        "axis":      {"range": [0, 10]},
                        "bar":       {"color": "#2b3a55"},
                        "bgcolor":   "#f7f9fc",
                        "borderwidth": 1,
                        "bordercolor": "#eaeaea",
                        "steps": [
                            {"range": [0, 4], "color": "rgba(110,180,110,0.30)"},
                            {"range": [4, 7], "color": "rgba(244,196,90,0.30)"},
                            {"range": [7,10], "color": "rgba(255,107,107,0.30)"},
                        ],
                    },
                ))
                gfig.update_layout(paper_bgcolor="white", height=240, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(gfig, use_container_width=True, config={"displayModeBar": False})
                st.caption("Composite: shift length, acuity, overtime, sick-call rate, task-completion lag.")

        with doc_col:
            with st.container(border=True):
                st.markdown("**Time on documentation per shift (minutes)**")
                weeks = ["W-12", "W-10", "W-8", "W-6", "W-4", "W-2", "Now"]
                series = [142, 138, 141, 135, 132, 88, 72]
                ffig = go.Figure()
                ffig.add_trace(go.Scatter(x=weeks, y=series, mode="lines+markers", name="min/shift",
                                          line=dict(color="#2b3a55", width=2.5),
                                          marker=dict(size=7)))
                ffig.add_vline(x="W-2", line=dict(color="#5fa4d8", dash="dash"))
                ffig.add_annotation(x="W-2", y=155, text="AI rollout", showarrow=False,
                                    font=dict(size=10, color="#5fa4d8"))
                st.plotly_chart(style_plotly(ffig, height=240), use_container_width=True, config={"displayModeBar": False})

        st.divider()
        st.write("### Workload pattern (heat)")

        np.random.seed(42)
        days  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hours = [f"H+{i}" for i in range(12)]
        z = np.zeros((7, 12))
        for d in range(7):
            for h in range(12):
                base = 0.4 + 0.4 * math.sin((h - 3) * math.pi / 8)
                if d in [4, 5]:
                    base += 0.15
                z[d, h] = max(0.1, min(1.0, base + (np.random.random() - 0.5) * 0.25))

        with st.container(border=True):
            hfig = go.Figure(data=go.Heatmap(
                z=z, x=hours, y=days,
                colorscale=[[0, "#f7f9fc"], [0.5, "#5fa4d8"], [1, "#2b3a55"]],
                showscale=True,
                hovertemplate="%{y} %{x}: %{z:.2f}<extra></extra>",
            ))
            hfig.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                font=dict(size=10, color="#1a2b4c"),
                height=260, margin=dict(l=40, r=10, t=10, b=30),
            )
            st.plotly_chart(hfig, use_container_width=True, config={"displayModeBar": False})
            st.caption("Each cell = one hour of a 12h shift across 7 recent days. Darker = higher composite workload.")

        st.divider()
        st.write("### Honest caveats")
        with st.container(border=True):
            st.markdown(
                "- Self-reported burnout is noisy - single-shift effects may dominate.\n"
                "- Overtime *increased* on launch month as staff verified AI output extra-carefully.\n"
                "- Wellbeing gains can vanish if hospitals respond to efficiency by cutting staffing levels - 'efficiency taxes'.\n"
                "- These metrics *do not capture* moral injury or emotional labour."
            )


# =============================================================================
# SECTION - KNOWN LIMITATIONS
# =============================================================================
def render_limits():
    st.title("Known Limitations & Failure Modes")
    st.markdown("A working catalogue of the ways this system can be wrong, has been wrong elsewhere, or could be "
                "wrong if deployed without care. Read this before trusting any output.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Documented failure modes")
        with st.container(border=True):
            st.markdown(
                "**Hallucinated chart entries.** Generative documentation tools have produced plausible-sounding "
                "observations the patient never had. _Mitigation: every draft is unsigned until human review; "
                "flagged terms forced into a verification step._"
            )
        with st.container(border=True):
            st.markdown(
                "**Alert fatigue.** High false-positive rates lead clinicians to ignore real warnings. "
                "_Mitigation: hourly digests for low-priority alerts; weekly per-clinician fatigue audit._"
            )
        with st.container(border=True):
            st.markdown(
                "**Bias in risk scoring.** Models trained on US/EU data have systematically under-scored "
                "deterioration risk in Black patients (Obermeyer et al, 2019). _Mitigation: model must be "
                "revalidated on local population before deployment._"
            )
        with st.container(border=True):
            st.markdown(
                "**Automation bias.** Clinicians follow AI recommendations even when their own judgement disagrees, "
                "especially under cognitive load. _Mitigation: visible confidence scores, easy override paths, "
                "mandatory training._"
            )
        with st.container(border=True):
            st.markdown(
                "**Distribution shift.** Performance silently degrades as patient populations, protocols, or "
                "sensors change. _Mitigation: continuous monitoring of model performance; pre-set thresholds for "
                "re-validation._"
            )

    with col2:
        st.subheader("Real-world deployment constraints")
        with st.container(border=True):
            st.markdown(
                "**Integration debt.** EHR vendors rarely expose real-time APIs. Most 'AI' features rely on "
                "screen-scraping or batch exports that lag the live record by minutes to hours."
            )
        with st.container(border=True):
            st.markdown(
                "**Regulatory landscape.** In the UK, AI used as a medical device requires MHRA approval; in the "
                "EU, the AI Act (in force 2026) classifies most clinical AI as high-risk. Educational tools like "
                "this are not approved devices."
            )
        with st.container(border=True):
            st.markdown(
                "**Liability.** Clinical responsibility cannot be delegated to a vendor. If an AI suggestion "
                "contributes to harm, the clinician who acted on it remains accountable - which is why the "
                "override path must be friction-free."
            )
        with st.container(border=True):
            st.markdown(
                "**Connectivity assumptions.** Hospital wifi fails. Cloud APIs go down. The system must degrade "
                "gracefully - manual workflows must remain functional, and staff must remember how to do them."
            )
        with st.container(border=True):
            st.markdown(
                "**Equity of access.** Patient-facing chatbots assume literacy, language match, and device access. "
                "Without thoughtful fallback, they widen rather than narrow communication gaps."
            )

    st.divider()
    st.info("**The throughline.** AI in nursing should subtract the busywork that keeps nurses away from patients - "
            "documentation, hunting for equipment, manual handoffs. It should not subtract clinical judgement, "
            "professional autonomy, or the relational work that *is* nursing. Jebex is built to be turned off "
            "without losing safety.")


# =============================================================================
# ROUTING
# =============================================================================
sec_code = section.split(" - ")[0].strip()
if   sec_code == "01":              render_documentation()
elif sec_code == "02":              render_monitoring()
elif sec_code == "03":              render_tasks()
elif sec_code == "04":              render_staffing()
elif sec_code == "05":              render_routine()
elif sec_code == "06":              render_cdss()
elif sec_code == "07":              render_communication()
elif sec_code == "08":              render_wellbeing()
else:                               render_limits()

st.divider()
st.caption("Jebex v0.9 (simulation) - Educational prototype only. Not a medical device. Not validated for clinical "
           "use. Built to demonstrate benefits AND limitations of AI in nursing workflows.")
