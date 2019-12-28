from command import Command
from types import Type
from abc import ABC, abstractmethod

class Handler(ABC):
    def __init__(self, arg_types={}, answer_types={}):
        self.arg_types = arg_types
        self.answer_types = answer_types + {Type.ERROR, Type.OK}

    @abstractmethod
    def parse(self, raw: dict) -> Command:
        '''Parse raw input'''
        pass

    @abstractmethod
    def handle(self, command: Command):
        '''Aggregate all of the responses to the command and send them back if necessary'''
        pass
