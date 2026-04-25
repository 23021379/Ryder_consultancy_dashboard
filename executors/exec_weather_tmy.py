import streamlit as st
import pandas as pd
import numpy as np
import pvlib

@st.cache_data(ttl=86400)
def fetch_24h_weather(latitude=55.024984, longitude=-1.468343, tz='Europe/London'):
    # pvgis gives us a pile of stuff back, but we just want the main weather data table
    res = pvlib.iotools.get_pvgis_tmy(latitude, longitude, map_variables=True)
    tmy_data = res[0]
    tmy_data.index = tmy_data.index.tz_convert(tz)
    
    now = pd.Timestamp.now(tz=tz).replace(minute=0, second=0, microsecond=0)
    start_time = now - pd.Timedelta(hours=12)
    end_time = now + pd.Timedelta(hours=12)
    
    times = pd.date_range(start_time, end_time, freq='h')
    
    # we need the weather for *today*, but tmy data is a generic "typical year", so we match it up by month and day
    rows = []
    for t in times:
        try:
            # Find matching absolute month/day/hour irrespective of year
            mask = (tmy_data.index.month == t.month) & \
                   (tmy_data.index.day == t.day) & \
                   (tmy_data.index.hour == t.hour)
            row = tmy_data[mask].iloc[0].copy()
            row['synthetic_time'] = t
            rows.append(row)
        except IndexError:
            pass
            
    df = pd.DataFrame(rows)
    if not df.empty:
        df.set_index('synthetic_time', inplace=True)
        
        # we have the actual air temp, but we have to guess the cloud cover by comparing what the sun *should* look like (clear sky) to what it *actually* looks like (ghi)
        location = pvlib.location.Location(latitude, longitude, tz=tz)
        cs = location.get_clearsky(df.index)
        
        # can't divide by zero when the sun is down!
        max_ghi = cs['ghi'].replace(0, 1)
        ratio = df['ghi'] / max_ghi
        cloud_cover = (1.0 - ratio) * 100
        # keep it sane, cloud cover can't be -10% or 150%
        df['Cloud Cover (%)'] = np.clip(cloud_cover, 0, 100).fillna(0)
        
    return df
