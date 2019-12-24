import time
import secrets
from actions import Action

class Command:
    def __init__(self, handler, action: Action, sender, to):
        self.handler = handler
        self.action = action
        if type(to) not in [list, set]:
            to = {to}
        self.sender = sender
        self.to = to
        self.timestamp = time.time()
        self.id = secrets.token_hex(4)
        self.answers = {x: None for x in to}

    def be_handled(self):
        self.handler.handle(self)
