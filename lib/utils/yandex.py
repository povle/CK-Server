import requests
from functools import lru_cache

@lru_cache()
def get_id(token: str):
    r = requests.get('https://login.yandex.ru/info', headers={'Authorization': 'OAuth ' + str(token)})
    d = r.json()
    return d['id']
