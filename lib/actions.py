from .types import Type

class Action:
    def __init__(self, name: str, description='', answer_types=set(),
                 arg_types=set(), admin_only=False, timeout=10):
        self.name = name
        self.arg_types = arg_types
        self.answer_types = answer_types
        self.answer_types.update({Type.ERROR, Type.OK})
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
    Action('update_config', arg_types={Type.TEXT}, admin_only=True,
           description="изменить конфиг, аргумент: ключ значение(проходит через ast.literal_eval)"),
    Action('off', description="выключить компьютер"),
    Action('restart', description="перезагрузить компьютер"),
    Action('sleep', description="перевести компьютер в режим сна"),
    Action('logout', description="выйти из пользователя"),
    Action('scr', arg_types={Type.TEXT}, answer_types={Type.PHOTO, Type.DOCUMENT},
           description="сделать скриншот, scr -d - скриншот документом"),
    Action('screen_off', description="отключить экран"),
    Action('screen_on', description="включить экран"),
    Action('wallpaper', arg_types={Type.PHOTO},
           description="сменить обои (новые прислать документом)"),
    Action('upload', arg_types={Type.DOCUMENT, Type.TEXT},
           description='загрузить прикреплённые документы в папку "Задания", upload -o открывает загруженный файл'),
    Action('move', arg_types={Type.TEXT},
           description='переместить всё содержимое папки "Задания" в папку "Старое"'),
    Action('altf', description="alt + f4"),
    Action('mute', description="выключить звук"),
    Action('unmute', description="включить звук"),
    Action('bin', description="очистить корзину"),
    Action('d'),
    Action('status', answer_types={Type.TEXT}, description="статус"),
    Action('test', answer_types={Type.TEXT}, description="test"),
    Action('version', answer_types={Type.TEXT}, description="версия клиента"),
    Action('quit', description="остановить бота")
]
