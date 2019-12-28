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
    Action('cmd', arg_types={Type.TEXT}, admin_only=True,
           description="выполнить заданную команду"),
    Action('nircmd', arg_types={Type.TEXT}, admin_only=True,
           description="выполнить заданную команду nircmd"),
    Action('press', arg_types={Type.TEXT}, admin_only=True,
           description="нажать заданные клавиши"),
    Action('python', arg_types={Type.TEXT}, admin_only=True,
           description="выполнить заданный код на python"),
    Action('off', description="выключить компьютер"),
    Action('restart', description="перезагрузить компьютер"),
    Action('sleep', description="перевести компьютер в режим сна"),
    Action('logout', description="выйти из пользователя"),
    Action('screenshot', answer_types={Type.PHOTO},
           description="сделать скриншот"),
    Action('screen_off', description="отключить экран"),
    Action('wallpaper', arg_types={Type.PHOTO},
           description="сменить обои (новые прислать документом)"),
    Action('upload', arg_types={Type.DOCUMENT},
           description='загрузить прикреплённые документы в папку "Задания"'),
    Action('move', arg_type={Type.TEXT},
           description='переместить всё содержимое папки "Задания" в папку "Старое"'),
    Action('altf', description="alt + f4"),
    Action('volume', description="выключить звук"),
    Action('bin', description="очистить корзину"),
    Action('d'),
    Action('status', answer_types={Type.TEXT}, description="статус"),
    Action('quit', description="остановить бота")
]
