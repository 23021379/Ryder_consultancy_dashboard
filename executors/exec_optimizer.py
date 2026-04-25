import pandas as pd

def get_optimum_configuration(df):
    """
    Look through whatever leftover data rows we have and just pick the one 
    that makes the most electricity per year.
    """
    if df is None or df.empty:
        return None
        
    best_row_idx = df['estimated_annual_yield_kwh'].idxmax()
    return df.loc[best_row_idx].to_dict()
