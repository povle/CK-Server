import time
import secrets
from actions import Action

class Command:
    def __init__(self, handler, action: Action, sender, to, args=[]):
        self.handler = handler
        self.action = action
        if type(to) not in [list, set]:
            to = {to}
        self.sender = sender
        self.to = to
        self.timestamp = time.time()
        self.id = secrets.token_hex(4)
        self.answers = {x: None for x in to}
        self.args = args
        self.complete = False

    def add_answer(self, comp_id, answer):
        if comp_id not in self.answers:
            raise KeyError
        if self.answers[comp_id] is not None:
            raise ValueError
        self.answers[comp_id] = answer
        if all([x is not None for x in self.answers.values()]):
            self.complete = True

    def be_handled(self):
        self.handler.handle(self)

    def to_dict(self):
        return {'command_id': self.id,
                'timestamp': self.timestamp,
                'to': list(self.to),
                'action': self.action.name,
                'timeout': self.action.timeout,
                'args': self.args}
