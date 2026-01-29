import requests
import time
from decimal import Decimal
import time
from datetime import datetime
import json
import pandas as pd

def get_report(cik, report_type, metrics, num_reports):

    result_df = pd.DataFrame()

    for metric in metrics:

        params = {
            'cik' : cik,
            'metric' : metric,
            'num_reports' : num_reports
        }
        if report_type == '10-Q':
            base_url = 'https://anselmjuan.pythonanywhere.com/10q'
        if report_type == '10-K':
            base_url = 'https://anselmjuan.pythonanywhere.com/10k'
        
        df = pd.DataFrame(requests.get(base_url, params=params).json())

        if df.empty:
            continue

        # Columns you want first
        first_two = ["Period Start", "Period End"]

        # Get the rest of the columns
        rest = [col for col in df.columns if col not in first_two]

        # Create new column order
        new_order = first_two + rest

        df = df[new_order]

        if df['Period Start'].isna().all():
            df = df.drop(columns=['Period Start'])

        if len(result_df) == 0:
            result_df = df
        else:
            result_df = result_df.merge(df, on="Period End", how="outer")
    
    return result_df