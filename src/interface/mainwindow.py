
import sys
import json
from math import pi
from threading import Lock
from pathlib import Path
from queue import SimpleQueue, Empty as EmptyQueueException

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QGraphicsScene, QFileDialog, QMessageBox, QGraphicsPixmapItem,
    QTextBrowser, QGraphicsItemGroup
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, Qt

import pymunk

import anytree

# pylint: disable=relative-beyond-top-level

from .objectgraphicsitem import ObjectGraphicsItem
from .choosefromtreedialog import ChooseFromTreeDialog
from .conditiongraphicspixmapitem import ConditionGraphicsPixmapItem

from ..storage.fileinfo import FileInfo

from ..objectives.objective import createObjectiveTree

# pylint: enable=relative-beyond-top-level

# sys.path manipulation used to import nodetreeview.py from ui
sys.path.insert(0, str(Path(__file__).parent))

# imported here so it is not imported in a different path
from nodetreeview import NodeValue # pylint: disable=wrong-import-order
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
        self.__objects = []
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

        self.__ui.actionImportObject.triggered.connect(
            self.__importObjectAction)

        self.__ui.actionOpenScenario.triggered.connect(
            self.__openScenarioAction)

        self.__ui.actionOpenShip.triggered.connect(
            self.__openShipAction)

        self.__ui.actionOpenController.triggered.connect(
            self.__openControllerAction)

        self.__ui.actionOpenImage.triggered.connect(
            self.__openImageAction)

        self.__ui.actionOpenObject.triggered.connect(
            self.__openObjectAction)

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

        self.__comm_engine = None
        self.__debug_msg_queues = {}

        self.__debug_messages_text_browsers = {}
        self.__condition_graphic_items = []

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
        self.clear()
        self.__ui.view.setScene(None)

    def clear(self):

        self.setWindowTitle(self.__title_basename)

        self.__ui.deviceInterfaceComboBox.clear()
        self.__ui.deviceInterfaceComponents.show()
        self.__ui.treeView.show()

        with self.__lock:
            self.__space.remove(*self.__space.bodies, *self.__space.shapes)

            scene = self.__ui.view.scene()
            for _, gitem, widgets, _ in self.__ships:
                scene.removeItem(gitem)
                for widget in widgets:
                    widget.setParent(None)

            for _, gitem in self.__objects:
                scene.removeItem(gitem)

            self.__ships.clear()
            self.__objects.clear()
            self.__condition_graphic_items.clear()

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

    def __loadShip(self, ship_info, arg_scenario_info, fileinfo):

        arg_scenario_info['starting-position'] = ship_info.position

        json_info = json.dumps(arg_scenario_info)

        ship_model = ship_info.model
        ship_model_is_tuple = isinstance(ship_model, tuple)

        if ship_model_is_tuple or ship_model is None:
            if ship_model_is_tuple:
                ship_options = tuple(anytree.Node(model_option)
                                     for model_option in ship_model)
            else:
                ship_options = fileinfo.listShipsModelTree().children

            ship_model = self.__getOptionDialog('Choose ship model',
                                                ship_options)

            if ship_model is None:
                return None

            ship_model = '/'.join(ship_model)

        loaded_ship = fileinfo.loadShip(
            ship_model, ship_info.name, self.__space,
            communication_engine=self.__comm_engine)

        ship = loaded_ship.device

        self.__widgets = loaded_ship.widgets
        ship.body.position = ship_info.position
        ship.body.angle = ship_info.angle

        for widget in self.__widgets:
            widget.setParent(self.__ui.deviceInterfaceComponents)

        ship_controller = ship_info.controller

        if ship_controller is None:

            controller_options = fileinfo.listControllersTree().children
            ship_controller = self.__getOptionDialog('Choose controller',
                                                     controller_options)

            if ship_controller is None:
                return None

            ship_controller = '/'.join(ship_controller)

        msg_queue = SimpleQueue()
        thread = fileinfo.loadController(ship_controller, ship, json_info,
                                         msg_queue, self.__lock)

        self.__debug_msg_queues[ship.name] = msg_queue

        if loaded_ship.images:

            ship_gitem = QGraphicsItemGroup()

            for ship_image in loaded_ship.images:

                pixmap = QPixmap(fileinfo.dataImagePath(ship_image.name))
                height = ship_image.height
                width = ship_image.width

                if height is None:
                    if width is not None:
                        pixmap = pixmap.scaledToWidth(width)
                elif width is None:
                    pixmap = pixmap.scaledToheight(height)
                else:
                    pixmap = pixmap.scaled(width, height)

                if ship_image.condition is None:
                    ship_gitem_part = QGraphicsPixmapItem(pixmap)
                else:
                    ship_gitem_part = ConditionGraphicsPixmapItem(
                        ship_image.condition, pixmap,
                        names={'ship': ship.mirror})
                    self.__condition_graphic_items.append(ship_gitem_part)

                ship_gitem_part.setOffset(ship_image.x, ship_image.y)

                ship_gitem.addToGroup(ship_gitem_part)

        else:
            ship_gitem = ObjectGraphicsItem(ship.body.shapes)

        self.__ui.view.scene().addItem(ship_gitem)

        self.__ui.deviceInterfaceComboBox.addItem(
            f'{ship_info.name} ({ship_model})')

        thread.start()

        return ship, ship_gitem, self.__widgets, thread

    def __loadObject(self, obj_info, fileinfo):

        obj_model = obj_info.model
        if obj_model is None:
            options = fileinfo.listObjectsModelTree().children
            obj_model = self.__getOptionDialog('Choose object model',
                                               options)

            if obj_model is None:
                return None

            obj_model = '/'.join(obj_model)

        body, config = fileinfo.loadObject(obj_model, self.__space)

        body.position = obj_info.position
        body.angle = obj_info.angle

        if config.image is None:
            object_gitem = ObjectGraphicsItem(body.shapes, color=Qt.gray)
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

            object_gitem = QGraphicsPixmapItem(pixmap)

        self.__ui.view.scene().addItem(object_gitem)

        return body, object_gitem

    def __loadScenarioShips(self, ships_info, arg_scenario_info):

        ships = [None]*len(ships_info)
        for i, ship_info in enumerate(ships_info):
            try:
                ship = self.__loadShip(ship_info, arg_scenario_info.copy(),
                                       FileInfo())
            except Exception as err:
                self.clear()
                QMessageBox.warning(self, 'Error', (
                    f'An error occurred loading a ship({ship_info.model}): \n'
                    f'{type(err).__name__}: {err}'))
                return None

            if ship is None:
                self.clear()
                return None

            ships[i] = ship

        return ships

    def __loadScenarioObjects(self, objects_info):

        objects = [None]*len(objects_info)
        for i, obj_info in enumerate(objects_info):
            try:
                obj = self.__loadObject(obj_info, FileInfo())
            except Exception as err:
                self.clear()
                QMessageBox.warning(self, 'Error', (
                    f'An error occurred loading an object({obj_info.model}): \n'
                    f'{type(err).__name__}: {err}'))
                return None

            objects[i] = obj

        return objects

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
        self.__ui.debugMessagesTabWidget.setVisible(
            scenario_info.visible_debug_window)

        self.__comm_engine = scenario_info.communication_engine

        self.__scenario_objectives = scenario_info.objectives

        arg_scenario_info = {

            'objectives': [objective.toDict() for objective in
                           self.__scenario_objectives]
        }

        self.__debug_msg_queues.clear()

        ships = self.__loadScenarioShips(scenario_info.ships, arg_scenario_info)
        if ships is None:
            return

        objects = self.__loadScenarioObjects(scenario_info.objects)
        if objects is None:
            return

        self.__ships = ships
        self.__objects = objects

        self.__space.reindex_static()

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

        for image_info in scenario_info.static_images:
            pixmap = QPixmap(fileinfo.dataImagePath(image_info.name))
            height = image_info.height
            width = image_info.width

            if height is None:
                if width is not None:
                    pixmap = pixmap.scaledToWidth(width)
            elif width is None:
                pixmap = pixmap.scaledToHeight(height)
            else:
                pixmap = pixmap.scaled(width, height)

            image_item = QGraphicsPixmapItem(pixmap)

            image_item.setX(image_info.x)
            image_item.setY(image_info.y)

            self.__ui.view.scene().addItem(image_item)

        self.__current_scenario = scenario
        self.__ui.deviceInterfaceComboBox.setVisible(len(self.__ships) > 1)

        self.__ui.debugMessagesTabWidget.clear()
        self.__debug_messages_text_browsers.clear()
        for ship, _, _, _ in ships:
            tbrowser = QTextBrowser()
            self.__debug_messages_text_browsers[ship.name] = tbrowser
            self.__ui.debugMessagesTabWidget.addTab(tbrowser, ship.name)

    @staticmethod
    def __updateGraphicsItem(body, gitem):

        pos = body.position
        gitem.setX(pos.x)
        gitem.setY(pos.y)
        gitem.prepareGeometryChange()
        gitem.setRotation(180*body.angle/pi)

    def __timerTimeout(self):

        if self.__current_scenario is None:
            return

        ships = tuple(ship for ship, _, _, _ in self.__ships)
        with self.__lock:
            self.__space.step(0.02)
            for ship, gitem, _, _ in self.__ships:
                ship.act()
                self.__updateGraphicsItem(ship.body, gitem)

            for obj_body, gitem in self.__objects:
                self.__updateGraphicsItem(obj_body, gitem)

            self.__comm_engine.step()

            self.__objectives_complete = all(
                objective.verify(self.__space, ships)
                for objective in self.__scenario_objectives)

            for dyn_gitem in self.__condition_graphic_items:
                dyn_gitem.evaluate()

        for node_value in self.__objectives_node_value:
            node_value.update()

        for ship_name, queue in self.__debug_msg_queues.items():
            tbrowser = self.__debug_messages_text_browsers.get(ship_name)
            if tbrowser is None:
                continue

            try:
                while not queue.empty():
                    tbrowser.append(queue.get_nowait())
            except EmptyQueueException:
                pass

        self.__updateTitle()

    @staticmethod
    def __importScenarioAction():

        fdialog = QFileDialog(None, 'Scenario Import Dialog', '',
                              'TOML files(*.toml) ;; JSON files(*.json) ;;'
                              'YAML files(*.yml *.yaml)')
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addScenarios(fdialog.selectedFiles())

    @staticmethod
    def __importShipAction():

        fdialog = QFileDialog(None, 'Ship Import Dialog', '',
                              'TOML files(*.toml) ;; JSON files(*.json) ;;'
                              'YAML files(*.yml *.yaml)')
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
    def __importObjectAction():

        fdialog = QFileDialog(None, 'Object Import Dialog', '',
                              'TOML files(*.toml) ;; JSON files(*.json) ;;'
                              'YAML files(*.yml *.yaml)')
        fdialog.setFileMode(QFileDialog.ExistingFiles)

        if not fdialog.exec_():
            return

        FileInfo().addObjects(fdialog.selectedFiles())

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

    @staticmethod
    def __openObjectAction():

        object_model = MainWindow.__getOptionDialog(
            'Choose object model', FileInfo().listObjectsModelTree().children)

        if object_model is not None:
            FileInfo().openObjectModelFile('/'.join(object_model))
