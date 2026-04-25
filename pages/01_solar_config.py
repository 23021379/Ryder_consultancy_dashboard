import streamlit as st
import matplotlib.pyplot as plt
from executors.exec_data_loader import load_data
from executors.exec_optimizer import get_optimum_configuration
from executors.exec_cross_section import generate_single_cross_section

st.set_page_config(page_title="Solar Configuration Dashboard", layout="wide")

# just throwing in some custom CSS to clean up the cards and stop the metrics from getting truncated
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
    }
</style>
""", unsafe_allow_html=True)

df_uniform, df_non_uniform = load_data()

st.title("Solar Configuration Dashboard")
st.markdown("Change parameters to find the maximum annual yield configuration.")

col_controls, col_display = st.columns([1, 3])

with col_controls:
    st.subheader("Controls")
    mode = st.radio("Array Setup Mode", ["Uniform", "Non-Uniform"])
    
    # We calculate the available roof types
    all_rt = set(df_uniform.get('roof_type', [])) | set(df_non_uniform.get('roof_type', []))
    all_roof_types = sorted(list(all_rt)) if all_rt else ['sawtooth']
    roof_type = st.selectbox("Roof Type", options=all_roof_types, index=0)
    
    # We filter data down to the selected roof_type to generate accurate slider ranges
    df_u_filtered = df_uniform[df_uniform.get('roof_type', 'sawtooth') == roof_type] if not df_uniform.empty else df_uniform
    df_nu_filtered = df_non_uniform[df_non_uniform.get('roof_type', 'sawtooth') == roof_type] if not df_non_uniform.empty else df_non_uniform
    
    all_az = set(df_u_filtered.get('azimuth', [])) | set(df_nu_filtered.get('azimuth', []))
    all_azimuths = sorted(list(all_az)) if all_az else [-45]
    azimuth = st.select_slider("Azimuth (°)", options=all_azimuths, value=all_azimuths[1] if len(all_azimuths) > 1 else all_azimuths[0])
    
    all_w = set(df_u_filtered.get('panel_width', [])) | set(df_nu_filtered.get('panel_width', []))
    all_widths = sorted(list(all_w)) if all_w else [8]
    width = st.select_slider("Panel Width (m)", options=all_widths, value=all_widths[0])
    
    all_g = set(df_u_filtered.get('gap', [])) | set(df_nu_filtered.get('gap', []))
    all_gaps = sorted(list(all_g)) if all_g else [10]
    # Handle the case where the default 10 might not exist in the filtered options
    default_gap = 10 if 10 in all_gaps else all_gaps[0]
    gap = st.select_slider("Gap (m)", options=all_gaps, value=default_gap)

with col_display:
    st.subheader("Optimal Cross Section")
    # Filter datasets and get best row
    if mode == "Uniform":
        df = df_uniform
    else:
        df = df_non_uniform

    if df is not None and not df.empty:
        # Pre-filter
        df_filtered = df[(df.get('roof_type', 'sawtooth') == roof_type) & (df['azimuth'] == azimuth) & (df['panel_width'] == width) & (df['gap'] == gap)]
        best_cfg = get_optimum_configuration(df_filtered)

        if best_cfg is None:
            st.error("No valid configurations found for these parameters.")
        else:
            yield_val = best_cfg['estimated_annual_yield_kwh']
            area_m2 = best_cfg['viable_pv_area_m2']
            
            # Commercial Calculations (Based on Canadian Solar CS3W-440MS)
            # Exact Dimensions: 2108 mm x 1048 mm = ~2.21 m² per physical 440W module
            num_panels = int(area_m2 / 2.21)
            system_kwp = (num_panels * 440) / 1000.0
            
            # Costs
            panel_cost = num_panels * 166 # Interpolated from ~400W and 450W brackets
            mounting_and_labour = num_panels * 85
            fixed_bos = 80000
            total_cost = panel_cost + mounting_and_labour + fixed_bos
            
            # Financial Returns (Assuming a conservative £0.25/kWh Commercial Rate)
            commercial_electricity_rate = 0.25
            annual_savings = yield_val * commercial_electricity_rate
            
            # Additional derived metrics
            payback_period = total_cost / annual_savings if annual_savings > 0 else 0
            yield_per_panel = yield_val / num_panels if num_panels > 0 else 0
            savings_per_panel = annual_savings / num_panels if num_panels > 0 else 0
            cost_per_panel = total_cost / num_panels if num_panels > 0 else 0
            
            # Duration (Assumes 17.5 panels per day average on complex active roofs, 5 day work week)
            install_days = num_panels / 17.5
            install_weeks = install_days / 5
            
            st.write("### Project Viability Metrics (CS3W-440MS Baseline)")
            
            with st.container(border=True):
                st.markdown("**Overview & ROI**")
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Annual Yield", f"{yield_val / 1000:,.1f} MWh")
                m2.metric("Annual Savings", f"£{annual_savings / 1000:,.1f}k")
                m3.metric("System Size", f"{system_kwp:,.0f} kWp")
                m4.metric("Est. Total Cost", f"£{total_cost / 1000:,.1f}k")
                m5.metric("Payback Period", f"{payback_period:.1f} Yrs")

            with st.container(border=True):
                st.markdown("**Unit Economics & Operations**")
                u1, u2, u3, u4, u5 = st.columns(5)
                u1.metric("Total Panels", f"{num_panels:,} Units")
                u2.metric("Yield / Panel", f"{yield_per_panel:,.0f} kWh/yr")
                u3.metric("Savings / Panel", f"£{savings_per_panel:,.0f}/yr")
                u4.metric("Cost / Panel", f"£{cost_per_panel:,.0f} (Inst.)")
                u5.metric("Install Time", f"{install_weeks:.1f} wks")
            
            st.divider()
            
            # Map params for plot
            if mode == "Uniform":
                pitch = float(best_cfg['pitch'])
                s_p = n_p = pitch
                p_c = 1.0
                title_str = f"Uniform Optimal ({pitch:.1f}°) | Yield: {yield_val:,.0f} kWh"
            else:
                s_p = float(best_cfg['southern_most_pitch'])
                n_p = float(best_cfg['northern_most_pitch'])
                p_c = float(best_cfg['pitch_change'])
                title_str = f"Non-Uniform Optimal ({p_c} Exp) | Yield: {yield_val:,.0f} kWh"

            fig = generate_single_cross_section(width, gap, s_p, n_p, p_c, title_str)
            st.pyplot(fig)
            plt.close(fig)
                
            st.divider()
            st.write("### Topographical Raytracing (Seasonal Progression)")
            st.markdown("Visualising the structural shading interactions across the 4 major solar seasons.")
            
            import os
            import rasterio
            import numpy as np
            
            seasons = ['Spring_Equinox', 'Summer_Solstice', 'Autumn_Equinox', 'Winter_Solstice']
            season_labels = seasons
            s_cols = st.columns(4)
            
            base_workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
            
            for i, season in enumerate(seasons):
                if mode == "Uniform":
                    pitch = int(float(best_cfg['pitch']))
                    file_name = f"radiation_{roof_type}_p{pitch}_g{int(gap)}_a{int(azimuth)}_w{int(width)}_{season}.tif"
                    file_path = os.path.join(base_workspace, f"{roof_type}_{int(azimuth)}", file_name)
                else:
                    p_c = float(best_cfg['pitch_change'])
                    file_name = f"rad_{season}_g{int(gap)}_c{p_c}.tif"
                    # Handle legacy sawtooth folder naming ('a' instead of 'sawtooth_')
                    folder_prefix = f"a{int(azimuth)}" if roof_type == 'sawtooth' else f"{roof_type}_{int(azimuth)}"
                    file_path = os.path.join(base_workspace, 'experiment_non_uniform', f"{folder_prefix}_w{int(width)}", file_name)
                
                with s_cols[i]:
                    st.markdown(f"<div style='text-align: center; font-weight: 600; color: #2b3a55; margin-bottom: 5px;'>{season_labels[i]}</div>", unsafe_allow_html=True)
                    if os.path.exists(file_path):
                        try:
                            with rasterio.open(file_path) as src:
                                arr = src.read(1)
                                nodata = src.nodata
                                if nodata is not None:
                                    arr = np.where(arr == nodata, np.nan, arr)
                                # clean up the background pixels so the empty space becomes transparent
                                arr = np.where(arr <= 0.01, np.nan, arr)
                                
                                fig, ax = plt.subplots(figsize=(4, 4))
                                ax.imshow(arr, cmap='inferno', interpolation='bilinear')
                                ax.axis('off')
                                plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
                                st.pyplot(fig)
                                plt.close(fig)
                        except Exception as e:
                            st.caption(f"Render failed: {e}")
                    else:
                        st.caption("Simulation file not currently available for these exact parameters.")
                        
    else:
        st.error("Dataset not loaded properly.")
