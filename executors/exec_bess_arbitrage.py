import pandas as pd
import numpy as np

def calculate_optimal_action(hourly_yield, agile_prices):
    """
    Looks at the upcoming solar yield and current grid prices to figure out 
    what the battery should be doing right now (charge, discharge, sit tight).
    
    Spits back a dictionary with the current action and a schedule of upcoming charge/discharge windows.
    """
    if hourly_yield is None or agile_prices is None or hourly_yield.empty or agile_prices.empty:
        return {
            "current_action_str": "**ACTION**: Standard Operation (Optimization Offline)",
            "charge_windows": [],
            "discharge_windows": []
        }
        
    try:
        # step 1: line up the timelines. The grid prices update every 30 mins, 
        # so we need to stretch our hourly solar forecast to match that rhythm.
        
        # Ensure agile_prices is sorted
        df_prices = agile_prices.copy().sort_index()
        
        # Resample yield to 30-min and forward fill
        df_yield = hourly_yield.copy()
        if not isinstance(df_yield.index, pd.DatetimeIndex):
            df_yield.index = pd.to_datetime(df_yield.index)
            
        if df_yield.index.tz is None and df_prices.index.tz is not None:
             df_yield.index = df_yield.index.tz_localize(df_prices.index.tz)
             
        df_yield_30m = df_yield.resample('30T').ffill()
        
        # mash the price and yield data together where their times overlap
        merged = pd.merge(df_prices, df_yield_30m.rename('yield_kw'), left_index=True, right_index=True, how='inner')
        if merged.empty:
            raise ValueError("No overlapping time periods between yield and price datasets.")
            
        # Use real time localized to the dataset's timezone
        now = pd.Timestamp.now(tz=merged.index.tz).floor('30T')
        
        # figure out which 30-min chunk represents "right now"
        if now in merged.index:
            current_idx = now
        elif now < merged.index[0]:
            current_idx = merged.index[0]
        else:
            past_times = merged.index[merged.index <= now]
            current_idx = past_times[-1] if not past_times.empty else merged.index[-1]
            
        current_time = current_idx
        current_price = merged.loc[current_idx, 'value_inc_vat']
        current_yield = merged.loc[current_idx, 'yield_kw']
        
        # crunch some percentiles so we know what counts as "expensive" or "cheap" relative to the rest of the day
        price_95th = merged['value_inc_vat'].quantile(0.95)
        price_80th = merged['value_inc_vat'].quantile(0.80)
        price_50th = merged['value_inc_vat'].quantile(0.50)
        price_15th = merged['value_inc_vat'].quantile(0.15)
        yield_70th = merged['yield_kw'].quantile(0.70)
        
        upcoming_24h_yield = merged['yield_kw'].sum()
        # if we aren't expecting much sun today, we'll call that a "yield drought"
        yield_drought_threshold = yield_70th * 6 
        
        # step 2: the actual decision making. A big if/else tree to decide what the battery should do.
        action_msg = ""
        action_reason = ""
        
        if current_price < 0:
             action_msg = "MAX CHARGE (Grid)"
             action_reason = f"Negative Pricing Crisis (Grid paying: {current_price:.1f}p/kWh)"
        elif current_price >= price_95th:
             action_msg = "DISCHARGE (Hospital + Grid Export)"
             action_reason = f"Extreme Peak Run (Price extraordinarily high: {current_price:.1f}p/kWh)"
        elif current_price < price_50th and upcoming_24h_yield < yield_drought_threshold:
             action_msg = "BUY TO STORE (Defensive)"
             action_reason = f"Yield Drought Pre-Charge (Low upcoming solar, reasonable grid price: {current_price:.1f}p/kWh)"
        elif current_price >= price_80th:
             action_msg = "DISCHARGE (Hospital Only)"
             action_reason = f"Standard Peak Avoidance (Avoid drawing at {current_price:.1f}p/kWh)"
        elif current_price <= price_15th:
             action_msg = "BUY TO STORE (Opportunistic)"
             action_reason = f"Plunge Pricing (Grid Price Low: {current_price:.1f}p/kWh, Expected to rise)"
        elif current_yield > yield_70th and current_price < price_80th:
             action_msg = "STORE SOLAR"
             action_reason = f"Solar Excess Storage (Yield High, Grid Price Average)"
        else:
             action_msg = "DIRECT SOLAR / STANDARD USAGE"
             action_reason = f"Balanced default conditions"
             
        current_action_str = f"**ACTION**: {action_msg}\n\nTime: {current_time.strftime('%H:%M %Z')} | Reason: {action_reason}"
        
        # step 3: look ahead. Grab the two most expensive slots to sell, and the two cheapest to buy.
        top_discharge = merged.nlargest(2, 'value_inc_vat')
        top_charge_prices = merged.nsmallest(2, 'value_inc_vat')
        
        # package these up nicely so the dashboard can read them easily
        discharge_windows = []
        for idx, row in top_discharge.iterrows():
            time_str = idx.strftime('%H:%M')
            discharge_windows.append({"time": time_str, "type": "Discharging", "price": row['value_inc_vat']})
            
        charge_windows = []
        for idx, row in top_charge_prices.iterrows():
            time_str = idx.strftime('%H:%M')
            charge_windows.append({"time": time_str, "type": "Charging", "price": row['value_inc_vat']})
            
        # throw them all in one list and sort them chronologically for the UI schedule
        all_windows = sorted(charge_windows + discharge_windows, key=lambda x: x['time'])
            
        return {
            "current_action_str": current_action_str,
            "schedule": all_windows
        }
        
    except Exception as e:
        print(f"BESS Arbitrage Error: {e}")
        return {
            "current_action_str": "**ACTION**: Standard Operation (Optimization Offline)",
            "schedule": []
        }
