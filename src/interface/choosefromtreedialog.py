
from collections import Mapping

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from ..utils.fileinfo import FileInfo

UiChooseFromTree, _ = uic.loadUiType(FileInfo().uiFilePath('choosefromtree.ui'))

class ChooseFromTreeDialog(QDialog):

    def __init__(self, options: 'Sequence[anytree.Node]',
                 parent: 'QWidget' = None) -> None:

        QDialog.__init__(self, parent=parent)

        self.__ui = UiChooseFromTree()
        self.__ui.setupUi(self)

        self.__ui.treeView.setModel(QStandardItemModel())
        self.__ui.treeView.setUniformRowHeights(True)
        self.__ui.treeView.setHeaderHidden(True)

        self.__ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        self.__result = None

        for option in options:
            ChooseFromTreeDialog.__addOptions(self.__ui.treeView.model(),
                                              option)

        self.__ui.buttonBox.accepted.connect(self.__dialogAccepted)
        self.__ui.treeView.clicked.connect(self.__treeViewClicked)

    def getOption(self):
        self.__result = None
        self.exec_()
        return self.__result

    @staticmethod
    def __addOptions(parent_row, options: 'anytree.Node') -> None:

        item = QStandardItem(options.name)
        item.setEditable(False)
        parent_row.appendRow(item)

        for child in options.children:
            ChooseFromTreeDialog.__addOptions(item, child)

    def __dialogAccepted(self):
        current_item = self.__ui.treeView.model().itemFromIndex(
            self.__ui.treeView.currentIndex())

        result = []
        while current_item is not None:
            result.insert(0, current_item.text())
            current_item = current_item.parent()
        self.__result = tuple(result)

    def __treeViewClicked(self):

        current_item = self.__ui.treeView.model().itemFromIndex(
            self.__ui.treeView.currentIndex())

        self.__ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
            current_item.rowCount() == 0)
