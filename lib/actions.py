from types import Type

class Action:
    def __init__(self, name: str, description='', answer_types={},
                 arg_types={}, admin_only=False, timeout=10):
        self.name = name
        self.arg_types = arg_types
        self.answer_types = answer_types + {Type.ERROR, Type.OK}
        self.admin_only = admin_only
        self.description = description
        self.timeout = timeout


actions = [
    Action('cmd', arg_types={Type.TEXT}, admin_only=True),
    Action('nircmd', arg_types={Type.TEXT}, admin_only=True),
    Action('press', arg_types={Type.TEXT}, admin_only=True),
    Action('python', arg_types={Type.TEXT}, admin_only=True),
    Action('off'),
    Action('restart'),
    Action('sleep'),
    Action('logout'),
    Action('screenshot', answer_types={Type.PHOTO}),
    Action('screen_off'),
    Action('wallpaper', arg_types={Type.PHOTO}),
    Action('upload', arg_types={Type.DOCUMENT}),
    Action('move', arg_type={Type.TEXT}),
    Action('altf'),
    Action('volume'),
    Action('bin'),
    Action('d'),
    Action('status', answer_types={Type.TEXT}),
    Action('quit')
]
