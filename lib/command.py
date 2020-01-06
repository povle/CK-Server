import time
import secrets
from .actions import Action

class Command:
    def __init__(self, handler, action: Action, sender, to, excepts=[], args=[]):
        self.handler = handler
        self.action = action
        self.sender = sender
        self.to = to
        self.excepts = excepts
        self.timestamp = time.time()
        self.id = secrets.token_hex(4)
        self.answers = {x: None for x in to}
        self.args = args
        self.sent_to = {}
        self.complete = False
        self.handled = False
        self.timeout = self.action.timeout

    def add_answer(self, comp_id, answer):
        if comp_id not in self.to and not self.broadcast: #FIXME: change broadcast mechanism (should not be a special case, just put all the necessary ids in self.to)
            raise KeyError
        ans = self.answers.get(comp_id)
        if ans is not None and ans.get('status') != 'error':
            #the target may want to reattempt the action
            #also newly connected should be able to respond
            raise ValueError('Already answered')
        self.answers[comp_id] = answer
        if all([x is not None for x in self.answers.values()]):
            self.complete = True
            self.be_handled()

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, val):
        if type(val) not in [list, set]:
            val = {val}
        self._to = val
        self.broadcast = 'all' in self._to

    def be_handled(self):
        if self.handled:
            return #FIXME: raise custom exception
        self.handled = True
        self.handler.handle(self)

    def to_dict(self):
        return {'command_id': self.id,
                'timestamp': self.timestamp,
                'to': list(self.to),
                'action': self.action.name,
                'timeout': self.action.timeout,
                'args': self.args}

    def is_targeted_to(self, cid):
        if self.broadcast:
            return cid not in self.excepts
        else:
            return cid in self.to and cid not in self.excepts

    def is_awaiting_dispatch(self, cid):
        return self.is_targeted_to(cid) and cid not in self.sent_to
