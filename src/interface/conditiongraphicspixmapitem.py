
from PyQt5.QtWidgets import QGraphicsPixmapItem

from ..utils.condition import Condition

class ConditionGraphicsPixmapItem(QGraphicsPixmapItem):

    def __init__(self, condition, *args, names=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.__condition = Condition(condition)
        self.__is_visible = True
        self.__condition_met = False
        self.__names = {} if names is None else names

    def show(self) -> None:
        self.setVisible(True)

    def hide(self) -> None:
        self.setVisible(False)

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible and self.__condition_met)
        self.__is_visible = visible

    def isVisible(self) -> bool:
        return self.__is_visible

    def evaluate(self, **kwargs):

        self.__condition_met = self.__condition.evaluate(**self.__names,
                                                         **kwargs)

        if self.__is_visible:
            super().setVisible(self.__condition_met)
