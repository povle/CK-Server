from enum import Enum

class Type(Enum):
    EXCEPTION = -1
    ERROR = 0
    OK = 1
    TEXT = 2
    PHOTO = 3
    DOCUMENT = 4
    VK_KEYBOARD = 5
