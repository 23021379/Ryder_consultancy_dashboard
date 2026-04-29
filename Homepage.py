import streamlit as st

st.markdown("""
<style>
    /* App background */
    .stApp {
        background-color: #f7f9fc;
    }

    /* Card-like containers */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.05);
        background: #ffffff;
        border: 1px solid #eaeaea;
        padding: 12px 15px;
    }

    /* Metric values */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2b3a55;
    }

    /* Headings */
    h1, h2, h3 {
        color: #1a2b4c;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="JEBEX dashboard", 
    layout="wide"
)

st.title("JEBEX dashboard")

st.write("Select modules below or use the navbar.")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.subheader("Solar Configuration")
        if st.button("Open", key=1):
            st.switch_page("pages/01_Solar_Config.py")
        st.caption("View metrics and adjust solar configuration")

with col2:
    with st.container(border=True):
        st.subheader("Forecast")
        if st.button("Open", key=2):
            st.switch_page("pages/02_Forecasts.py")
        st.caption("View grid, solar and weather forecasts")

with col3:
    with st.container(border=True):
        st.subheader("Fault Detection")
        if st.button("Open", key=3):
            st.switch_page("pages/03_Fault_Monitor.py")
        st.caption("View fault analysis")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Staff and Patient Experience")
        if st.button("Open", key=4):
            st.switch_page("pages/04_Staff_and_Patient_Experience.py")
        st.caption("View Seydina")
