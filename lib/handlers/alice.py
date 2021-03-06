from lib import Handler, Type, Command
from difflib import SequenceMatcher

inverse_readable = {'off': ['выключи компьютер', 'выключи', 'компьютер выключи', 'выключи комп', 'комп выключи'],
                    'screen_off': ['выключи экран', 'экран', 'экран выключи'],
                    'mute': ['выключи звук', 'звук', 'звук выключи'],
                    'unmute': ['включи звук', 'звук включи'],
                    'restart': ['перезагрузи', 'перезагрузка', 'перезагрузи комп', 'комп перезагрузи'],
                    'altf': ['закрой приложение', 'приложение закрой', 'закрой программу'],
                    'sleep': ['переведи в режим сна', 'перейди в режим сна', 'сон', 'режим сна', 'спать'],
                    'quit': ['останови бота', 'бота останови'],
                    'bin': ['очисти корзину', 'корзину очисти'],
                    'd': ['открой дисковод', 'дисковод', 'дисковод открой']}
readable = {}
for k in inverse_readable:
    for v in inverse_readable[k]:
        readable[v] = k


class AliceHandler(Handler):
    def __init__(self,):
        super().__init__(answer_types={Type.TEXT},
                         arg_types={Type.TEXT})
        self.readable = readable

    def initial_parse(self, raw):
        parsed = self.parse_request(raw['request'])
        args = []
        if parsed['args']:
            args.append({'type': 'text', 'text': parsed['args']})

        action = self.closest_action(parsed['action'], 0.8)
        if action is None:
            raise ValueError('Unknown action')
        action = self.readable[action]

        return {'action': action,
                'ids': parsed['ids'],
                'room': parsed['room'],
                'args': args,
                'excepts': parsed['excepts']
                }

    def parse_request(self, request: dict):
        ids = []
        excepts = []
        nlu = request['nlu']

        entities = nlu.get('entities', [])
        for ent in entities:
            if ent['type'] == 'YANDEX.NUMBER':
                ids.append(str(ent['value']))

        tokens = nlu['tokens']
        excepts_present = 'кроме' in tokens
        broadcast = 'все' in tokens or 'всех' in tokens or not ids or excepts_present

        action = ' '.join([x for x in tokens if x not in ids+['все', 'всех', 'кроме', 'и', 'на']])

        if broadcast:
            if excepts_present:
                excepts = ids
            ids = ['all']

        return {'ids': ids, 'excepts': excepts, 'action': action, 'args': [], 'room': 'default'}

    def closest_action(self, text, threshold):
        d = {x: SequenceMatcher(None, x, text).ratio() for x in self.readable.keys()}
        a = sorted(d.keys(), key=lambda x: d[x], reverse=True)
        if d[a[0]] < threshold:
            return None
        return a[0]

    def handle(self, command: Command):
        pass

    def handle_late(self, command: Command, cid: str):
        pass

    def get_sender(self, raw):
        return raw['session']['user']['user_id']
