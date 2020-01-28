
import os
import signal
from math import pi
from threading import Lock

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QFileDialog, QLabel
from PyQt5.QtCore import QTimer, QDir

import pymunk

from .shipgraphicsitem import ShipGraphicsItem
from .choosefromtreedialog import ChooseFromTreeDialog

from ..utils.fileinfo import FileInfo
from ..utils.actionqueue import ActionQueue

UiMainWindow, _ = uic.loadUiType(FileInfo().uiFilePath('mainwindow.ui'))

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

        self.__ships = []
        self.__scenario_objectives = []
        self.__objectives_complete = False
        self.__current_scenario = None

        self.__ui.actionLoadScenario.triggered.connect(
            self.__loadScenarioAction)

        self.__ui.actionImportScenario.triggered.connect(
            self.__importScenarioAction)

        self.__ui.actionImportShip.triggered.connect(
            self.__importShipAction)

        self.__ui.actionImportController.triggered.connect(
            self.__importControllerAction)

        self.__title_basename = 'Spaceship Control'

        self.__updateTitle()

    def __updateTitle(self):

        if self.__current_scenario is None:
            self.setWindowTitle(self.__title_basename)
        else:
            if not self.__scenario_objectives:
                suffix = ''
            elif self.__objectives_complete:
                suffix = ' ✓'
            else:
                suffix = ' ✗'

            self.setWindowTitle(
                f'{self.__title_basename}({self.__current_scenario}){suffix}')


    def closeEvent(self, event):
        self.__ui.view.setScene(None)

    def clear(self):

        self.setWindowTitle(self.__title_basename)

        self.__ui.deviceInterfaceComponents.show()

        with self.__lock:
            self.__space.remove(self.__space.bodies, self.__space.shapes)
            for ship, gitem, widgets, _ in self.__ships:
                self.__ui.view.scene().removeItem(gitem)
                for widget in widgets:
                    widget.setParent(None)

            self.__ships = []

        self.__current_scenario = None

    def __getOptionDialog(self, title, options):

        dialog = ChooseFromTreeDialog(options)
        dialog.setWindowTitle(title)

        return dialog.getOption()

    def __loadScenarioAction(self):

        scenario = self.__getOptionDialog(
            'Choose scenario', FileInfo().listScenariosTree().children)

        if scenario is not None:
            self.loadScenario('/'.join(scenario))

    def loadScenario(self, scenario):

        self.clear()

        fileinfo = FileInfo()

        scenario_info = fileinfo.loadScenario(scenario)

        self.__ui.deviceInterfaceComponents.setVisible(
            scenario_info.visible_user_interface)

        ships = [None]*len(scenario_info.ships)
        self.__scenario_objectives = scenario_info.objectives
        for i, ship_info in enumerate(scenario_info.ships):

            ship_model = ship_info.model
            if ship_model is None:
                ship_options = fileinfo.listShipsModelTree().children
                ship_model = self.__getOptionDialog('Choose ship model',
                                                    ship_options)

                if ship_model is None:
                    self.clear()
                    return

                ship_model = '/'.join(ship_model)

            ship, widgets = fileinfo.loadShip(ship_model, ship_info.name,
                                              self.__space, self.__action_queue)

            self.__widgets = widgets
            ship.body.position = ship_info.position
            ship.body.angle = ship_info.angle

            for widget in widgets:
                widget.setParent(self.__ui.deviceInterfaceComponents)

            ship_controller = ship_info.controller

            if ship_controller is None:

                controller_options = fileinfo.listControllersTree().children
                ship_controller = self.__getOptionDialog('Choose controller',
                                                         controller_options)

                if ship_controller is None:
                    self.clear()
                    return

                ship_controller = '/'.join(ship_controller)

            thread = fileinfo.loadController(ship_controller, ship, self.__lock)

            ship_gitem = ShipGraphicsItem(ship.body.shapes)
            self.__ui.view.scene().addItem(ship_gitem)
            ships[i] = (ship, ship_gitem, widgets, thread)

            thread.start()

        self.__ships = ships

        for widget in self.__ships[0][2]:
            widget.show()

        self.__current_scenario = scenario

    def __timerTimeout(self):

        self.__action_queue.processItems()

        ships = tuple(ship for ship, _, _, _ in self.__ships)
        with self.__lock:
            self.__space.step(0.02)
            for ship, gitem, _, _ in self.__ships:
                ship.act()
                pos = ship.body.position
                gitem.setX(pos.x)
                gitem.setY(pos.y)
                gitem.prepareGeometryChange()
                gitem.setRotation(180*ship.body.angle/pi)
            self.__objectives_complete = all(
                objective.verify(self.__space, ships)
                for objective in self.__scenario_objectives)

        self.__updateTitle()

    def __importScenarioAction(self):

        fdialog = QFileDialog(None, 'Scenario Import Dialog', '',
                              'TOML files(*.toml)')
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addScenarios(fdialog.selectedFiles())

    def __importShipAction(self):

        fdialog = QFileDialog(None, 'Ship Import Dialog', '',
                              'TOML files(*.toml)')
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addShips(fdialog.selectedFiles())

    def __importControllerAction(self):

        fdialog = QFileDialog(None, 'Controller Import Dialog', '',
                              'executable files(*)')

        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addControllers(fdialog.selectedFiles())
