
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QRectF

class ShipGraphicsItem(QGraphicsItem):

    def __init__(self) -> None:
        super().__init__()

    def boundingRect(self) -> QRectF:
        return QRectF(self.x() - 20, self.y() - 20, 20, 20)

    def paint(self, painter, _option, _widget) -> None:
        painter.drawRect(self.boundingRect());
