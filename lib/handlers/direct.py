from lib import Handler, Type, Command, AuthError
from lib.utils import checkpw
import base64

class DirectHandler(Handler):
    def __init__(self, secret):
        super().__init__(answer_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT},
                         arg_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT})
        self.secret = secret

    def initial_parse(self, raw: dict):
        if not checkpw(raw.get('secret', '').encode('utf8'), self.secret):
            raise AuthError
        parsed = raw['command']
        args = parsed.get('args', [])
        for arg in args:
            if 'data' in arg:
                arg['data'] = base64.b64decode(arg['data'])

        return {'action': parsed['action'], 'ids': parsed['ids'], 'room': parsed['room'],
                'args': args, 'excepts': parsed.get('excepts', [])}

    def handle(self, command: Command):
        return command.answers

    def get_sender(self, raw):
        return 0

    def handle_late(self, command: Command, cid: str):
        pass
