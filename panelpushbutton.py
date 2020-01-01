
from PyQt5.QtWidgets import QPushButton

class PanelPushButton(QPushButton):

    def __init__(self):
        super().__init__()

        self.__was_pressed = False
        self.clicked.connect(self.setPressed)

    def setPressed(self):
        self.__was_pressed = True

    def getPressed(self, reset=True):
        pressed = self.__was_pressed
        if pressed and reset:
            self.__was_pressed = False

        return pressed
