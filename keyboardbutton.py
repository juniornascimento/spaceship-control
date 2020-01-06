
from threading import Lock
from PyQt5.QtWidgets import QPushButton

class KeyboardButton(QPushButton):

    def __init__(self):
        super().__init__('kb')

        super().clicked.connect(self.__clicked)
        self.__focus = False
        self.__lock = Lock()
        self.__queue = bytearray()

    def appendToQueue(self, val):
        with self.__lock:
            self.__queue.extend(val.encode('utf-8'))

    def keyPressEvent(self, event):
        self.appendToQueue('{:08x}'.format(event.key()))

    def focusOutEvent(self, _event):
        self.__focus = False

    def __clicked(self):
        if self.__focus:
            self.clearFocus()
        else:
            self.setFocus()
            self.__focus = True
