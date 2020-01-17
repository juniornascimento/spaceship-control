
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import QRectF, QPointF, Qt

class DrawingPart(ABC):

    def paint(self, painter, option, widget) -> None:
        painter.save()
        self._paint(painter, option, widget)
        painter.restore()

    @abstractmethod
    def boundingRect(self) -> QRectF:
        pass

    @abstractmethod
    def _paint(self, painter, option, widget) -> None:
        pass

class EllipseDrawingPart(DrawingPart):

    def __init__(self, height, width, color=None,
                 border_color=None, brush_color=None,
                 offset=QPointF(0, 0)):
        super().__init__()

        if border_color is None:
            self.__b_color = color
        else:
            self.__b_color = border_color

        if brush_color is None:
            self.__color = color
        else:
            self.__color = brush_color
        self.__offset = offset
        self.__a_radius = height/2
        self.__b_radius = width/2

    def boundingRect(self) -> QRectF:
        return QRectF(-self.__b_radius, -self.__a_radius, 2*self.__a_radius,
                      2*self.__b_radius)

    def _paint(self, painter, option, widget) -> None:
        if self.__b_color is not None:
            pen = painter.pen()
            pen.setColor(self.__b_color)
            painter.setPen(pen)
        if self.__color is not None:
            painter.setBrush(self.__color)

        painter.drawEllipse(self.__offset, self.__b_radius, self.__a_radius)

class LineDrawingPart(DrawingPart):

    def __init__(self, start, end, color=None) -> None:
        super().__init__()

        self.__start = start
        self.__end = end
        self.__color = color

    def boundingRect(self) -> QRectF:
        start_x = self.__start.x()
        start_y = self.__start.y()
        return QRectF(start_x, start_y, end_x - start_x, end_y - start_y)

    def _paint(self, painter, option, widget) -> None:
        if self.__color is not None:
            pen = painter.pen()
            pen.setColor(self.__color)
            painter.setPen(pen)

        painter.drawLine(self.__start, self.__end)

class ShipGraphicsItem(QGraphicsItem):

    def __init__(self, shapes) -> None:
        super().__init__()

        self.__parts = [EllipseDrawingPart(20, 20, color=Qt.blue),
                        LineDrawingPart(QPointF(0, 0), QPointF(10, 0),
                                        color=Qt.red)]

    def boundingRect(self) -> QRectF:
        return QRectF(-100, -100, 200, 200)

    def paint(self, painter, option, widget) -> None:

        for part in self.__parts:
            part.paint(painter, option, widget)
