from .. import Handler, Type, Command, AuthError

class DirectHandler(Handler):
    def __init__(self, secret):
        super().__init__(answer_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT},
                         arg_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT})
        self.secret = secret

    def initial_parse(self, raw: dict):
        if raw.get('secret') != self.secret:
            raise AuthError
        parsed = raw['command']
        return {'action': parsed['action'], 'sender': 0,
                'ids': parsed['ids'], 'room': parsed['room'],
                'args': parsed['args'], 'excepts': parsed.get('excepts', [])}

    def handle(self, command: Command):
        return command.answers

    def handle_late(self, command: Command, cid: str):
        pass
