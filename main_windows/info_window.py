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
from PyQt5 import QtGui,QtWidgets, QtCore


class_list = ["Car", "Human", "Kamaz", "Moto"]

class ListWidg(QtWidgets.QListWidget):
    """модицифированный класс ListWidget с переопределенной логикой mouseDoubleClick"""

    SigSelectionChanged = QtCore.pyqtSignal()

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.current_selected = []



    def mouseDoubleClickEvent(self, ev: QtGui.QMouseEvent) -> None:

        super().mouseDoubleClickEvent(ev)
        self.item = self.itemAt(ev.x(),ev.y())
        print(self.item)
        print("DOUBLE CLICK YO")

        self.object = self.itemWidget(self.item)

        self.info_widget = Info_object_widget(item = self.object)
        self.info_widget.SigCloseWidget.connect(self.updateItem)
        # self.info_widget.close.connect(self.print_close)
        # self.info_widget.load_item(item)
        self.info_widget.show()


    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(ev)

        if self.current_selected != self.selectedItems():
            self.current_selected = self.selectedItems()
            self.SigSelectionChanged.emit()
        else:
            self.current_selected = self.selectedItems()

    def updateItem(self):
        self.new_object = self.info_widget.get_object()
        # self.object.class_combo = self.new_object.class_combo
        self.object.setTextUp(self.new_object[0])
        self.object.setTextDown(self.new_object[1])

        print(self.new_object[2])









class Info_object_widget(QtWidgets.QWidget):
    """
    виджет для вывода информации об объекте, на который сделали doubleClick
    при инициилизации передается object

    поля класса, координат можно менять, для этого надо поменять значения и нажать на кнопку Ok!

    """
    SigCloseWidget = QtCore.pyqtSignal()

    def __init__(self, item = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.name_label = QtWidgets.QLabel("МАШИНА, АГА", self)
        # self.class_label = QtWidgets.QLabel("Не МАШИНА, АГА", self)

        self.widg_layout = QtWidgets.QVBoxLayout()

        print(item.textUpQLabel.text())
        print(item.textDownQLabel.text())
        print(item.class_combo.itemText(item.class_combo.currentIndex()))
        # print(self.item.class_combo.items)

        self.name = QtWidgets.QLineEdit(self)
        self.name.setText("Да мне все равно на твои тачки")
        self.widg_layout.addWidget(self.name)

        self.x_layout = QtWidgets.QHBoxLayout()
        self.x_coord_label = QtWidgets.QLabel(self, text= "x:")
        self.x_layout.addWidget(self.x_coord_label)
        self.x_coord = QtWidgets.QLineEdit(self)
        self.x_coord.setText("10")
        self.x_layout.addWidget(self.x_coord)
        self.widg_layout.addLayout(self.x_layout)
        # self.widg_layout.addWidget(self.x_coord)

        self.y_layout = QtWidgets.QHBoxLayout()
        self.y_coord_label = QtWidgets.QLabel(self, text="y:")
        self.y_layout.addWidget(self.y_coord_label)
        self.y_coord = QtWidgets.QLineEdit(self)
        self.y_coord.setText("10")
        self.y_layout.addWidget(self.y_coord)
        self.widg_layout.addLayout(self.y_layout)
        # self.widg_layout.addWidget(self.y_coord)

        self.z_layout = QtWidgets.QHBoxLayout()
        self.z_coord_label = QtWidgets.QLabel(self, text="z:")
        self.z_layout.addWidget(self.z_coord_label)
        self.z_coord = QtWidgets.QLineEdit(self)
        self.z_coord.setText("10")
        self.z_layout.addWidget(self.z_coord)
        self.widg_layout.addLayout(self.z_layout)
        # self.widg_layout.addWidget(self.z_coord)

        self.length_layout = QtWidgets.QHBoxLayout()
        self.length_label = QtWidgets.QLabel(self, text="length:")
        self.length_layout.addWidget(self.length_label)
        self.length_box = QtWidgets.QLineEdit(self)
        self.length_box.setText("10")
        self.length_layout.addWidget(self.length_box)
        self.widg_layout.addLayout(self.length_layout)
        # self.widg_layout.addWidget(self.length_box)

        self.width_layout = QtWidgets.QHBoxLayout()
        self.width_label = QtWidgets.QLabel(self, text="width:")
        self.width_layout.addWidget(self.width_label)
        self.width_box = QtWidgets.QLineEdit(self)
        self.width_box.setText("10")
        self.width_layout.addWidget(self.width_box)
        self.widg_layout.addLayout(self.width_layout)
        # self.widg_layout.addWidget(self.width_box)

        self.depth_layout = QtWidgets.QHBoxLayout()
        self.depth_label = QtWidgets.QLabel(self, text="depth:")
        self.depth_layout.addWidget(self.depth_label)
        self.depth_box = QtWidgets.QLineEdit(self)
        self.depth_box.setText("10")
        self.depth_layout.addWidget(self.depth_box)
        self.widg_layout.addLayout(self.depth_layout)
        # self.widg_layout.addWidget(self.depth_box)

        self.angle_layout = QtWidgets.QHBoxLayout()
        self.angle_label = QtWidgets.QLabel(self, text="angle:")
        self.angle_layout.addWidget(self.angle_label)
        self.angle_box = QtWidgets.QLineEdit(self)
        self.angle_box.setText("10")
        self.angle_layout.addWidget(self.angle_box)
        self.widg_layout.addLayout(self.angle_layout)

        self.additional_info = QtWidgets.QLineEdit(self)
        self.additional_info.setText("")
        self.widg_layout.addWidget(self.additional_info)

        # self.class_choice = copy.copy(item.class_combo)
        # # self.class_choice = QtWidgets.QComboBox()
        # # for ind in range(self.item.class_combo.count()):
        # #     self.class_choice.addItem(self.item.class_combo.itemText(ind))
        # self.widg_layout.addWidget(self.class_choice)
        #TODO combobox disappear when IngoWidget initilized

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

        self.widg_layout.addLayout(self.buttons_layout)

        self.setLayout(self.widg_layout)


    def load_item(self):
        # print(self.item.textUpQLabel.text())
        pass

    def save_changes(self):
        self.SigCloseWidget.emit()
        self.close()

    def get_object(self):

        name = self.name.text()
        x = self.x_coord.text()
        y = self.y_coord.text()
        z = self.z_coord.text()
        length = self.length_box.text()
        width = self.width_box.text()
        depth = self.depth_box.text()
        angle = self.angle_box.text()

        combo = self.class_choice
        print(combo)
        class_name = self.class_choice.itemText(self.class_choice.currentIndex())
        class_name_idx = self.class_choice.currentIndex()

        # obj_inst = QCustomQWidget()
        # obj_inst.setTextUp(name)
        # obj_inst.setTextDown(''.join([x,y,z,length,width,depth]))
        # obj_inst.class_combo = self.item.class_combo
        # obj_inst.class_combo.activated(class_name_idx)

        return name, ''.join([x,y,z,length,width,depth,angle]), combo
    #Todo update return and parsing of objects back to listwidget




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


# class ObjectLabel(QtGui.QWidget):
#     def __init__(self, parent = None):
#         super().__init__(parent)
#         self.Vlayout = QtGui.QVBoxLayout()
#         self.class_name = QtGui.Qlabel()
#         self.size_label = QtGui.Qlabel()
#         self.Vlayout.addWidget(self.class_name)
#         self.Vlayout.addWidget(self.size_label)
#         self.Hlayout = QtGui.QHBoxLayout()
#         self.iconLabel = QtGui.Qlabel()
#         self.Hlayout.addLayout(self.Vlayout)
#         self.Hlayout.addWidget(self.iconLabel)
#         self.setLayout(self.Hlayout)
#
#     def setObject(self, object):
#         self.class_name.setText(object["class"])
#         self.size_label.setText(str(object["size"]))


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