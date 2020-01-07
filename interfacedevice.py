
from PyQt5.QtWidgets import QLabel

from panelpushbutton import PanelPushButton
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
        super().__init__(device_type='text-display', **kwargs)

        self.__label = label
        self.__queue = action_queue

    def command(self, command: 'List[str]') -> 'Any':
        return super().command(command, TextDisplayDevice.__COMMANDS)

    def setText(self, text: str) -> None:
        self.__queue.add(Action(QLabel.setText, self.__label, text))

    __COMMANDS = {

        'set-text': setText
    }

class ButtonDevice(InterfaceDevice):

    def __init__(self, button: 'PanelPushButton', **kwargs: 'Any') -> None:
        super().__init__(device_type='button', **kwargs)

        self.__button = button

    def command(self, command: 'List[str]') -> 'Any':
        return super().command(command, ButtonDevice.__COMMANDS)

    def __clicked(self) -> None:
        return '1' if self.__button.getPressed() else '0'

    __COMMANDS = {

        'clicked': __clicked
    }

class KeyboardReceiverDevice(InterfaceDevice):

    def __init__(self, kb_receiver: 'KeyboardButton', **kwargs: 'Any') -> None:
        super().__init__(device_type='keyboard', **kwargs)

        self.__receiver = kb_receiver

    def command(self, command: 'List[str]') -> 'Any':
        return super().command(command, KeyboardReceiverDevice.__COMMANDS)

    def __get(self) -> None:
        return self.__receiver.getAll()

    __COMMANDS = {

        'get': __get
    }
