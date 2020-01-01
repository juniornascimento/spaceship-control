
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QRectF, QPointF, Qt

class ShipGraphicsItem(QGraphicsItem):

    def __init__(self) -> None:
        super().__init__()

    def boundingRect(self) -> QRectF:
        return QRectF(-100, -100, 100, 100)

    def paint(self, painter, _option, _widget) -> None:
        pen = painter.pen()
        pen.setColor(Qt.blue)
        painter.setBrush(Qt.blue);
        painter.setPen(pen)
        painter.drawEllipse(self.pos(), 10, 10);
        pen.setColor(Qt.red)
        painter.setPen(pen)
        painter.drawLine(self.pos(), QPointF(self.x() + 10, self.y()))
