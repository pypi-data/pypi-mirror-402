import requests
import time
from decimal import Decimal
import time
from datetime import datetime
import json
import pandas as pd

def get_report(cik, report_type, metric, num_reports):

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

    # Columns you want first
    first_three = ["Period Start", "Period End", "Filing Date"]

    # Get the rest of the columns
    rest = [col for col in df.columns if col not in first_three]

    # Create new column order
    new_order = first_three + rest

    return df[new_order]