
import sys
import json
from math import pi
from threading import Lock
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QFileDialog
from PyQt5.QtCore import QTimer

import pymunk

import anytree

# pylint: disable=relative-beyond-top-level

from .shipgraphicsitem import ShipGraphicsItem
from .choosefromtreedialog import ChooseFromTreeDialog

from ..storage.fileinfo import FileInfo

from ..objectives.objective import createObjectiveTree

# pylint: enable=relative-beyond-top-level

# sys.path manipulation used to import nodetreeview.py from ui
sys.path.insert(0, str(Path(__file__).parent))
UiMainWindow, _ = uic.loadUiType(FileInfo().uiFilePath('mainwindow.ui')) # pylint: disable=invalid-name
sys.path.pop(0)

class MainWindow(QMainWindow):

    def __init__(self, parent=None):

        super().__init__(parent=parent)

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

        self.__ships = []
        self.__scenario_objectives = []
        self.__objectives_complete = False
        self.__current_scenario = None

        self.__widgets = []

        self.__ui.actionLoadScenario.triggered.connect(
            self.__loadScenarioAction)

        self.__ui.actionImportScenario.triggered.connect(
            self.__importScenarioAction)

        self.__ui.actionImportShip.triggered.connect(
            self.__importShipAction)

        self.__ui.actionImportController.triggered.connect(
            self.__importControllerAction)

        self.__ui.actionImportPackage.triggered.connect(
            self.__importPackageAction)

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


    def closeEvent(self, _event):
        self.__ui.view.setScene(None)

    def clear(self):

        self.setWindowTitle(self.__title_basename)

        self.__ui.deviceInterfaceComponents.show()
        self.__ui.treeView.show()

        with self.__lock:
            self.__space.remove(self.__space.bodies, self.__space.shapes)
            for _, gitem, widgets, _ in self.__ships:
                self.__ui.view.scene().removeItem(gitem)
                for widget in widgets:
                    widget.setParent(None)

            self.__ships = []

        self.__current_scenario = None

    @staticmethod
    def __getOptionDialog(title, options):

        dialog = ChooseFromTreeDialog(options)
        dialog.setWindowTitle(title)

        return dialog.getOption()

    def __loadScenarioAction(self):

        scenario = self.__getOptionDialog(
            'Choose scenario', FileInfo().listScenariosTree().children)

        if scenario is not None:
            self.loadScenario('/'.join(scenario))

    def __loadShip(self, ship_info, json_info, fileinfo):

        ship_model = ship_info.model
        if ship_model is None:
            ship_options = fileinfo.listShipsModelTree().children
            ship_model = self.__getOptionDialog('Choose ship model',
                                                ship_options)

            if ship_model is None:
                return None

            ship_model = '/'.join(ship_model)

        ship, widgets = fileinfo.loadShip(ship_model, ship_info.name,
                                          self.__space)

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
                return None

            ship_controller = '/'.join(ship_controller)

        thread = fileinfo.loadController(ship_controller, ship, json_info,
                                         self.__lock)

        ship_gitem = ShipGraphicsItem(ship.body.shapes)
        self.__ui.view.scene().addItem(ship_gitem)

        thread.start()

        return ship, ship_gitem, widgets, thread

    def loadScenario(self, scenario):

        self.clear()

        fileinfo = FileInfo()

        scenario_info = fileinfo.loadScenario(scenario)

        self.__ui.deviceInterfaceComponents.setVisible(
            scenario_info.visible_user_interface)

        self.__scenario_objectives = scenario_info.objectives

        json_info = json.dumps({

            'objectives': [objective.toDict() for objective in
                           self.__scenario_objectives]
        })

        ships = [None]*len(scenario_info.ships)
        for i, ship_info in enumerate(scenario_info.ships):
            ship = self.__loadShip(ship_info, json_info, fileinfo)
            if ship is None:
                self.clear()
                return
            ships[i] = ship

        self.__ships = ships

        for widget in self.__ships[0][2]:
            widget.show()

        self.__current_scenario = scenario

        if self.__scenario_objectives:
            objectives_root_node = anytree.Node('root')
            for objective in self.__scenario_objectives:
                createObjectiveTree(objective, parent=objectives_root_node)

            for node in objectives_root_node.descendants:
                node.name = (node.name.name, node.name.description)

            self.__ui.treeView.clear()
            self.__ui.treeView.addNodes(objectives_root_node.children)
        else:
            self.__ui.treeView.hide()

    def __timerTimeout(self):

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

    @staticmethod
    def __importScenarioAction():

        fdialog = QFileDialog(None, 'Scenario Import Dialog', '',
                              'TOML files(*.toml) ;; JSON files(*.json)')
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addScenarios(fdialog.selectedFiles())

    @staticmethod
    def __importShipAction():

        fdialog = QFileDialog(None, 'Ship Import Dialog', '',
                              'TOML files(*.toml) ;; JSON files(*.json)')
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addShips(fdialog.selectedFiles())

    @staticmethod
    def __importControllerAction():

        fdialog = QFileDialog(None, 'Controller Import Dialog', '',
                              'executable files(*)')

        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addControllers(fdialog.selectedFiles())

    @staticmethod
    def __importPackageAction():

        fdialog = QFileDialog(None, 'Controller Import Dialog')

        fdialog.setFileMode(QFileDialog.DirectoryOnly)

        if not fdialog.exec_():
            return

        for package in fdialog.selectedFiles():
            FileInfo().addPackage(package)
