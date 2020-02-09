
import sys
import json
from math import pi
from threading import Lock
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QGraphicsScene, QFileDialog, QMessageBox, QGraphicsPixmapItem
)
from PyQt5.QtGui import QPixmap
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

# imported here so it is not imported in a different path
from nodetreeview import NodeValue
UiMainWindow, _ = uic.loadUiType(FileInfo().uiFilePath('mainwindow.ui')) # pylint: disable=invalid-name
sys.path.pop(0)

class ObjectiveNodeValue(NodeValue):

    def __init__(self, objective):
        super().__init__(f'✗ {objective.name}', objective.description)

        self.__objective = objective

    def update(self):
        symbol = '✓' if self.__objective.accomplished() else '✗'
        self.name = f'{symbol} {self.__objective.name}'

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
        self.__objectives_node_value = []

        self.__ui.actionLoadScenario.triggered.connect(
            self.__loadScenarioAction)

        self.__ui.actionImportScenario.triggered.connect(
            self.__importScenarioAction)

        self.__ui.actionImportShip.triggered.connect(
            self.__importShipAction)

        self.__ui.actionImportController.triggered.connect(
            self.__importControllerAction)

        self.__ui.actionImportImage.triggered.connect(
            self.__importImageAction)

        self.__ui.actionOpenScenario.triggered.connect(
            self.__openScenarioAction)

        self.__ui.actionOpenShip.triggered.connect(
            self.__openShipAction)

        self.__ui.actionOpenController.triggered.connect(
            self.__openControllerAction)

        self.__ui.actionOpenImage.triggered.connect(
            self.__openImageAction)

        self.__ui.actionImportPackage.triggered.connect(
            self.__importPackageAction)

        self.__ui.deviceInterfaceComboBox.currentIndexChanged.connect(
            self.__deviceInterfaceComboBoxIndexChange)

        self.__title_basename = 'Spaceship Control'

        view_geometry = self.__ui.view.geometry()
        view_geometry.setWidth(self.geometry().width()//2)
        self.__ui.view.setGeometry(view_geometry)
        self.__updateTitle()

        self.__current_ship_widgets_index = 0

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

        self.__ui.deviceInterfaceComboBox.clear()
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
        self.__current_ship_widgets_index = 0
        self.__updateTitle()

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

        ship, config, widgets = fileinfo.loadShip(ship_model, ship_info.name,
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

        if config.image is None:
            ship_gitem = ShipGraphicsItem(ship.body.shapes)
        else:
            pixmap = QPixmap(fileinfo.dataImagePath(config.image.name))
            height = config.image.height
            width = config.image.width

            if height is None:
                if width is not None:
                    pixmap = pixmap.scaledToWidth(width)
            elif width is None:
                pixmap = pixmap.scaledToheight(height)
            else:
                pixmap = pixmap.scaled(width, height)

            ship_gitem = QGraphicsPixmapItem(pixmap)
        self.__ui.view.scene().addItem(ship_gitem)

        self.__ui.deviceInterfaceComboBox.addItem(
            f'{ship_info.name} ({ship_model})')

        thread.start()

        return ship, ship_gitem, widgets, thread

    def loadScenario(self, scenario):

        self.clear()

        fileinfo = FileInfo()

        try:
            scenario_info = fileinfo.loadScenario(scenario)
        except Exception as err:
            QMessageBox.warning(self, 'Error', (
                'An error occurred loading the scenario: \n'
                f'{type(err).__name__}: {err}'))
            return

        self.__ui.deviceInterfaceWidgets.setVisible(
            scenario_info.visible_user_interface)

        self.__scenario_objectives = scenario_info.objectives

        json_info = json.dumps({

            'objectives': [objective.toDict() for objective in
                           self.__scenario_objectives]
        })

        ships = [None]*len(scenario_info.ships)
        for i, ship_info in enumerate(scenario_info.ships):
            try:
                ship = self.__loadShip(ship_info, json_info, fileinfo)
            except Exception as err:
                self.clear()
                QMessageBox.warning(self, 'Error', (
                    f'An error occurred loading a ship({ship_info.model}): \n'
                    f'{type(err).__name__}: {err}'))
                return

            if ship is None:
                self.clear()
                return
            ships[i] = ship

        self.__ships = ships

        for widget in self.__ships[0][2]:
            widget.show()

        self.__objectives_node_value = []
        if self.__scenario_objectives:
            objectives_root_node = anytree.Node('root')
            for objective in self.__scenario_objectives:
                createObjectiveTree(objective, parent=objectives_root_node)

            for node in objectives_root_node.descendants:
                node_value = ObjectiveNodeValue(node.name)
                node.name = node_value
                self.__objectives_node_value.append(node_value)

            self.__ui.treeView.clear()
            self.__ui.treeView.addNodes(objectives_root_node.children)
        else:
            self.__ui.treeView.hide()

        self.__current_scenario = scenario
        self.__ui.deviceInterfaceComboBox.setVisible(len(self.__ships) > 1)

    def __timerTimeout(self):

        if self.__current_scenario is None:
            return

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

        for node_value in self.__objectives_node_value:
            node_value.update()

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
    def __importImageAction():

        fdialog = QFileDialog(None, 'Image Import Dialog', '',
                              'image files(*.png *.gif)')

        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addImages(fdialog.selectedFiles())

    @staticmethod
    def __importPackageAction():

        fdialog = QFileDialog(None, 'Controller Import Dialog')

        fdialog.setFileMode(QFileDialog.DirectoryOnly)

        if not fdialog.exec_():
            return

        for package in fdialog.selectedFiles():
            FileInfo().addPackage(package)

    def __deviceInterfaceComboBoxIndexChange(self, cur_index):

        if cur_index == -1 or cur_index >= len(self.__ships):
            return

        for widget in self.__ships[self.__current_ship_widgets_index][2]:
            widget.hide()

        for widget in self.__ships[cur_index][2]:
            widget.show()

        self.__current_ship_widgets_index = cur_index

    @staticmethod
    def __openScenarioAction():

        scenario = MainWindow.__getOptionDialog(
            'Choose scenario', FileInfo().listScenariosTree().children)

        if scenario is not None:
            FileInfo().openScenarioFile('/'.join(scenario))

    @staticmethod
    def __openShipAction():

        ship = MainWindow.__getOptionDialog(
            'Choose ship model', FileInfo().listShipsModelTree().children)

        if ship is not None:
            FileInfo().openShipModelFile('/'.join(ship))

    @staticmethod
    def __openControllerAction():

        controller = MainWindow.__getOptionDialog(
            'Choose controller', FileInfo().listControllersTree().children)

        if controller is not None:
            FileInfo().openControllerFile('/'.join(controller))

    @staticmethod
    def __openImageAction():

        image = MainWindow.__getOptionDialog(
            'Choose image', FileInfo().listImagesTree().children)

        if image is not None:
            FileInfo().openImageFile('/'.join(image))
