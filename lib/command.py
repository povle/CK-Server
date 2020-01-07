import time
import secrets
from .actions import Action
#FIXME: to - полные id получателей, ids - номера (без комнаты)
class Command:
    def __init__(self, handler, action: Action, sender, ids, room, excepts=[], args=[]):
        self.handler = handler
        self.action = action
        self.sender = sender
        self.ids = ids #comp numbers w/o rooms
        self.excepts = excepts #w/o rooms
        self.room = room
        self.answers = {}
        self.ready_for_dispatch = False
        if not self.broadcast and self.room not in ['all', 'default']:
            self.to = [f'{self.room}.{cid}' for cid in ids] #cids w/ rooms
        self.timestamp = time.time()
        self.id = secrets.token_hex(4)
        self.args = args
        self.sent_to = set() #w/ rooms
        self.complete = False
        self.handled = False
        self.timeout = self.action.timeout

    def add_answer(self, comp_id, answer):
        if not self.is_targeted_to(comp_id):
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
    def broadcast(self):
        return 'all' in self.ids or self.ids == 'all'

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, val):
        self._to = [x for x in val if self.is_targeted_to(x)]
        self.ready_for_dispatch = True
        for cid in self._to:
            if cid not in self.answers:
                self.answers[cid] = None

    def be_handled(self):
        if self.handled:
            raise RuntimeError('Already handled') #FIXME: raise custom exception
        self.handled = True
        self.handler.handle(self)

    def to_dict(self):
        return {'command_id': self.id,
                'timestamp': self.timestamp,
                'room': self.room,
                'to': self.to,
                'action': self.action.name,
                'timeout': self.action.timeout,
                'args': self.args}

    def is_targeted_to(self, cid):
        cid, room = self.get_id_room(cid)
        return self.room in (room, 'all')\
            and (cid in self.ids or self.broadcast)\
            and cid not in self.excepts

    def is_awaiting_dispatch(self, cid):
        return self.is_targeted_to(cid) and cid not in self.sent_to

    @staticmethod
    def get_id_room(rcid):
        spl = rcid.split('.')
        cid = spl[-1]
        room = spl[-2]
        return cid, room
