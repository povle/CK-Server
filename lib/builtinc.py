from .actions import actions, Action
from .types import Type
from .utils import vk_keyboard as _vk_keyboard

class BuiltinAction(Action):
    def __init__(self, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = func
        self.timeout = 0

    def execute(self, args=[]):
        kwargs = {'text': '', 'documents': [], 'photos': []}
        for arg in args:
            if arg['type'] == 'text':
                kwargs['text'] += arg['text']
            else:
                kwargs[arg['type']+'s'].append(arg)
        kwargs = {key: kwargs[key] for key in kwargs if kwargs[key]}
        response = self.func(**kwargs)
        if type(response) is str:
            response = {'type': 'text', 'text': response}
        if type(response) is not list:
            response = list(response)
        return self.make_answer(response)

    def make_answer(self, payload):
        ans = {'status': 'ok',
               'payload': payload
               }
        return ans

class ErrorAction(Action):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 0

    def execute(self, args=[]):
        for arg in args:
            if arg['type'] == 'exception':
                e = arg['exception']
        msg = getattr(e, 'message', str(e))
        if not msg:
            msg = repr(e)
        ans = {'status': 'error',
               'message': msg,
               'exception': type(e).__name__
               }
        return ans


error_action = ErrorAction('error')

def help(text=''):
    message = ''
    for f in actions + builtin_actions:
        doc = f.description
        if doc and (text != '-a' and not f.admin_only)\
                or (text == '-a' and f.admin_only):
            message += f'•{f.name} - {doc}\n'
    return message

def vk_keyboard(text=''):
    if not text:
        keyboard = _vk_keyboard.keyboard
    elif text == '-a':
        keyboard = _vk_keyboard.admin_keyboard
    return [{'type': 'keyboard', 'keyboard': keyboard.get_keyboard()},
            {'type': 'text', 'text': 'Клавиатура подана'}]


builtin_actions = {
    BuiltinAction(func=help, name='help', answer_types={Type.TEXT}, arg_types={Type.TEXT}),
    BuiltinAction(func=vk_keyboard, name='keyboard', answer_types={Type.VK_KEYBOARD},
                  arg_types={Type.TEXT}, description="включить клавиатуру")
}
