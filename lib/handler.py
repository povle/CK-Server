from command import Command
from types import Type

class Handler:
    def __init__(self, arg_types={}, answer_types={}):
        self.arg_types = arg_types
        self.answer_types = answer_types + {Type.ERROR, Type.OK}

    def parse(self, raw: dict) -> Command:
        '''Parse raw input'''
        pass

    def handle(self, command: Command):
        '''Aggregate all of the responses to the command and send them back if necessary'''
        pass
