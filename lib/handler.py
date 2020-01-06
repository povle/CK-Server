from .command import Command
from .types import Type
from abc import ABC, abstractmethod
from .actions import actions, Action
import inspect
import time
from . import builtinc

class Handler(ABC):
    def __init__(self, arg_types={}, answer_types={}):
        self.arg_types = arg_types
        self.answer_types = answer_types
        self.answer_types.update({Type.ERROR, Type.OK})
        self.builtins = {name: func for name, func in inspect.getmembers(
            builtinc, predicate=inspect.isfunction)}
        self.actions = [x for x in actions
                        if x.arg_types.issubset(self.arg_types) and
                        x.answer_types.issubset(self.answer_types)]

    def handle_builtins(self, command):
        if command.action.name in self.builtins:
            payload = self.builtins[command.action.name](command.args)
            ans = {'comp_id': -1,
                   'command_id': command.id,
                   'timestamp': time.time(),
                   'status': 'ok',
                   'payload': payload
                   }
            command.add_answer(-1, ans)
            return True
        return False

    @abstractmethod
    def initial_parse(self, raw: dict) -> dict:
        pass

    def parse(self, raw: dict) -> Command:
        '''Parse raw input'''
        parsed = self.initial_parse(raw)
        action_name = parsed['action']
        sender = parsed['sender']
        to = parsed['to']
        args = parsed['args']
        excepts = parsed.get('excepts', [])
        action_name = [x for x in [a.name for a in self.actions] + list(self.builtins.keys()) if x == action_name]
        if action_name:
            action_name = action_name[0]
        else:
            raise ValueError('Unknown action')
        if action_name in self.builtins:
            to = [-1]
            action = Action(action_name, timeout=0)
        else:
            action = [x for x in self.actions if x.name == action_name][0]
        command = Command(self, action, sender, to, args=args, excepts=excepts)
        self.handle_builtins(command)
        return command

    @abstractmethod
    def handle(self, command: Command):
        '''Aggregate all of the responses to the command and send them back if necessary'''
        pass
