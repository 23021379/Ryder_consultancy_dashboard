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


left, right = st.columns(2)
with left:
    with st.container():
        if st.button("Solar Configuration"):
            st.switch_page("pages/01_solar_config.py")

        st.caption("View metrics and adjust solar configuration")

with right:
    with st.container():
        if st.button("Forecast"):
            st.switch_page("pages/02_forecast.py")

        st.caption("View grid, solar and weather forecasts")
