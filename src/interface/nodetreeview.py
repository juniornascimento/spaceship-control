
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class NodeTreeView(QTreeView):

    def __init__(self, parent: 'QWidget' = None) -> None:

        super().__init__(parent=parent)

        self.setModel(QStandardItemModel())
        self.setUniformRowHeights(True)
        self.setHeaderHidden(True)

    def clear(self):
        self.model().clear()

    def addNodes(self, nodes: 'Sequence[anytree.Node]') -> None:

        for node in nodes:
            NodeTreeView.__addNode(self.model(), node)

    def selectedItem(self) -> QStandardItem:
        return self.model().itemFromIndex(self.currentIndex())

    def selectedIsLeaf(self) -> bool:
        return self.selectedItem().rowCount() == 0

    def selectedItemPath(self) -> 'Tuple[QStandardItem, ...]':
        current_item = self.selectedItem()

        result = []
        while current_item is not None:
            result.insert(0, current_item)
            current_item = current_item.parent()

        return tuple(result)

    @staticmethod
    def __addNode(parent_row, options: 'anytree.Node') -> None:

        item = QStandardItem(options.name)
        item.setEditable(False)
        parent_row.appendRow(item)

        for child in options.children:
            NodeTreeView.__addNode(item, child)

