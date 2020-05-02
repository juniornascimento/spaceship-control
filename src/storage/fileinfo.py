
import os
import shutil
from pathlib import Path
import subprocess
from enum import Enum
from collections import namedtuple

import json
import toml
import yaml

from PyQt5 import uic

from anytree import Node

from . import configfileinheritance, configfilevariables

from .loaders import (
    shiploader, scenarioloader, controllerloader, objectloader
)

from ..utils import dictutils

class FileInfo:

    __instance = None

    FileDataType = Enum('FileDataType', ('CONTROLLER', 'SHIPMODEL', 'SCENARIO',
                                         'OBJECTMODEL', 'IMAGE', 'UIDESIGN'))

    __DataTypeInfoType = namedtuple('DataTypeInfoType',
                                    ('path', 'use_dist_path', 'suffix_list',
                                     'list_remove_suffix', 'list_blacklist',
                                     'package_glob_list', 'files_mode'))

    __CONF_FILE_SUFFIX_LIST = ('.toml', '.json', '.yaml', '.yml')
    __CONF_FILE_GLOB_LIST = tuple(
        f'*{suffix}' for suffix in __CONF_FILE_SUFFIX_LIST)

    __DATA_TYPE_INFO = {
        FileDataType.CONTROLLER: __DataTypeInfoType(
            'controllers', False, None, False, ('__pycache__',), ('*',), 0o555),
        FileDataType.SHIPMODEL: __DataTypeInfoType(
            'ships', False, __CONF_FILE_SUFFIX_LIST, True, (),
            __CONF_FILE_GLOB_LIST, 0o644),
        FileDataType.SCENARIO: __DataTypeInfoType(
            'scenarios', False, __CONF_FILE_SUFFIX_LIST, True, (),
            __CONF_FILE_GLOB_LIST, 0o644),
        FileDataType.OBJECTMODEL: __DataTypeInfoType(
            'objects', False, __CONF_FILE_SUFFIX_LIST, True, (),
            __CONF_FILE_GLOB_LIST, 0o644),
        FileDataType.IMAGE: __DataTypeInfoType(
            'images', False, None, False, (),
            ('*.gif', '*.png'), 0o644),
        FileDataType.UIDESIGN: __DataTypeInfoType(
            'forms', True, ('.ui',), True, (), None, None)
    }

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

    def listFilesTree(self, filedatatype):

        filedatatype_info = self.__getFileDataTypeInfo(filedatatype)

        return self.__listTree(
            self.getPath(filedatatype),
            Node(filedatatype_info.path),
            remove_suffix=filedatatype_info.list_remove_suffix,
            blacklist=filedatatype_info.list_blacklist)

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

    def addScenarios(self, files):
        return self.addFiles(self.FileDataType.SCENARIO, files)

    def addShips(self, files):
        return self.addFiles(self.FileDataType.SHIPMODEL, files)

    def addControllers(self, files):
        return self.addFiles(self.FileDataType.CONTROLLER, files)

    def addObjects(self, files):
        return self.addFiles(self.FileDataType.OBJECTMODEL, files)

    def addImages(self, files):
        return self.addFiles(self.FileDataType.IMAGE, files)

    def addFiles(self, filedatatype, files):

        filedatatype_info = self.__getFileDataTypeInfo(filedatatype)

        if filedatatype_info.files_mode is None:
            raise ValueError('Can\'t add files to this FileDataType')

        return self.__addFiles(self.getPath(filedatatype), files,
                               mode=filedatatype_info.files_mode)

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

    def __findSuffix(self, basename, filedatatype, valid_suffixes):

        for valid_suffix in valid_suffixes:
            filepath = self.getPath(filedatatype, basename + valid_suffix)
            if filepath is not None:
                return filepath, valid_suffix

        return None, None

    def __getContent(self, basename, filedatatype, inexistent_message):

        filepath, suffix = self.__findSuffix(
            basename, filedatatype, ('.toml', '.json', '.yaml', '.yml'))

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

        content = self.__getContent(scenario_name, self.FileDataType.SCENARIO,
                                    'Inexistent scenario named \'{name}\'')

        dictutils.mergeMatch(content, (), ('Ship', 'ships'), 'Ship',
                             absolute=True)
        dictutils.mergeMatch(content, (), ('Objective', 'objectives'),
                             'Objective', absolute=True)

        configfilevariables.subVariables(content)

        return content

    def __getShipContent(self, ship_model, variables=None):

        content = self.__getContent(ship_model, self.FileDataType.SHIPMODEL,
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

        configfilevariables.subVariables(content, variables=variables)

        return content

    def __getObjectContent(self, object_model):

        content = self.__getContent(object_model, self.FileDataType.OBJECTMODEL,
                                    'Inexistent object model named \'{name}\'')

        dictutils.mergeMatch(content, (), ('Shape', 'shapes'), 'Shape',
                             absolute=True)
        dictutils.mergeMatch(content, ('Shape',), ('Point', 'points'), 'Point',
                             absolute=True)

        configfilevariables.subVariables(content)

        return content

    def loadUi(self, filename):
        return uic.loadUiType(
            self.getPath(self.FileDataType.UIDESIGN, filename))

    def loadScenario(self, scenario_name):

        prefixes = scenario_name.split('/')[:-1]

        scenario_content = self.__getScenarioContent(scenario_name)

        scenario_content = configfileinheritance.mergeInheritedFiles(
            scenario_content, self.__getScenarioContent, prefixes=prefixes)

        return scenarioloader.loadScenario(scenario_content, prefixes=prefixes)

    def loadShip(self, model, name, space, communication_engine=None,
                 variables=None):

        prefixes = model.split('/')[:-1]

        ship_content = self.__getShipContent(model, variables=variables)

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

    def loadController(self, controller_name, ship, json_info,
                       debug_queue, lock):
        return controllerloader.loadController(
            self.getPath(self.FileDataType.CONTROLLER, controller_name),
            ship, json_info, debug_queue, lock)

    def openFile(self, filedatatype, filename):

        filedatatype_info = self.__getFileDataTypeInfo(filedatatype)

        valid_suffixes = filedatatype_info.suffix_list

        if valid_suffixes is None:
            path = self.getPath(filedatatype, filename)
        else:
            path, _ = self.__findSuffix(filename, filedatatype, valid_suffixes)

        if path is not None:
            self.__openFile(path)

    @staticmethod
    def __openFile(path):
        subprocess.call(['xdg-open', path])

    @staticmethod
    def __addFiles(path, files, mode=0o644):
        path_str = str(path)
        for file in files:
            new_file = shutil.copy(file, path_str)
            os.chmod(new_file, mode)

    def getPath(self, filedatatype, name=None, to_string=True):

        if filedatatype is None:
            if to_string:
                return str(self.__path)
            return self.__path

        filedatatype_info = self.__getFileDataTypeInfo(filedatatype)

        if filedatatype_info.use_dist_path:
            basepath = self.__dist_data_path
        else:
            basepath = self.__path

        filepath = basepath.joinpath(filedatatype_info.path)

        if name is None:
            return filepath

        filepath = filepath.joinpath(name)

        if not(filepath.exists() and filepath.is_file()):
            return None

        if to_string:
            return str(filepath)
        return filepath

    @staticmethod
    def __getFileDataTypeInfo(filedatatype):

        info = FileInfo.__DATA_TYPE_INFO.get(filedatatype)

        if info is None:
            raise ValueError(f'Invalid file data type')

        return info
