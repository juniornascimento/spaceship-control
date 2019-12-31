
from PyQt5.QtWidgets import QLabel

from actionqueue import Action
from device import DefaultDevice

class InterfaceDevice(DefaultDevice):

    def __init__(self, **kwargs: 'Any') -> None:
        super().__init__(**kwargs)

    def act(self):
        pass

class TextDisplayDevice(InterfaceDevice):

    def __init__(self, label: 'QLabel', action_queue: 'ActionQueue',
                 **kwargs: 'Any') -> None:
        super().__init__(device_type='x-position-sensor', **kwargs)

        self.__label = label
        self.__queue = action_queue

    def command(self, command: 'List[str]') -> 'Any':
        return super().command(command, TextDisplayDevice.__COMMANDS)

    def setText(self, text: str) -> None:
        self.__queue.add(Action(QLabel.setText, self.__label, text))

    __COMMANDS = {

        'set-text': setText
    }
