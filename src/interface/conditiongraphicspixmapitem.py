
from PyQt5.QtWidgets import QGraphicsPixmapItem

class ConditionGraphicsPixmapItem(QGraphicsPixmapItem):

    def __init__(self, *args, **kwargs, condition=None) -> None:
        super().__init__(*args, **kwargs)

        self.__condition = Condition(condition) if condition else None
        self.__is_visible = self.isVisible()
        self.__condition_met = False

    def show(self) -> None:
        self.setVisible(True)

    def hide(self) -> None:
        self.setVisible(False)

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible and self.__condition_met)
        self.__is_visible = visible

    def isVisible(self) -> bool:
        return self.__is_visible

    def evaluate(self, *args, **kwargs):
        self.__condition_met = self.__condition.evaluate(*args, **kwargs)
        if self.__is_visible:
            super().setVisible(self.__condition_met)

