from .command import Command
from .types import Type
from abc import ABC, abstractmethod
from .actions import actions
import time
from . import builtinc

class Handler(ABC):
    def __init__(self, arg_types=set(), answer_types=set()):
        self.arg_types = arg_types
        self.answer_types = answer_types
        self.answer_types.update({Type.ERROR, Type.OK})
        self.builtins = [x for x in builtinc.builtin_actions
                         if x.arg_types.issubset(self.arg_types)
                         and x.answer_types.issubset(self.answer_types)]
        self.actions = [x for x in actions
                        if x.arg_types.issubset(self.arg_types)
                        and x.answer_types.issubset(self.answer_types)]
        self.error_action = builtinc.error_action

    def handle_builtins(self, command):
        for action in self.builtins + [self.error_action]:
            if command.action is action:
                response = action.execute(command.args)
                ans = {'comp_id': '0.0',
                       'command_id': command.id,
                       'timestamp': time.time(),
                       }
                ans.update(response)
                command.add_answer('0.0', ans)
                return True
        return False

    @abstractmethod
    def initial_parse(self, raw: dict) -> dict:
        pass

    def parse(self, raw: dict) -> Command:
        '''Parse raw input'''
        try:
            parsed = self.initial_parse(raw)
            action_name = parsed['action']
            room = parsed['room']
            ids = parsed['ids']
            args = parsed['args']
            excepts = parsed.get('excepts', [])
            for act in self.actions:
                if act.name == action_name:
                    action = act
                    break
            else:
                room = '0'
                ids = ['0']
                excepts = []
                for act in self.builtins:
                    if act.name == action_name:
                        action = act
                        break
                else:
                    raise ValueError('Unknown action')
        except Exception as e:
            action = self.error_action
            args = [{'type': 'exception',
                     'exception': e}]
            ids = ['0']
            room = '0'
            excepts = []
        command = Command(self, action=action, sender=self.get_sender(raw), ids=ids, room=room, args=args, excepts=excepts)
        self.handle_builtins(command)
        return command

    @abstractmethod
    def get_sender(self, raw: dict):
        pass

    @abstractmethod
    def handle(self, command: Command):
        '''Aggregate all of the responses to the command and send them back if necessary'''
        pass

    @abstractmethod
    def handle_late(self, command: Command, cid: str):
        '''Send one answer separately'''
        pass
