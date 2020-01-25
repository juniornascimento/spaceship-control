
from abc import ABC, abstractmethod

class Objective(ABC):

    def __init__(self, name: str, description: str) -> None:
        super().__init__()

        self.__name = name
        self.__desc = description

    @property
    def description(self) -> str:
        return self.__desc

    @property
    def name(self) -> str:
        return self.__name

    @abstractmethod
    def accomplished(self, space: 'pymunk.Space',
                     ships: 'Sequence[Device]') -> bool:
        pass

class ObjectiveGroup(ABC):

    def __init__(self, subobjectives: 'Sequence[Objective]',
                 name: str = 'Objectives list',
                 description: str = None) -> None:
        super().__init__(name, description)

        self.__subobjectives = tuple(subobjectives)

    @property
    def subobjectives(self):
        return self.__subobjectives

    def objectivesStatus(self, space: 'pymunk.Space',
                         ships: 'Sequence[Device]') \
                             -> 'Sequence[Objective, bool]':

        return ((objective, objective.accomplished(space, ships))
                for objective in  self.__subobjectives)

    def accomplished(self, space: 'pymunk.Space',
                     ships: 'Sequence[Device]') -> bool:
        return all(acp for _, acp in accomplishedList(space, ships))
