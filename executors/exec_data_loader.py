import streamlit as st
import pandas as pd
import os

@st.cache_data
def load_data():
    # using relative paths based on this script's location so you can run the dashboard from anywhere
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    
    # Load Uniform Data
    dfs_u = []
    u_sawtooth = os.path.join(base_dir, 'ryder_pv_v6_annual.csv')
    if os.path.exists(u_sawtooth):
        df = pd.read_csv(u_sawtooth)
        if 'roof_type' not in df.columns:
            df['roof_type'] = 'sawtooth'
        dfs_u.append(df)
        
    u_waffle = os.path.join(base_dir, 'ryder_pv_v6_annual_waffle.csv')
    if os.path.exists(u_waffle):
        df = pd.read_csv(u_waffle)
        if 'roof_type' not in df.columns:
            df['roof_type'] = 'waffle'
        dfs_u.append(df)
        
    df_uniform = pd.concat(dfs_u, ignore_index=True) if dfs_u else pd.DataFrame()
            
    # Load Non-Uniform Data
    dfs_nu = []
    nu_sawtooth = os.path.join(base_dir, 'ryder_non_uniform_v6_annual.csv')
    if os.path.exists(nu_sawtooth):
        df = pd.read_csv(nu_sawtooth)
        if 'roof_type' not in df.columns:
            df['roof_type'] = 'sawtooth'
        dfs_nu.append(df)
        
    nu_waffle = os.path.join(base_dir, 'ryder_non_uniform_v6_annual_waffle.csv')
    if os.path.exists(nu_waffle):
        df = pd.read_csv(nu_waffle)
        if 'roof_type' not in df.columns:
            df['roof_type'] = 'waffle'
        dfs_nu.append(df)
        
    df_non_uniform = pd.concat(dfs_nu, ignore_index=True) if dfs_nu else pd.DataFrame()
        
    return df_uniform, df_non_uniform
