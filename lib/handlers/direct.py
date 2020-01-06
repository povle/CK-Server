from .. import Handler, Type, Command

class DirectHandler(Handler):
    def __init__(self, secret):
        super().__init__(answer_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT},
                         arg_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT})
        self.secret = secret

    def initial_parse(self, raw: dict):
        if raw.get('secret') != self.secret:
            raise ValueError #FIXME: AuthError
        parsed = raw['command']
        return {'action': parsed['action'], 'sender': 0,
                'to': parsed['to'], 'args': parsed['args'], 'excepts': parsed.get('excepts', [])}

    def handle(self, command: Command):
        return command.answers