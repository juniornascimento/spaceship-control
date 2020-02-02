
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class NodeValue:

    def __init__(self, name, description):
        self.__name = name
        self.__desc = description
        self.__item = None

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, new_val):
        self.__name = new_val
        if self.__item is not None:
            self.__item.setText(new_val)

    @property
    def description(self):
        return self.__desc

    @description.setter
    def description(self, new_val):
        self.__desc = new_val
        if self.__item is not None:
            self.__item.setToolTip(new_val)

    def __setItem(self, new_val):
        self.__item = new_val

    item = property(None, __setItem)

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

        node_value = options.name
        set_item = False

        if isinstance(node_value, NodeValue):
            set_item = True
            node_desc = node_value.description
            node_name = node_value.name
        elif isinstance(node_value, tuple):
            node_desc = node_value[1]
            node_name = node_value[0]
        else:
            node_name = node_value
            node_desc = None

        item = QStandardItem(node_name)

        if node_desc:
            item.setToolTip(node_desc)
        item.setEditable(False)
        parent_row.appendRow(item)

        for child in options.children:
            NodeTreeView.__addNode(item, child)

        if set_item is True:
            node_value.item = item
