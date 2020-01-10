
from threading import Lock
from base64 import b64encode
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

    def getAll(self):
        with self.__lock:
            content = self.__queue.decode('utf-8')
            self.__queue.clear()

        return content

    def keyPressEvent(self, event):
        self.appendToQueue('{:02x}{:08x}'.format(int(event.modifiers()) >> 24,
                                                 event.key()))

    def focusOutEvent(self, _event):
        self.__focus = False

    def __clicked(self):
        if self.__focus:
            self.clearFocus()
        else:
            self.setFocus()
            self.__focus = True
