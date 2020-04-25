import requests
from functools import lru_cache
from lib.handlers import alice

@lru_cache()
def get_id(token: str):
    r = requests.get('https://login.yandex.ru/info', headers={'Authorization': 'OAuth ' + str(token)})
    d = r.json()
    return d['id']

def form_alice_response(raw, trusted_ids):
    proceed_with_command = False

    token = raw['session'].get('user', {}).get('access_token')
    authorized = get_id(token) in trusted_ids if token else False
    resp = {'version': '1.0'}
    try:
        if raw['session'].get('new'):
            text = 'Control Kitty - это приватный навык для удалённого управления компьютерами с помощью голоса.'
            if not authorized:
                text += '\nДля работы с навыком необходима авторизация. Скажите "авторизоваться".'
            resp.update({'response': {'text': text, 'end_session': False}})
            if not authorized:
                resp['response'].update({'buttons': [{'title': 'Авторизоваться', 'hide': True}]})

        elif 'account_linking_complete_event' in raw:
            if not authorized:
                text = 'У вашего аккаунта нет прав для выполнения команд. Выберите другой аккаунт или обратитесь к разработчику.'
            else:
                text = 'Вы успешно авторизовались'
            resp.update({'response': {'text': text, 'end_session': False}})

        elif not raw.get('request').get('command'):
            resp.update({'response': {'text': 'Получено', 'end_session': False}})

        elif raw['request']['command'].lower() == 'авторизоваться':
            resp.update({"start_account_linking": {}})

        elif raw['request']['command'].lower() in ('помощь', 'что ты умеешь', 'что ты умеешь?'):
            text = 'Доступные команды:\n' + '\n'.join([x[0] for x in alice.inverse_readable.values()])
            if not authorized:
                text = 'Для выполнения команд необходима авторизация. Скажите "авторизоваться".\n' + text
            resp.update({'response': {'text': text, 'end_session': False}})

        else:
            if authorized:
                resp.update({'response': {'text': 'Выполняю...', 'end_session': False}})
                proceed_with_command = True
            else:
                resp.update({"start_account_linking": {}})
    except Exception as e:
        resp.update({'response': {'text': f'Ошибка: {e}', 'end_session': False}})

    return resp, proceed_with_command
