import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

@st.cache_data(ttl=1800)
def fetch_grid_prices():
    # calling the octopus energy agile api to get the real-time wholesale prices. 
    # we're hardcoding this to the active tariff right now.
    url = "https://api.octopus.energy/v1/products/AGILE-24-10-01/electricity-tariffs/E-1R-AGILE-24-10-01-A/standard-unit-rates/"
    
    now = datetime.utcnow()
    # grab the last 12 hours and the next 12 hours so we have a full rolling window
    period_from = now - timedelta(hours=12)
    period_to = now + timedelta(hours=13)  # a bit extra to ensure overlap
    
    params = {
        "period_from": period_from.isoformat() + "Z",
        "period_to": period_to.isoformat() + "Z",
        "page_size": 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        if not results:
            return pd.DataFrame()
            
        df = pd.DataFrame(results)
        df['valid_from'] = pd.to_datetime(df['valid_from']).dt.tz_convert('Europe/London')
        df = df.sort_values('valid_from')
        df.set_index('valid_from', inplace=True)
        return df[['value_inc_vat']]
    except Exception as e:
        print(f"Error fetching Octopus prices: {e}")
        return pd.DataFrame()
