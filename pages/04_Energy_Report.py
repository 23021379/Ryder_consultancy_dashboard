import streamlit as st
import matplotlib.pyplot as plt
from executors.exec_data_loader import load_data
from executors.exec_optimizer import get_optimum_configuration
from executors.exec_cross_section import generate_single_cross_section
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Energy Report", layout="wide")

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

st.title("Energy Report")
st.markdown("View the overall energy consumption through each ward to make energy efficient decisions")

col_controls, col_display, col_dif = st.columns([1, 1, 1])

# --- Data ---
wards = [
    'CCU', 'Stroke Ward', "Children's Ward", 'Trauma', 'Elderly Care',
    'Maternity', 'X-ray', 'Radiotherapy', 'Emergency Decision Unit',
    'Main Theatre', 'Pathology', 'Day Clinic', 'Outpatient Dialysis'
]
consumption = [136, 143, 76, 99, 91, 186, 181, 211, 116, 397, 420, 112, 119]

edited_consumption = [137, 141, 77, 99, 123, 187, 209, 131, 402, 418, 111, 120, 120]

differences = [e - o for e, o in zip(edited_consumption, consumption)]

with col_controls:
    st.subheader("Average Energy Consumption")

    df = pd.DataFrame({
        'Ward': wards,
        'Consumption': consumption
    })

    fig = px.pie(
        df,
        values='Consumption',
        names='Ward',
        hover_data={'Consumption': True},
        labels={'Consumption': 'kWh/m²/yr'}
    )

    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>%{value} kWh/m²/yr<extra></extra>',
        textinfo='none',
        pull=[0.03] * len(wards),  # slightly separates every slice
        marker=dict(
            line=dict(color='#ffffff', width=2.5)  # white border between slices
        )
    )

    fig.update_layout(
        margin=dict(t=20, b=150, l=0, r=0),  # increase bottom margin for legend space
        paper_bgcolor='#f7f9fc',
        showlegend=True,
        legend=dict(
            orientation='v',
            font=dict(size=9),
            x=0,
            y=-0.6  # push legend further down below the chart
        ),
        height=600  # increase height to accommodate the extra space
    )



    st.plotly_chart(fig, use_container_width=True)


with col_display:
    st.subheader("Current Energy Consumption")
    df = pd.DataFrame({
        'Ward': wards,
        'Consumption': edited_consumption
    })

    fig = px.pie(
        df,
        values='Consumption',
        names='Ward',
        hover_data={'Consumption': True},
        labels={'Consumption': 'kWh/m²/yr'}
    )

    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>%{value} kWh/m²/yr<extra></extra>',
        textinfo='none',
        pull=[0.03] * len(wards),  # slightly separates every slice
        marker=dict(
            line=dict(color='#ffffff', width=2.5)  # white border between slices
        )
    )

    fig.update_layout(
        margin=dict(t=20, b=150, l=0, r=0),  # increase bottom margin for legend space
        paper_bgcolor='#f7f9fc',
        showlegend=True,
        legend=dict(
            orientation='v',
            font=dict(size=9),
            x=0,
            y=-0.6  # push legend further down below the chart
        ),
        height=600  # increase height to accommodate the extra space
    )

    st.plotly_chart(fig, use_container_width=True)

with col_controls:
    st.subheader("Difference in Energy Consumption")
    pull_values = []
    for c in edited_consumption:
        if c >= 397:
            pull_values.append(0.1)
        elif c >= 186:
            pull_values.append(0.05)
        else:
            pull_values.append(0.02)
    threshold = 15  # only show red if consumption increased by more than this

    slice_colors = []
    for d in differences:
        if d < 0:
            slice_colors.append('#e74c3c')  # green = improvement
        elif d > threshold:
            slice_colors.append('#2ecc71')  # red = significant increase
        else:
            slice_colors.append('#95a5a6')  # gray = minor change or unchanged

    fig2 = px.pie(
        pd.DataFrame({'Ward': wards, 'Consumption': edited_consumption}),
        values='Consumption',
        names='Ward',
    )

    fig2.update_traces(
        customdata=differences,
        hovertemplate='<b>%{label}</b><br>%{customdata:+d} kWh/m²/yr<extra></extra>',
        textinfo='none',
        pull=pull_values,
        marker=dict(
            colors=slice_colors,
            line=dict(color='#ffffff', width=2.5)
        )
    )

    fig2.update_layout(
        margin=dict(t=20, b=0, l=0, r=150),
        paper_bgcolor='#f7f9fc',
        showlegend=True,
        legend=dict(
            orientation='v',
            font=dict(size=9),
            x=1.05,
            y=0.5,
            xanchor='left',
            yanchor='middle'
        ),
        height=500
    )

    st.plotly_chart(fig2, use_container_width=True)

