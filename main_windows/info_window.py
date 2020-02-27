import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import matplotlib.pyplot as plt
import numpy.matlib as matlib
from math import sin, cos, atan2, sqrt
import random
# from window_2d import *
import numpy as np



# class ListWidgetMine(QtWidgets.QListWidget):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#
# class CustomListWidgetItem(QListWidgetItem, QLabel):
#     def __init__(self, parent=None):
#         QListWidgetItem.__init__(self, parent)
#         QLabel.__init__(self, parent)
#

import sys
from PyQt5 import QtGui,QtWidgets


class_list = ["Car", "Human", "Kamaz", "Moto"]

class ListWidg(QtWidgets.QListWidget):
    """модицифированный класс ListWidget с переопределенной логикой mouseDoubleClick"""

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def mouseDoubleClickEvent(self, ev: QtGui.QMouseEvent) -> None:

        super().mouseDoubleClickEvent(ev)
        item = self.itemAt(ev.x(),ev.y())
        print(item)
        print("DOUBLE CLICK YO")

        object = self.itemWidget(item)

        self.info_widget = Info_object_widget(object)
        # self.info_widget.load_item(item)
        self.info_widget.show()

class Info_object_widget(QtWidgets.QWidget):
    """
    виджет для вывода информации об объекте, на который сделали doubleClick
    при инициилизации передается object

    поля класса, координат можно менять, для этого надо поменять значения и нажать на кнопку Ok!

    """

    def __init__(self, item = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.name_label = QtWidgets.QLabel("МАШИНА, АГА", self)
        # self.class_label = QtWidgets.QLabel("Не МАШИНА, АГА", self)

        self.widg_layout = QtWidgets.QVBoxLayout()

        self.item = item

        self.name = QtWidgets.QLineEdit(self)
        self.name.setText("Да мне все равно на твои тачки")
        self.widg_layout.addWidget(self.name)

        self.coords = QtWidgets.QLineEdit(self)
        self.coords.setText("10,20,30,40")
        self.widg_layout.addWidget(self.coords)

        self.buttons_layout = QtWidgets.QHBoxLayout()

        self.ok_but = QtWidgets.QPushButton("Ok!",self)
        self.ok_but.clicked.connect(self.save_changes)
        self.buttons_layout.addWidget(self.ok_but)

        self.cancel_but = QtWidgets.QPushButton("cancel",self)
        self.cancel_but.clicked.connect(self.close)
        self.buttons_layout.addWidget(self.cancel_but)

        self.load_but = QtWidgets.QPushButton("load", self)
        self.load_but.clicked.connect(self.load_item)
        self.buttons_layout.addWidget(self.load_but)

        self.change_but = QtWidgets.QPushButton("change", self)
        self.change_but.clicked.connect(self.change_class)
        self.buttons_layout.addWidget(self.change_but)

        self.widg_layout.addLayout(self.buttons_layout)

        self.setLayout(self.widg_layout)

    def load_item(self):
        # print(self.item.textUpQLabel.text())
        pass

    def save_changes(self):
        text = self.name.text()
        coords_text = self.coords.text()
        # print(text, class_text)
        self.item["class"] = text
        self.item["coord"] = coords


    def change_class(self):
        items = ("Car", "Human", "Kamaz", "Python")
        item, ok = QtWidgets.QInputDialog.getItem(self, "select input dialog",
                                        "list of languages", items, 0, False)

        if ok and item:
            self.name.setText(str(item))




class QCustomQWidget (QtGui.QWidget):
    def __init__ (self, parent = None):
        super(QCustomQWidget, self).__init__(parent)
        self.textQVBoxLayout = QtGui.QVBoxLayout()
        self.textUpQLabel = QtGui.QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textDownQLabel = QtGui.QLabel()
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.allQHBoxLayout = QtGui.QHBoxLayout()

        self.class_combo = QtWidgets.QComboBox()
        self.allQHBoxLayout.addWidget(self.class_combo)

        # self.class_dialog = QtWidgets.QInputDialog()
        # self.allQHBoxLayout.addWidget(self.class_dialog)
        #
        # items = ("C", "C++", "Java", "Python")
        #
        # item, ok = self.class_dialog.getItem(self, "select input dialog",
        #                                 "list of languages", items, 0, False)

        # TODO продумать поля этого объекта

        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.setLayout(self.allQHBoxLayout)
        # setStyleSheet
        self.textUpQLabel.setStyleSheet(''' color: rgb(0, 0, 255); ''')
        self.textDownQLabel.setStyleSheet(''' color: rgb(255, 0, 0); ''')

        self.setComboBox()
        self.class_combo.currentIndexChanged.connect(self.print_if_change)

    def print_if_change(self):
        print(self," CHANGED its class to ", self.class_combo.currentText())



    def setTextUp (self, text):
        self.textUpQLabel.setText(text)
    def setTextDown (self, text):
        self.textDownQLabel.setText(text)
    def setComboBox(self):
        self.class_combo.insertItems(1,class_list)

        # TODO как выкидывать измененный объект из класса, который ни наследуется, ни может возвращать


class ObjectLabel(QtGui.QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.Vlayout = QtGui.QVBoxLayout()
        self.class_name = QtGui.Qlabel()
        self.size_label = QtGui.Qlabel()
        self.Vlayout.addWidget(self.class_name)
        self.Vlayout.addWidget(self.size_label)
        self.Hlayout = QtGui.QHBoxLayout()
        self.iconLabel = QtGui.Qlabel()
        self.Hlayout.addLayout(self.Vlayout)
        self.Hlayout.addWidget(self.iconLabel)
        self.setLayout(self.Hlayout)

    def setObject(self, object):
        self.class_name.setText(object["class"])
        self.size_label.setText(str(object["size"]))


class exampleQMainWindow (QtGui.QMainWindow):
    def __init__ (self):
        super(exampleQMainWindow, self).__init__()
        # Create QListWidget
        # self.myQListWidget = QtGui.QListWidget(self)
        self.myQListWidget = ListWidg(self)
        # self.myQListWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        for index, name, icon in [ ('No.1', 'Meyoko', 'icon.png'), ('No.2', 'Nyaruko', 'icon.png'), ('No.3', 'Louise', 'icon.png')]:
            # Create QCustomQWidget
            myQCustomQWidget = QCustomQWidget()
            myQCustomQWidget.setTextUp(index)
            myQCustomQWidget.setTextDown(name)
            # myQCustomQWidget.setIcon(icon)
            myQListWidgetItem = QtWidgets.QListWidgetItem(self.myQListWidget)
            myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
            # Add QListWidgetItem into QListWidget
            self.myQListWidget.addItem(myQListWidgetItem)
            self.myQListWidget.setItemWidget(myQListWidgetItem, myQCustomQWidget)
            # print(myQListWidgetItem)
            # print(myQListWidgetItem.ItemWidget)
            # print(self.myQListWidget.itemWidget(myQListWidgetItem))

            self.setCentralWidget(self.myQListWidget)


if __name__ == "__main__":
    app = QtGui.QApplication([])
    window = exampleQMainWindow()
    window.show()
    sys.exit(app.exec_())