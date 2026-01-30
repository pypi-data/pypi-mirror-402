import requests


max_lim = 10000


for i in range(max_lim):
    resp = requests.get('http://localhost:5001/api/v1/example-send-temp-file')
    print(f'{i}/{max_lim} = {resp.status_code}')  # noqa
    resp.raise_for_status()
