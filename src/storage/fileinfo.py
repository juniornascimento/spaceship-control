
import os
import shutil
from pathlib import Path
import subprocess

import json
import toml
import yaml

from anytree import Node

from . import configfileinheritance, configfilevariables

from .loaders import (
    shiploader, scenarioloader, controllerloader, objectloader
)

from ..utils import dictutils

class FileInfo:

    __instance = None

    def __init__(self):
        self.__path = \
            Path.home().joinpath('.local/share/spaceshipcontrol').resolve()
        self.__dist_data_path = Path(__file__).parent.parent.resolve()

        if self.__dist_data_path.name == 'src':
            self.__dist_data_path = self.__dist_data_path.parent

        self.__path.mkdir(parents=True, exist_ok=True)

        create_n_link_example_dirs = ['controllers', 'ships', 'scenarios',
                                      'objects', 'images']

        dist_data_examples_path = self.__dist_data_path.joinpath('examples')

        for dirname in create_n_link_example_dirs:
            path = self.__path.joinpath(dirname)
            path.mkdir(exist_ok=True)

            example_dir_path = path.joinpath('examples')
            try:
                os.unlink(example_dir_path)
            except FileNotFoundError:
                pass
            os.symlink(dist_data_examples_path.joinpath(dirname),
                       example_dir_path)

    def __new__(cls):
        if FileInfo.__instance is None:
            FileInfo.__instance = super().__new__(cls)

        return FileInfo.__instance

    def listShipsModelTree(self):
        return self.__listTree(self.__path.joinpath('ships'), Node('ships'))

    def listScenariosTree(self):
        return self.__listTree(self.__path.joinpath('scenarios'),
                               Node('scenarios'))

    def listControllersTree(self):
        return self.__listTree(self.__path.joinpath('controllers'),
                               Node('controllers'), blacklist=('__pycache__',),
                               remove_suffix=False)

    def listImagesTree(self):
        return self.__listTree(self.__path.joinpath('images'),
                               Node('images'), remove_suffix=False)

    def listObjectsModelTree(self):
        return self.__listTree(self.__path.joinpath('objects'), Node('objects'))

    def __listTree(self, base_path, current_node, blacklist=(),
                   remove_suffix=True):

        for path in sorted(base_path.iterdir()):

            if path.name in blacklist:
                continue

            if remove_suffix is True:
                path = path.with_suffix('')

            new_node = Node(path.name, parent=current_node)
            if path.is_dir():
                self.__listTree(path, new_node, blacklist=blacklist,
                                remove_suffix=remove_suffix)

        return current_node

    def uiFilePath(self, *args, **kwargs):
        return self.__getPath(self.__dist_data_path.joinpath('forms'), *args,
                              **kwargs)

    def shipModelPath(self, *args, **kwargs):
        return self.__getPath(self.__path.joinpath('ships'), *args, **kwargs)

    def controllerPath(self, *args, **kwargs):
        return self.__getPath(
            self.__path.joinpath('controllers'), *args, **kwargs)

    def imagePath(self, *args, **kwargs):
        return self.__getPath(
            self.__path.joinpath('images'), *args, **kwargs)

    def scenarioPath(self, *args, **kwargs):
        return self.__getPath(
            self.__path.joinpath('scenarios'), *args, **kwargs)

    def objectModelPath(self, *args, **kwargs):
        return self.__getPath(
            self.__path.joinpath('objects'), *args, **kwargs)

    def dataImagePath(self, *args, **kwargs):
        return self.__getPath(
            self.__path.joinpath('images'), *args, **kwargs)

    def addScenarios(self, files):
        return self.__addFiles(self.__path.joinpath('scenarios'), files)

    def addShips(self, files):
        return self.__addFiles(self.__path.joinpath('ships'), files)

    def addControllers(self, files):
        return self.__addFiles(self.__path.joinpath('controllers'), files,
                               mode=0o555)

    def addObjects(self, files):
        return self.__addFiles(self.__path.joinpath('objects'), files)

    def addImages(self, files):
        return self.__addFiles(self.__path.joinpath('images'), files)

    def addPackage(self, package_pathname):

        package_path = Path(package_pathname)

        package_name = package_path.name

        for directory, mode, patterns in (
                ('scenarios', 0o644, ('*.toml', '*.json', '*.yml', '*.yaml')),
                ('ships', 0o644, ('*.toml', '*.json', '*.yml', '*.yaml')),
                ('objects', 0o644, ('*.toml', '*.json', '*.yml', '*.yaml')),
                ('controllers', 0o555, ('*',)),
                ('images', 0o644, ('*.png', '*.gif'))):

            dest_base_path = self.__path.joinpath(directory).joinpath(
                package_name)
            package_subdir_path = package_path.joinpath(directory)

            for pat in patterns:
                for path in package_subdir_path.rglob(pat):
                    if path.is_file():

                        dest_path = dest_base_path.joinpath(
                            path.parent.relative_to(package_subdir_path))

                        if not dest_path.exists():
                            dest_path.mkdir(parents=True)

                        self.__addFiles(dest_path, (path,), mode=mode)

    @staticmethod
    def __findSuffix(basename, get_path, valid_suffixes):

        for valid_suffix in valid_suffixes:
            filepath = get_path(basename + valid_suffix)
            if filepath is not None:
                return filepath, valid_suffix

        return None, None

    @staticmethod
    def __getContent(basename, get_path, inexistent_message):

        filepath, suffix = FileInfo.__findSuffix(
            basename, get_path, ('.toml', '.json', '.yaml', '.yml'))

        if filepath is None:
            raise Exception(inexistent_message.format(name=basename))

        if suffix == '.json':
            with open(filepath) as file:
                return json.load(file)

        if suffix in ('.yaml', '.yml'):
            with open(filepath) as file:
                return yaml.safe_load(file)

        return toml.load(filepath)

    def __getScenarioContent(self, scenario_name):

        content = self.__getContent(scenario_name, self.scenarioPath,
                                    'Inexistent scenario named \'{name}\'')

        dictutils.mergeMatch(content, (), ('Ship', 'ships'), 'Ship',
                             absolute=True)
        dictutils.mergeMatch(content, (), ('Objective', 'objectives'),
                             'Objective', absolute=True)

        configfilevariables.subVariables(content)

        return content

    def __getShipContent(self, ship_model):

        content = self.__getContent(ship_model, self.shipModelPath,
                                    'Inexistent ship model named \'{name}\'')

        dictutils.mergeMatch(content, (), ('Shape', 'shapes'), 'Shape',
                             absolute=True)
        dictutils.mergeMatch(content, (), ('Actuator', 'actuators'), 'Actuator',
                             absolute=True)
        dictutils.mergeMatch(content, (), ('Sensor', 'sensors'), 'Sensor',
                             absolute=True)
        dictutils.mergeMatch(content, (),
                             ('InterfaceDevice', 'interface_devices'),
                             'InterfaceDevice',
                             absolute=True)
        dictutils.mergeMatch(content, ('Shape',), ('Point', 'points'), 'Point',
                             absolute=True)

        configfilevariables.subVariables(content)

        return content

    def __getObjectContent(self, object_model):

        content = self.__getContent(object_model, self.objectModelPath,
                                    'Inexistent object model named \'{name}\'')

        dictutils.mergeMatch(content, (), ('Shape', 'shapes'), 'Shape',
                             absolute=True)
        dictutils.mergeMatch(content, ('Shape',), ('Point', 'points'), 'Point',
                             absolute=True)

        configfilevariables.subVariables(content)

        return content

    def loadScenario(self, scenario_name):

        prefixes = scenario_name.split('/')[:-1]

        scenario_content = self.__getScenarioContent(scenario_name)

        scenario_content = configfileinheritance.mergeInheritedFiles(
            scenario_content, self.__getScenarioContent, prefixes=prefixes)

        return scenarioloader.loadScenario(scenario_content, prefixes=prefixes)

    def loadShip(self, model, name, space, communication_engine=None):

        prefixes = model.split('/')[:-1]

        ship_content = self.__getShipContent(model)

        ship_content = configfileinheritance.mergeInheritedFiles(
            ship_content, self.__getShipContent, prefixes=prefixes)

        return shiploader.loadShip(ship_content, name, space, prefixes=prefixes,
                                   communication_engine=communication_engine)

    def loadObject(self, model, space):

        prefixes = model.split('/')[:-1]

        obj_content = self.__getObjectContent(model)

        obj_content = configfileinheritance.mergeInheritedFiles(
            obj_content, self.__getObjectContent, prefixes=prefixes)

        return objectloader.loadObject(obj_content, space, prefixes=prefixes)

    def loadController(self, controller_name, ship, json_info, lock):
        return controllerloader.loadController(
            self.controllerPath(controller_name), ship, json_info, lock)

    def openScenarioFile(self, scenario):

        scenario_path, _ = self.__findSuffix(
            scenario, self.scenarioPath, ('.toml', '.json', '.yaml', '.yml'))

        if scenario_path is not None:
            self.__openFile(scenario_path)

    def openShipModelFile(self, ship_model):

        model_path, _ = self.__findSuffix(
            ship_model, self.shipModelPath, ('.toml', '.json', '.yaml', '.yml'))

        if model_path is not None:
            self.__openFile(model_path)

    def openObjectModelFile(self, obj_model):

        model_path, _ = self.__findSuffix(obj_model, self.objectModelPath,
                                          ('.toml', '.json', '.yaml', '.yml'))

        if model_path is not None:
            self.__openFile(model_path)

    def openControllerFile(self, controller):

        controller_path = self.controllerPath(controller)

        if controller_path is not None:
            self.__openFile(controller_path)

    def openImageFile(self, image):

        image_path = self.imagePath(image)

        if image_path is not None:
            self.__openFile(image_path)

    @staticmethod
    def __openFile(path):
        subprocess.call(['xdg-open', path])

    def __addFiles(self, path, files, mode=0o644):
        path_str = str(path)
        for file in files:
            new_file = shutil.copy(file, path_str)
            os.chmod(new_file, mode)

    @staticmethod
    def __getPath(basepath, name=None, to_string=True):

        if name is None:
            if to_string:
                return str(basepath)
            return basepath

        file_path = basepath.joinpath(name)

        if not(file_path.exists() and file_path.is_file()):
            return None

        if to_string:
            return str(file_path)
        return file_path
