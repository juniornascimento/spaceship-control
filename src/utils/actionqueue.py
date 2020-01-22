
from threading import Lock

class Action:

    def __init__(self, function, *args):

        self.function = function
        self.args = args

class ActionQueue:

    def __init__(self):
        self.__list = []
        self.__lock = Lock()

    def add(self, action: Action):
        with self.__lock:
            self.__list.append(action)

    def processItems(self):
        with self.__lock:
            for action in self.__list:
                action.function(*action.args)
