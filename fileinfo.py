
import os
from pathlib import Path

class FileInfo:

    __instance = None

    def __init__(self):
        self.__path = \
            Path.home().joinpath('.local/share/spaceshipcontrol').resolve()
        self.__dist_data_path = Path(__file__).parent.resolve()

        self.__path.mkdir(parents=True, exist_ok=True)

        create_n_link_example_dirs = ['controllers', 'ships']

        dist_data_examples_path = self.__dist_data_path.joinpath('examples')
        for dirname in create_n_link_example_dirs:
            path = self.__path.joinpath(dirname)
            path.mkdir(exist_ok=True)

            example_dir_path = path.joinpath('examples')
            if not example_dir_path.exists():
                os.symlink(dist_data_examples_path.joinpath(dirname),
                           example_dir_path)

    def __new__(cls):
        if FileInfo.__instance is None:
            FileInfo.__instance = super().__new__(cls)

        return FileInfo.__instance

    def shipModelPath(self, name=None):
        ships_path = self.__path.joinpath('ships')
        if name is None:
            return ships_path

        ship = ships_path.joinpath(name)

        if not(ship.exists() and ship.is_file()):
            return None

        return ship
