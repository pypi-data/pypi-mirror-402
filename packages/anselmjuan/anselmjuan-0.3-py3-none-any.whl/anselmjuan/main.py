import requests
import time
from decimal import Decimal
import time
from datetime import datetime
import json

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
    
    return requests.get(base_url, params=params).json()
