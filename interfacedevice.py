
from PyQt5.QtGui import QFontMetricsF, QTextCursor
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

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

class ConsoleDevice(InterfaceDevice):

    def __init__(self, text: 'QTextBrowser', action_queue: 'ActionQueue',
                 columns: int, rows: int, **kwargs: 'Any') -> None:
        super().__init__(device_type='text-display', **kwargs)

        self.__text = text
        self.__queue = action_queue
        self.__col = 0
        self.__row = 0

        text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        text.setFocusPolicy(Qt.NoFocus)

        text.setPlainText('A'*(rows*columns - 1))

        tdoc = text.document()
        fmetrics = QFontMetricsF(tdoc.defaultFont())
        margins = text.contentsMargins()

        height = fmetrics.lineSpacing()*rows + \
            2*(tdoc.documentMargin() + text.frameWidth()) + \
                margins.top() + margins.bottom()


        width = fmetrics.width('A')*columns + \
            2*(tdoc.documentMargin() + text.frameWidth()) + \
                margins.left() + margins.right()

        text.setFixedHeight(height)
        text.setFixedWidth(width)

        text.setMaximumBlockCount(rows)

    def command(self, command: 'List[str]') -> 'Any':
        return super().command(command, ConsoleDevice.__COMMANDS)

    def __setPos(self, column, row):
        self.__col = column
        self.__row = row

        return '<<ok>>'

    def __getPos(self):
        return f'{self.__col}-{self.__row}'

    def __newline(self):
        self.__row += 1

    def __columndec(self):
        self.__col -= 1

    def __columnstart(self):
        self.__col = 0

    def __write(self, text):
        pass

    def __update(self):
        pass

    __COMMANDS = {

        'write': __write,
        'set-position': __setPos,
        'get-position': __getPos,
        'LF': __newline,
        'BS': __columndec,
        'CR': __columnstart,
        'update': __update
    }
