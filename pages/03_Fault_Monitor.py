"""

Completely Generated

"""

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
    "warning": (251, 188,   5,  210),
    "alert":   (234,  67,  53,  210),
    "offline": (189, 193, 198,  210),
}

GROUP_ACCENT_COLORS = [
    (66,  133, 244),   # blue
    (234,  67,  53),   # red
    (52,  168,  83),   # green
    (251, 188,   5),   # yellow
    (103,  58, 183),   # purple
    (0,   172, 193),   # teal
]

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
        (60,  60,  300, 220, "Ward A"),
        (60,  260, 300, 420, "Ward B"),
        (340, 60,  580, 180, "ICU"),
        (340, 220, 580, 420, "Server Room"),
        (620, 60,  860, 280, "Mechanical Plant"),
        (620, 320, 860, 520, "Electrical"),
        (60,  460, 580, 560, "Corridor"),
    ]
    for x1, y1, x2, y2, label in rooms:
        draw.rectangle([x1, y1, x2, y2], outline=(180, 190, 210), width=2)
        draw.text(
            ((x1 + x2) // 2 - len(label) * 3, (y1 + y2) // 2 - 8),
            label, fill=(160, 170, 190),
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
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Floor Plan Sensors")
    st.caption("Fault Monitor")
    st.divider()

    # Floor plan selector
    active_floor = st.selectbox(
        "Floor Plan",
        floor_plan_names,
        index=floor_plan_names.index(st.session_state.active_floor),
    )
    if active_floor != st.session_state.active_floor:
        st.session_state.active_floor = active_floor
        st.session_state.selected_device_id = None
        st.rerun()

    # Image upload
    st.markdown("**Upload Floor Plan Image**")
    uploaded = st.file_uploader(
        "PNG, JPEG or WebP",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
    )
    if uploaded:
        st.session_state.floor_plan_img = Image.open(uploaded).convert("RGB")
        st.success("Floor plan loaded")

    st.divider()

    # Group legend
    st.markdown("**Groups**")
    for i, g in enumerate(groups):
        gc = GROUP_ACCENT_COLORS[i % len(GROUP_ACCENT_COLORS)]
        hex_color = "#{:02x}{:02x}{:02x}".format(*gc)
        count = sum(1 for d in devices if d.group == g)
        st.markdown(
            f"<span style='color:{hex_color};font-size:1rem;font-weight:700'>&#9632;</span>"
            f" <span style='font-size:0.85rem;color:#1a2b4c'>{g}</span>"
            f" <span style='font-size:0.75rem;color:#9ca3af'>({count})</span>",
            unsafe_allow_html=True,
        )

    st.divider()
    backend_ok = backend.health_check()
    st.caption(
        f"Backend: **{'FAKE DATA' if type(backend).__name__ == 'FakeSensorBackend' else 'LIVE'}** "
        f"· {'Connected' if backend_ok else 'Unreachable'}"
    )

# ─────────────────────────────────────────────────────────────────────────────
# Header — matches existing page structure
# ─────────────────────────────────────────────────────────────────────────────
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("Fault Monitor")

with col_head2:
    alert_count = status_counts["alert"]
    warn_count  = status_counts["warning"]
    if alert_count > 0:
        st.error(f"**{alert_count} ACTIVE ALERT{'S' if alert_count > 1 else ''}** — requires attention")
    elif warn_count > 0:
        st.warning(f"**{warn_count} WARNING{'S' if warn_count > 1 else ''}** — review recommended")
    else:
        st.success("**ALL SYSTEMS NOMINAL**")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Main layout: floor plan | device list | detail panel
# ─────────────────────────────────────────────────────────────────────────────
col_map, col_list, col_detail = st.columns([2.2, 1.1, 1.1], gap="medium")

# ── COLUMN 1: Floor plan map ──────────────────────────────────────────────────
with col_map:
    with st.container(border=True):
        st.subheader(f"Floor Plan — {st.session_state.active_floor}")
        st.caption(
            f"{len(devices)} devices · "
            f"{status_counts['ok']} OK · "
            f"{status_counts['warning']} Warning · "
            f"{status_counts['alert']} Alert · "
            f"{status_counts['offline']} Offline"
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

        # Legend strip
        st.markdown("**Status legend**")
        leg_cols = st.columns(4)
        for i, (status, label, colour) in enumerate([
            ("ok",      "OK",      "#34a853"),
            ("warning", "Warning", "#fbbc05"),
            ("alert",   "Alert",   "#ea4335"),
            ("offline", "Offline", "#bdc1c6"),
        ]):
            leg_cols[i].markdown(
                f"<span style='color:{colour};font-size:1rem;font-weight:900'>&#9679;</span> "
                f"<span style='font-size:0.78rem;color:#1a2b4c'>{label} ({status_counts[status]})</span>",
                unsafe_allow_html=True,
            )


# ── COLUMN 2: Device list ─────────────────────────────────────────────────────
with col_list:
    with st.container(border=True):
        st.subheader("Devices")
        st.caption("Click a device to view sensor readings")

        # Filter controls
        filter_status = st.multiselect(
            "Filter by status",
            options=["ok", "warning", "alert", "offline"],
            default=["ok", "warning", "alert", "offline"],
            label_visibility="collapsed",
        )
        filter_group = st.selectbox(
            "Filter by group",
            options=["All groups"] + groups,
            label_visibility="collapsed",
        )

        filtered = [
            d for d in devices
            if d.status in filter_status
            and (filter_group == "All groups" or d.group == filter_group)
        ]

        if not filtered:
            st.caption("No devices match the current filter.")
        else:
            for d in filtered:
                is_active = d.id == st.session_state.selected_device_id
                sc_hex = "#{:02x}{:02x}{:02x}".format(*STATUS_COLORS_RGB[d.status])

                # Use a button as the row — Streamlit doesn't have a native
                # clickable row component
                clicked = st.button(
                    f"{d.name}",
                    key=f"btn_{d.id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                )
                if clicked:
                    st.session_state.selected_device_id = (
                        None if is_active else d.id
                    )
                    st.rerun()

                st.markdown(
                    f"<div style='margin:-8px 0 4px 4px;font-size:0.74rem;color:#6b7280'>"
                    f"{d.device_type} &nbsp;·&nbsp; {d.group} &nbsp;"
                    f"<span style='color:{sc_hex};font-weight:700'>"
                    f"&#9679; {d.status.upper()}</span></div>",
                    unsafe_allow_html=True,
                )


# ── COLUMN 3: Detail panel ────────────────────────────────────────────────────
with col_detail:
    with st.container(border=True):
        selected = (
            backend.get_device(st.session_state.selected_device_id)
            if st.session_state.selected_device_id
            else None
        )

        if selected is None:
            st.subheader("Device Detail")
            st.caption("Select a device on the floor plan or from the list to view sensor readings.")
            st.markdown(
                "<div class='upload-hint' style='margin-top:16px'>"
                "Click any dot on the floor plan, or use the device list on the left."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            sc_hex = "#{:02x}{:02x}{:02x}".format(*STATUS_COLORS_RGB[selected.status])

            # Device header
            st.subheader(selected.name)
            st.markdown(
                f"{status_pill_html(selected.status)}"
                f"&nbsp; <span style='font-size:0.78rem;color:#6b7280'>"
                f"{selected.device_type} · {selected.group}</span>",
                unsafe_allow_html=True,
            )

            reason_class = f"reason-{selected.status}"
            st.markdown(
                f"<p class='{reason_class}'>{selected.status_reason}</p>",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"<p style='font-size:0.75rem;color:#9ca3af;margin:0'>"
                f"Position: ({selected.x_pct:.0f} %, {selected.y_pct:.0f} %)</p>",
                unsafe_allow_html=True,
            )

            st.divider()

            # Sensor readings
            st.markdown(
                f"<p style='font-weight:600;font-size:0.82rem;color:#6b7280;"
                f"text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px'>"
                f"Sensor Readings</p>",
                unsafe_allow_html=True,
            )

            if not selected.readings:
                st.caption("No readings available.")
            else:
                rows_html = ""
                for r in selected.readings:
                    val_str = str(r.value)
                    if isinstance(r.value, bool):
                        val_str = "Yes" if r.value else "No"
                    rows_html += (
                        f"<div class='reading-row'>"
                        f"<span class='reading-label'>{r.label}</span>"
                        f"<span>"
                        f"<span class='reading-value'>{val_str}</span>"
                        f"<span class='reading-unit'>{r.unit}</span>"
                        f"<span class='reading-ts'>{r.last_updated}</span>"
                        f"</span>"
                        f"</div>"
                    )
                st.markdown(rows_html, unsafe_allow_html=True)

            st.divider()

            # AI status placeholder
            st.markdown(
                "<p style='font-weight:600;font-size:0.78rem;color:#9ca3af;"
                "text-transform:uppercase;letter-spacing:0.06em'>AI Status Model</p>",
                unsafe_allow_html=True,
            )
            st.caption(
                "AI-driven status inference is not yet connected. "
                "Status is currently supplied directly by the backend."
            )

            if st.button("Deselect device", use_container_width=True):
                st.session_state.selected_device_id = None
                st.rerun()