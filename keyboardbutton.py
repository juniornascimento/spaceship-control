
from threading import Lock
from base64 import b64encode
from PyQt5.QtWidgets import QPushButton

class KeyboardButton(QPushButton):

    def __init__(self, can_delete_after=100):
        super().__init__('kb')

        super().clicked.connect(self.__clicked)

        self.__key_size = 10

        self.__focus = False
        self.__lock = Lock()
        self.__queue = bytearray()
        self.__can_delete_after = can_delete_after*self.__key_size

    def appendToQueue(self, val):
        with self.__lock:

            if len(val) != self.__key_size:
                raise ValueError('KeyboardButton internal error: '
                                 'wrong key size')

            if len(self.__queue) > 2*self.__can_delete_after:
                del self.__queue[0: self.__can_delete_after]

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
