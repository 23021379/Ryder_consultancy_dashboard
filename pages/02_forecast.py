import streamlit as st
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import pydeck as pdk
import os

from executors.exec_weather_tmy import fetch_24h_weather
from executors.exec_yield_hourly import generate_hourly_yield
from executors.exec_octopus_api import fetch_grid_prices
from executors.exec_raster_overlay import fetch_roof_raster
from executors.exec_bess_arbitrage import calculate_optimal_action

st.set_page_config(page_title="SMART HOSPITAL ENERGY Simulation", layout="wide", initial_sidebar_state="expanded")

# just throwing in some custom CSS to clean up the cards and stop the metrics from getting truncated
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.05);
        background: #ffffff;
        border: 1px solid #eaeaea;
        padding: 15px;
    }
    .stApp {
        background-color: #f7f9fc;
        color: #1a2b4c;
    }
    p, span, label, div.stMarkdown, div.stText {
        color: #1a2b4c;
    }
    h1, h2, h3 {
        color: #1a2b4c;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2b3a55;
    }
</style>
""", unsafe_allow_html=True)

# -----------------
# DATA LOADING
# -----------------
with st.spinner("Fetching Typical Meteorological Year & Physics Simulation"):
    tmy_24h = fetch_24h_weather()
    
yield_total = 0
if not tmy_24h.empty:
    with st.spinner("Generating Live Yield Models"):
        hourly_yield = generate_hourly_yield(tmy_24h, surface_tilt=15, surface_azimuth=180, viable_area_m2=10000)
        yield_total = hourly_yield.sum()

with st.spinner("Pulling Octopus Agile Live Spot Prices"):
    agile_prices = fetch_grid_prices()

# -----------------
# HEADER
# -----------------
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("SMART HOSPITAL ENERGY | North Tyneside general hospital")
    st.markdown("**Dashboard:** Overview | Buildings Plans | **Forecasts** | Reports")

bess_action = calculate_optimal_action(hourly_yield if yield_total > 0 else None, agile_prices)

with col_head2:
    st.info(bess_action.get("current_action_str", "**ACTION**: Standard Operation (Optimization Offline)"))

st.divider()

# -----------------
# LAYOUT
# -----------------
col_left, col_mid, col_right = st.columns([1.2, 1.8, 0.8])

# LEFT COLUMN: CHARTS
with col_left:
    with st.container(border=True):
        st.subheader("Weather & Yield Forecast")
        st.caption("Expected Solar Yield (kWh) · Temperature (°C) · Cloud Cover (%)")
        
        # Plot the daily TMY (Typical Meteorological Year) values alongside our solar yield curve
        if tmy_24h is not None and not tmy_24h.empty:
            fig_yield = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_yield.add_trace(
                go.Scatter(x=tmy_24h.index, y=hourly_yield, name="Expected Solar Yield", 
                           line=dict(color="#fbbc05", width=3, shape='spline'), fill='tozeroy', fillcolor='rgba(251,188,5,0.15)'),
                secondary_y=False,
            )
            fig_yield.add_trace(
                go.Scatter(x=tmy_24h.index, y=tmy_24h['temp_air'], name="Temperature",
                           line=dict(color="#4285f4", width=3, shape='spline')),
                secondary_y=True,
            )
            fig_yield.add_trace(
                go.Scatter(x=tmy_24h.index, y=tmy_24h['Cloud Cover (%)'], name="Cloud Cover (%)",
                           line=dict(color="#d3d3d3", width=2, dash='dot', shape='spline')),
                secondary_y=True,
            )
            fig_yield.update_layout(
                hovermode="x unified",
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=250
            )
            fig_yield.update_yaxes(showgrid=True, gridcolor="#eaeaea", secondary_y=False)
            fig_yield.update_yaxes(showgrid=False, secondary_y=True)
            
            st.plotly_chart(fig_yield, use_container_width=True, config={'displayModeBar': False})

    with st.container(border=True):
        st.subheader("Grid Price Forecast")
        st.caption("Grid Prices (p/kWh) | next 24 hours")
        
        if agile_prices is not None and not agile_prices.empty:
            fig_price = go.Figure()
            fig_price.add_trace(
                go.Scatter(x=agile_prices.index, y=agile_prices['value_inc_vat'], 
                           line=dict(color="#34a853", width=3, shape='spline'), fill='tozeroy', fillcolor='rgba(52,168,83,0.15)')
            )
            fig_price.update_layout(
                hovermode="x unified",
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=220
            )
            fig_price.update_yaxes(showgrid=True, gridcolor="#eaeaea")
            st.plotly_chart(fig_price, use_container_width=True, config={'displayModeBar': False})
        else:
            st.warning("Failed to fetch recent Octopus Agile Tariff rates.")

# MIDDLE COLUMN: GEOSPATIAL / 3D
with col_mid:
    with st.container(border=True):
        st.subheader(f"Expected yield over the next 24 hours: {yield_total:,.0f} kWh ↗")
        st.caption("Hospital Roof Model | Solar Arrays GeoJSON Overlay")
        
        try:
            # We attempt to dynamically load the hospital GEOJSON from the root directory to generate a real topography map
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
            file_path = os.path.join(base_dir, 'hospital_wings_matched.geojson')
            
            import geopandas as gpd
            # Load geojson and project to EPSG:4326 for PyDeck
            gdf = gpd.read_file(file_path)
            if gdf.crs:
                gdf = gdf.to_crs(epsg=4326)
            geojson_data = json.loads(gdf.to_json())
                
            # Render a high-quality 3D Extruded Map using PyDeck to emulate the mockup
            layer = pdk.Layer(
                "GeoJsonLayer",
                data=geojson_data,
                opacity=0.8,
                stroked=True,
                filled=True,
                extruded=True,
                wireframe=True,
                get_elevation=15, # we add a bit of fake elevation here just so the buildings pop out in 3D
                get_fill_color=[255, 180, 0, 200],  # Sunset Orange for solar
                get_line_color=[255, 255, 255],
                pickable=True
            )
            
            view_state = pdk.ViewState(
                latitude=55.024984,
                longitude=-1.468343,
                zoom=16.5,
                pitch=55,
                bearing=-15
            )
            
            tooltip = {"html": "<b>Roof Segment ID:</b> {id}"}
            
            # Fetch raster
            tif_path = os.path.join(base_dir, 'sawtooth_0', 'radiation_sawtooth_p15_g10_a0_w12_Autumn_Equinox.tif')
            image_data, image_bounds = fetch_roof_raster(tif_path, file_path)
            
            bitmap_layer = pdk.Layer(
                "BitmapLayer",
                image=image_data,
                bounds=image_bounds,
                opacity=0.75,
                pickable=False
            )
            
            r = pdk.Deck(layers=[layer, bitmap_layer], initial_view_state=view_state, map_provider="carto", map_style=pdk.map_styles.LIGHT, tooltip=tooltip)
            st.pydeck_chart(r, use_container_width=True)
            
        except Exception as e:
            st.error(f"Map Rendering Error: Could not locate `hospital_wings_matched.geojson` at {file_path}. ({e})")

# RIGHT COLUMN: METRICS / STORAGE
with col_right:
    with st.container(border=True):
        st.subheader("Modern Battery Storage")
        st.caption("ONLINE | CHARGING")
        
        st.markdown(f"<div style='text-align: center;'><span class='metric-value'>74%</span><br>1.48 MWh / 2.0 MWh Capacity</div>", unsafe_allow_html=True)
        st.progress(0.74, text="")
        
        st.markdown("---")
        schedule = bess_action.get("schedule", [])
        if schedule:
             for action in schedule:
                  st.write(f" **{action['time']}**  Expected 1.78 MWh ({action['type']} at {action['price']:.1f}p)")
        else:
             st.write("Schedule Optimization Offline")