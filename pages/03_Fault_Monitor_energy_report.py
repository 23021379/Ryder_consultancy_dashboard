"""

Completely Generated

"""
import matplotlib.pyplot as plt
from executors.exec_data_loader import load_data
from executors.exec_optimizer import get_optimum_configuration
from executors.exec_cross_section import generate_single_cross_section
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import io
import os
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# Import backend — swap FakeSensorBackend for a real implementation when ready
from backend.sensors import FakeSensorBackend, SensorDevice

# ─────────────────────────────────────────────────────────────────────────────
# Page config — must be first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fault Monitor",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — mirrors the existing dashboard aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Base ──────────────────────────────────────────────────────── */
    .stApp {
        background-color: #f7f9fc;
        color: #1a2b4c;
    }
    p, span, label, div.stMarkdown, div.stText {
        color: #1a2b4c;
    }
    h1, h2, h3, h4 {
        color: #1a2b4c;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }

    /* ── Cards (matches existing page container style) ─────────────── */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.05);
        background: #ffffff;
        border: 1px solid #eaeaea !important;
        padding: 15px;
    }

    /* ── Status pill badges ─────────────────────────────────────────── */
    .pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .pill-ok      { background: #d1fae5; color: #065f46; }
    .pill-warning { background: #fef3c7; color: #92400e; }
    .pill-alert   { background: #fee2e2; color: #991b1b; }
    .pill-offline { background: #f3f4f6; color: #6b7280; }

    /* ── Device list rows ───────────────────────────────────────────── */
    .device-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 9px 12px;
        border-radius: 8px;
        border: 1px solid #eaeaea;
        margin-bottom: 6px;
        background: #ffffff;
        cursor: pointer;
        transition: border-color 0.15s, background 0.15s;
    }
    .device-row:hover  { border-color: #4285f4; background: #f0f6ff; }
    .device-row.active { border-color: #4285f4; background: #e8f0fe; }
    .device-row .dname { font-weight: 600; font-size: 0.88rem; color: #1a2b4c; }
    .device-row .dtype { font-size: 0.75rem; color: #6b7280; margin-top: 1px; }
    .device-row .dgroup{
        font-size: 0.7rem; color: #4285f4; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.05em;
    }

    /* ── Detail panel readings ──────────────────────────────────────── */
    .reading-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 7px 0;
        border-bottom: 1px solid #f3f4f6;
    }
    .reading-row:last-child { border-bottom: none; }
    .reading-label  { font-size: 0.82rem; color: #6b7280; }
    .reading-value  { font-size: 0.95rem; font-weight: 700; color: #1a2b4c;
                      font-family: 'Courier New', monospace; }
    .reading-unit   { font-size: 0.75rem; color: #9ca3af; margin-left: 4px; }
    .reading-ts     { font-size: 0.68rem; color: #d1d5db; margin-left: 8px; }

    /* ── Metric strip ───────────────────────────────────────────────── */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2b3a55;
    }

    /* ── Upload zone hint ───────────────────────────────────────────── */
    .upload-hint {
        background: #f0f6ff;
        border: 1px dashed #93c5fd;
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 0.82rem;
        color: #6b7280;
        margin-bottom: 12px;
    }

    /* ── Reason text ────────────────────────────────────────────────── */
    .reason-ok      { color: #065f46; font-size: 0.8rem; }
    .reason-warning { color: #92400e; font-size: 0.8rem; }
    .reason-alert   { color: #991b1b; font-size: 0.8rem; font-weight: 600; }
    .reason-offline { color: #6b7280; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Backend initialisation
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_backend():
    return FakeSensorBackend()

backend = get_backend()

# ─────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────────────────────
if "selected_device_id" not in st.session_state:
    st.session_state.selected_device_id = None
if "floor_plan_img" not in st.session_state:
    st.session_state.floor_plan_img = None
if "active_floor" not in st.session_state:
    st.session_state.active_floor = "Ground Floor"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
STATUS_COLORS_RGB = {
    "ok":      (52,  168,  83),
    "warning": (251, 188,   5),
    "alert":   (234,  67,  53),
    "offline": (189, 193, 198),
}

STATUS_FILL_RGBA = {
    "ok":      (52,  168,  83,  210),
    "warning": (234,  67,  53,  210),
    "alert":   (251, 188,   5,  210),
    "offline": (189, 193, 198,  210),
}

GROUP_ACCENT_COLORS = [
    (234,  67,  53),   # red
    (251, 188, 5),  # yellow
    (52,  168,  83),   # green
    (251, 188,   5),   # yellow
]

wards = [
    'Outpatient Dialysis', 'Stroke Ward', "Children's Ward", 'Trauma', 'Elderly Care',
    'Maternity', 'X-ray', 'Radiotherapy', 'Emergency Decision Unit',
    'Main Theatre', 'Pathology', 'Day Clinic', 'CCU'
]
consumption = [13.6, 16.3, 8.8, 11.3, 10.4, 21.2, 20.6, 24.1, 13.2, 45.8, 47.9, 12.8, 15.5]

edited_consumption = [13.7, 14.5, 8.2, 11.3, 14.0, 21.3, 23.8, 23.2, 16.9, 47.7, 47.6, 13.7, 15.6]

differences = [e - o for e, o in zip(edited_consumption, consumption)]
room_consumption = dict(zip(wards, differences))

def group_color(groups: list[str], group_name: str) -> tuple:
    idx = groups.index(group_name) if group_name in groups else 0
    return GROUP_ACCENT_COLORS[idx % len(GROUP_ACCENT_COLORS)]

def status_pill_html(status: str) -> str:
    labels = {"ok": "OK", "warning": "WARNING", "alert": "ALERT", "offline": "OFFLINE"}
    return f"<span class='pill pill-{status}'>{labels.get(status, status.upper())}</span>"

def render_floor_plan(
    base_img: Image.Image,
    devices: list[SensorDevice],
    groups: list[str],
    selected_id: str | None,
) -> Image.Image:
    """Draw status dots and labels onto a copy of the floor plan image."""
    img = base_img.copy().convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    dot_r = max(10, int(min(W, H) * 0.016))

    for d in devices:
        x = int(d.x_pct / 100 * W)
        y = int(d.y_pct / 100 * H)

        gc = group_color(groups, d.group)
        sc_fill = STATUS_FILL_RGBA[d.status]
        sc_ring = STATUS_COLORS_RGB[d.status]

        # Pulse ring for selected device
        if d.id == selected_id:
            draw.ellipse(
                [x - dot_r - 7, y - dot_r - 7, x + dot_r + 7, y + dot_r + 7],
                outline=(66, 133, 244, 200), width=3,
            )

        # Group-colour outer ring
        draw.ellipse(
            [x - dot_r - 3, y - dot_r - 3, x + dot_r + 3, y + dot_r + 3],
            outline=gc + (255,), width=3,
        )
        # Status-colour filled dot
        draw.ellipse(
            [x - dot_r, y - dot_r, x + dot_r, y + dot_r],
            fill=sc_fill, outline=(255, 255, 255, 220), width=2,
        )

        # Short name label
        label = d.name[:20]
        draw.text(
            (x + dot_r + 6, y - 9),
            label,
            fill=(30, 43, 76, 240),
            stroke_fill=(255, 255, 255, 200),
            stroke_width=2,
        )

    combined = Image.alpha_composite(img, overlay)
    return combined.convert("RGB")


def placeholder_floor_plan(w: int = 900, h: int = 600) -> Image.Image:
    """Generate a simple placeholder when no image has been uploaded."""
    img = Image.new("RGB", (w, h), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)

    # Grid lines
    for x in range(0, w, 90):
        draw.line([(x, 0), (x, h)], fill=(220, 225, 232), width=1)
    for y in range(0, h, 90):
        draw.line([(0, y), (w, y)], fill=(220, 225, 232), width=1)

    # Room outlines
    rooms = [
        # Top row (3 rooms)
        (60, 60, 340, 220, "Outpatient Dialysis"),
        (360, 60, 620, 220, "Stroke Ward"),
        (640, 60, 860, 220, "Childrens Ward"),

        # Middle-top row (3 rooms)
        (60, 240, 280, 400, "Trauma"),
        (300, 240, 520, 400, "Elderly Care"),
        (540, 240, 760, 400, "Maternity"),
        (780, 240, 860, 400, "X-Ray"),

        # Middle-bottom row (3 rooms)
        (60, 420, 220, 560, "Radiotherapy"),
        (240, 420, 420, 560, "Emergency Decision Unit"),
        (440, 420, 620, 560, "Main Theatre"),

        # Bottom corridor + 3 small rooms
        (640, 420, 720, 560, "Pathology"),
        (740, 420, 800, 560, "Day Care"),
        (820, 420, 860, 560, "CCU"),
    ]


    def consumption_to_color(diff, threshold=0.25):
        """
        Green if using less than baseline (negative diff),
        Red if using more than baseline (positive diff),
        Gray if within threshold of baseline.
        """
        if diff < -threshold:
            return (80, 200, 80, 80)  # green - using less (R=80, G=200, B=80)
        elif diff > threshold:
            return (220, 60, 60, 80)  # red - using more (R=220, G=60, B=60)
        else:
            return (180, 180, 180, 80)  # gray - about the same

    if room_consumption:
        values = list(room_consumption.values())
        avg_val = sum(values) / len(values)
    else:
        avg_val = 1

    for x1, y1, x2, y2, label in rooms:
        if room_consumption and label in room_consumption:
            fill_color = consumption_to_color(room_consumption[label], avg_val)
        else:
            fill_color = (200, 210, 225, 60)

        # Draw filled rectangle with RGBA overlay
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([x1, y1, x2, y2], fill=fill_color)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Room outline and label
        draw.rectangle([x1, y1, x2, y2], outline=(180, 190, 210), width=2)
        draw.text(
            ((x1 + x2) // 2 - len(label) * 3, (y1 + y2) // 2 - 8),
            label, fill=(60, 70, 90),
        )

    draw.text((w // 2 - 180, h - 32),
              "Upload a floor plan image using the sidebar",
              fill=(180, 190, 210))
    return img


# ─────────────────────────────────────────────────────────────────────────────
# Data fetch
# ─────────────────────────────────────────────────────────────────────────────
floor_plans = backend.get_floor_plans()
floor_plan_names = [fp.name for fp in floor_plans]
devices = backend.get_devices(st.session_state.active_floor)
groups  = sorted(set(d.group for d in devices))

# Status summary counts
status_counts = {s: sum(1 for d in devices if d.status == s)
                 for s in ("ok", "warning", "alert", "offline")}


# ─────────────────────────────────────────────────────────────────────────────
# Header — matches existing page structure
# ─────────────────────────────────────────────────────────────────────────────

st.title("Energy Report")


st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Main layout: floor plan | device list | detail panel
# ─────────────────────────────────────────────────────────────────────────────
col_average, col_current, col_dif = st.columns([1, 1, 1])
col_map, col_info = st.columns([3,1])
# ── COLUMN 1: Floor plan map ──────────────────────────────────────────────────
with col_map:
    with st.container(border=True):
        st.subheader(f"Floor Plan — {st.session_state.active_floor}")
        st.caption(
            "13 wards · "
            "2 Efficient · "
            "3 Inefficient · "
            "8 Nominal · "
            "0 Other"
        )

        base_img = st.session_state.floor_plan_img or placeholder_floor_plan()
        rendered = render_floor_plan(base_img, devices, groups,
                                         st.session_state.selected_device_id)

        # Click-to-select using streamlit-image-coordinates
        # The component accepts PIL Images directly (anything with a .save method)
        try:
            from streamlit_image_coordinates import streamlit_image_coordinates
            coords = streamlit_image_coordinates(rendered, key="fp_click")

            if coords:
                click_x_pct = coords["x"] / coords["width"]  * 100
                click_y_pct = coords["y"] / coords["height"] * 100
                hit_radius  = 4.0  # percent — tolerance for click hit

                best, best_dist = None, float("inf")
                for d in devices:
                    dist = ((d.x_pct - click_x_pct) ** 2 +
                            (d.y_pct - click_y_pct) ** 2) ** 0.5
                    if dist < hit_radius and dist < best_dist:
                        best, best_dist = d, dist

                if best and best.id != st.session_state.selected_device_id:
                    st.session_state.selected_device_id = best.id
                    st.rerun()
                elif coords and not best and st.session_state.selected_device_id:
                    # Click away from any sensor deselects
                    st.session_state.selected_device_id = None
                    st.rerun()

        except ImportError:
            st.image(rendered, use_container_width=True)
            st.markdown(
                "<div class='upload-hint'>"
                "Install <code>streamlit-image-coordinates</code> for click-to-select: "
                "<code>pip install streamlit-image-coordinates</code>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("**Status legend**")
        leg_cols = st.columns(4)
        for i, (status, label, colour, count) in enumerate([
            ("ok", "More Efficient", "#34a853", 2),
            ("warning", "Less Efficient", "#ea4335", 3),
            ("alert", "Average", "#bdc1c6", 8),
            ("offline", "Other", "#fbbc05", 0),
        ]):
            leg_cols[i].markdown(
                f"<span style='color:{colour};font-size:1rem;font-weight:900'>&#9679;</span> "
                f"<span style='font-size:0.78rem;color:#1a2b4c'>{label} ({count})</span>",
                unsafe_allow_html=True,
            )
with col_info:
    with st.container(border=True):
        st.title("Energy being lost to inefficiency")
        st.subheader("13.6 Wh/m^2/hr")
    with st.container(border=True):
        st.title("Energy being saved due to efficiency")
        st.subheader("3.6 Wh/m^2/hr")
    with st.container(border=True):
        st.title("Possible factors to inefficiencies")
        st.subheader("Electrical Panel A is not working as intended")
        st.subheader("BMS Node - Ward 3 is not working as intended")
        st.subheader("BMS Node - ICU is not working as intended")
# ── COLUMN 2: Device list ─────────────────────────────────────────────────────
with col_average:
    st.subheader("Average Energy Consumption")

    df = pd.DataFrame({
        'Ward': wards,
        'Consumption': consumption
    })

    fig = px.line(
        df,
        x='Ward',
        y='Consumption',
        labels={'Consumption': 'Wh/m²/hr', 'Ward': 'Ward'},
        markers=True
    )

    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>%{y} Wh/m²/hr<extra></extra>',
        line=dict(color='#4a90d9', width=2.5),
        marker=dict(size=7, color='#4a90d9', line=dict(color='#ffffff', width=1.5))
    )

    fig.update_layout(
        margin=dict(t=20, b=80, l=0, r=0),
        paper_bgcolor='#f7f9fc',
        plot_bgcolor='#f7f9fc',
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=9)
        ),
        yaxis=dict(
            title='Wh/m²/hr'
        ),
        showlegend=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
with col_current:
    st.subheader("Current Energy Consumption")

    df = pd.DataFrame({
        'Ward': wards,
        'Consumption': edited_consumption
    })

    fig = px.line(
        df,
        x='Ward',
        y='Consumption',
        labels={'Consumption': 'Wh/m²/hr', 'Ward': 'Ward'},
        markers=True
    )

    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>%{y} Wh/m²/hr<extra></extra>',
        line=dict(color='#e07b54', width=2.5),
        marker=dict(size=7, color='#e07b54', line=dict(color='#ffffff', width=1.5))
    )

    fig.update_layout(
        margin=dict(t=20, b=80, l=0, r=0),
        paper_bgcolor='#f7f9fc',
        plot_bgcolor='#f7f9fc',
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=9)
        ),
        yaxis=dict(
            title='Wh/m²/hr'
        ),
        showlegend=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

with col_dif:
    st.subheader("Energy Consumption Comparison")

    df = pd.DataFrame({
        'Ward': wards,
        'Average': consumption,
        'Current': edited_consumption
    })

    fig = go.Figure()

    # Shade red where Current > Average
    fig.add_trace(go.Scatter(
        x=df['Ward'].tolist() + df['Ward'].tolist()[::-1],
        y=df['Current'].tolist() + df['Average'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(220, 80, 80, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip',
        showlegend=True,
        name='Above Average'
    ))

    # Shade green where Current < Average
    fig.add_trace(go.Scatter(
        x=df['Ward'].tolist() + df['Ward'].tolist()[::-1],
        y=df['Average'].tolist() + df['Current'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(80, 180, 80, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip',
        showlegend=True,
        name='Below Average'
    ))

    fig.add_trace(go.Scatter(
        x=df['Ward'],
        y=df['Average'],
        mode='lines+markers',
        name='Average',
        hovertemplate='<b>%{x}</b><br>Average: %{y} Wh/m²/hr<extra></extra>',
        line=dict(color='#4a90d9', width=2.5),
        marker=dict(size=7, color='#4a90d9', line=dict(color='#ffffff', width=1.5))
    ))

    fig.add_trace(go.Scatter(
        x=df['Ward'],
        y=df['Current'],
        mode='lines+markers',
        name='Current',
        hovertemplate='<b>%{x}</b><br>Current: %{y} Wh/m²/hr<extra></extra>',
        line=dict(color='#e07b54', width=2.5),
        marker=dict(size=7, color='#e07b54', line=dict(color='#ffffff', width=1.5))
    ))

    fig.update_layout(
        margin=dict(t=20, b=80, l=0, r=0),
        paper_bgcolor='#f7f9fc',
        plot_bgcolor='#f7f9fc',
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=9)
        ),
        yaxis=dict(title='Wh/m²/hr'),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)