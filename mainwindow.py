
from math import pi
from threading import Thread, Lock
from subprocess import Popen, PIPE

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene
from PyQt5.QtCore import QTimer

import pymunk

from shipgraphicsitem import ShipGraphicsItem
from shiploader import loadShip
from actionqueue import ActionQueue

UiMainWindow, _ = uic.loadUiType('mainwindow.ui')

class MainWindow(QMainWindow):

    def __init__(self, parent=None):

        QMainWindow.__init__(self, parent=parent)

        self.__ui = UiMainWindow()
        self.__ui.setupUi(self)

        self.__ui.view.setScene(QGraphicsScene(parent))

        self.__lock = Lock()

        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__timerTimeout)

        self.__timer.setInterval(100)
        self.__timer.start()

        self.__space = pymunk.Space()
        self.__space.gravity = (0, 0)
        self.__action_queue = ActionQueue()

        ship, widgets = loadShip('test/ship.toml', self.__space,
                                 self.__action_queue)

        self.__widgets = widgets

        for widget in widgets:
            widget.setParent(self.__ui.deviceInterfaceComponents)
            widget.show()

        ship.body.position = 300, 400

        ship_gitem = ShipGraphicsItem()
        self.__ui.view.scene().addItem(ship_gitem)
        self.__ships = [(ship, ship_gitem)]

        t = Thread(target=self.__startController, daemon=True,
                   args=(['/usr/bin/python3', 'test/child.py'],
                         ship, self.__lock))

        t.start()

    def __timerTimeout(self):

        self.__action_queue.processItems()

        with self.__lock:
            self.__space.step(0.02)
            for ship, gitem in self.__ships:
                ship.act()
                pos = ship.body.position
                gitem.setX(pos.x/10)
                gitem.setY(pos.y/10)
                gitem.prepareGeometryChange()
                gitem.setRotation(180*ship.body.angle/pi)

    def __startController(self, program, device, lock):

        process = Popen(program, stdin=PIPE,
                        stdout=PIPE)

        try:
            while process.poll() is None:
                question = process.stdout.readline().decode()

                if question and question[-1] == '\n':
                    question = question[:-1]

                with lock:
                    answer = device.communicate(question)

                process.stdin.write(answer.encode())
                process.stdin.write(b'\n')
                process.stdin.flush()

        except BrokenPipeError:
            pass

