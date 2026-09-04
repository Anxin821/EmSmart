import requests
from datetime import datetime
from pathlib import Path
import sys

base = 'http://127.0.0.1:8001/api/v1'
creds = {'username':'admin','password':'admin123'}

r = requests.post(base + '/auth/login', json=creds, timeout=10)
if r.status_code != 200:
    print('LOGIN_FAIL', r.text)
    sys.exit(1)

token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

year, week, _ = datetime.utcnow().isocalendar()
print('ISO_YEAR_WEEK', year, week)
params = {'year': year, 'week': week, 'page': 1, 'page_size': 10}
resp = requests.get(base + '/production/weekly', headers=headers, params=params, timeout=10)
if resp.status_code != 200:
    print('REQUEST_FAIL', resp.status_code, resp.text)
    sys.exit(1)

data = resp.json().get('data', {})
items = data.get('items') if isinstance(data, dict) else None
count = len(items) if items else 0
print('RESULT_COUNT', count)
if count>0:
    print('FIRST_ITEM', items[0])
