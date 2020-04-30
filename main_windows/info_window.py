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



import sys
from PyQt5 import QtGui,QtWidgets, QtCore
from PyQt5.QtGui import *

class_list = ["Car", "Human", "Kamaz", "Moto"]

class ListWidg(QtWidgets.QListWidget):
    """модицифированный класс ListWidget с переопределенной логикой mouseDoubleClick"""

    SigSelectionChanged = QtCore.pyqtSignal(str)
    SigObjectChanged = QtCore.pyqtSignal(int)
    SigObjectDeleted = QtCore.pyqtSignal([list])
    SigCreateObject = QtCore.pyqtSignal()

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.current_selected = []

        self.objects = self.parent().objects


    def mouseDoubleClickEvent(self, ev: QtGui.QMouseEvent) -> None:

        super().mouseDoubleClickEvent(ev)

        self.item_chosen = self.itemAt(ev.x(),ev.y())
        print(self.item_chosen)
        print("DOUBLE CLICK YO")

        self.WidgetItem = self.itemWidget(self.item_chosen)
        self.obj_idx = [item["listwidgetitem"] for item in self.parent().objects].index(self.WidgetItem)
        self.object = self.parent().objects[self.obj_idx]

        self.info_widget = Info_object_widget(coords = self.object["coord"])
        self.info_widget.SigCloseWidget.connect(self.updateItem)
        self.info_widget.show()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(ev)

        # print("previous: ", self.current_selected)
        print("now selected: ", self.selectedItems())
        # print("decision of comparison", self.current_selected != self.selectedItems() )

        if self.current_selected != self.selectedItems():
            self.current_selected = self.selectedItems()
            self.SigSelectionChanged.emit("list")
            #TODO someshit
        # else:
        #     self.current_selected = self.selectedItems()

    def update_object(self, object):
        coords = object["coord"]
        id = object["id"]
        ListWidgetItemObject, ListWidgetItem = self.create_item()
        ListWidgetItemObject.setTextUp(id)
        ListWidgetItemObject.setTextDown(str(coords))

        self.add_item(ListWidgetItem,ListWidgetItemObject)

        object["listwidgetitem"] = ListWidgetItemObject
        object["listitem"] = ListWidgetItem

        # return object





    def updateItem(self):
        print("Is info_widget exist:", hasattr(self, "info_widget"))

        if hasattr(self,"info_widget"):
            self.new_object = self.info_widget.get_object()
            # print("Old: ",self.object["coord"])
            self.object["coord"] = self.new_object[1]
            self.object["id"] = self.new_object[0]
            # print("New: ", self.object["coord"])
            #здесь происходит синхронизация, разобраться. апдейтится self.parent().objects[self.obj_idx]

            self.WidgetItem.setTextUp(self.new_object[0])
            self.WidgetItem.setTextDown(str(self.new_object[1]))
            self.SigObjectChanged.emit(self.obj_idx)
        elif hasattr(self, "new_object_widget"):
            print("WOO HOO new widget and object!!! WOO HOOO")
            self.new_object = self.new_object_widget.get_object()

            self.WidgetItem.setTextUp(self.new_object[0])
            self.WidgetItem.setTextDown(str(self.new_object[1]))

            self.object_instance["coord"] = self.new_object[1]
            self.object_instance["class"] = self.new_object[2]
            self.SigCreateObject.emit()

            # print("written inside update func, should be second")

            #todo synchronization

            # self.parent().objects.append(object_instance)
            #
            # print("ВОТ ЗДЕСЬ ПРОВЕРОЧКА")
            # self.parent().update_db()
            #
            # obj_ind = len(self.parent().objects) - 1
            #
            # self.SigBevChange.emit(obj_ind)
            #
            # print("Creation is success!")
            # return bounding_box
            # self.parent().objects.append

        else:
            print("Nothing")
            pass

        # self.object.class_combo = self.new_object.class_combo


    def synchronizeListItem(self, obj_idx):
        objects = self.parent().objects
        object = objects[obj_idx]

        WidgetItem = object["listwidgetitem"]
        coords = object["coord"]

        WidgetItem.setTextDown(str(coords))
        WidgetItem.setTextUp(object["id"])

    def update_selection(self):
        for list_row in range(self.count()):
            print("list row: ", list_row)

            list_item = self.item(list_row)

            print("list item: ", list_item)

            if list_item in self.current_selected:
                list_item.setSelected(True)
            else:
                list_item.setSelected(False)

            # list_ind = self.row(list_item)
            # list_instance = self.item(list_ind)
            # list_instance.setSelected(True)

    def update_class(self, value):
        print("class changed ", value)

        idx_changed = [object["listwidgetitem"] for object in self.parent().objects].index(value)
        self.object = self.parent().objects[idx_changed]
        print(self.object)
        print(value.class_combo.currentText())
        self.object["class"] = value.class_combo.currentText()
        # self.object["class"] = value.class_combo.text()
        # idx_changed = [self.itemWidget(self.item(ind)) for ind in range(self.count())].index(value)

        self.SigObjectChanged.emit(idx_changed)
        #todo порядок может иметь роль.

        # SigObjectChanged.emit

    def create_item(self):
        myListWidgetObject = QCustomQWidget() # это то, что добавляется после
        # myListWidgetObject.setTextUp(id_instance)
        # myListWidgetObject.setTextDown(str(coord))
        # myListWidgetObject.class_combo.currentIndexChanged.connect(self.change_class)
        myListWidgetObject.SigClassChanged.connect(self.update_class)

        ListWidgetItem = QtWidgets.QListWidgetItem(self)  # это то, что появляется как элемент
        ListWidgetItem.setSizeHint(myListWidgetObject.sizeHint())
        # self.list_widget.addItem(ListWidgetItem)
        # self.list_widget.setItemWidget(ListWidgetItem, myListWidgetObject)
        return myListWidgetObject, ListWidgetItem

    def add_item(self, item, item_object):
        self.addItem(item)
        self.setItemWidget(item,item_object)


    def create_new_bb_item(self):
        ListWidgetObject, ListWidgetItem = self.create_item()
        self.addItem(ListWidgetItem)
        self.setItemWidget(ListWidgetItem, ListWidgetObject)
        # self.addItem(ListWidgetObject, ListWidgetItem)

        # self.WidgetItem = self.currentItem()
        # print(self.count(), self.item(self.count() - 1 ))
        self.WidgetItem = self.itemWidget(self.item(self.count() -1))

        self.object_instance = {}
        self.object_instance["listwidgetitem"] = ListWidgetObject
        self.object_instance["listitem"] = ListWidgetItem

        self.new_object_widget = Info_object_widget(coords=None)
        self.new_object_widget.SigCloseWidget.connect(self.updateItem)
        self.new_object_widget.show()

        print("test is written inside create_new_bb should be first")

    def delete_item(self, list_item):
        self.takeItem(self.row(list_item))
        return 'Success'




#TODO Как-то пробросить SigObjectChanged от изменения combobox  внутрь ListWidget


class Info_object_widget(QtWidgets.QWidget):
    """
    виджет для вывода информации об объекте, на который сделали doubleClick
    при инициилизации передается object

    поля класса, координат можно менять, для этого надо поменять значения и нажать на кнопку Ok!

    """
    SigCloseWidget = QtCore.pyqtSignal()

    def __init__(self, coords = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.widg_layout = QtWidgets.QVBoxLayout()

        # coords = kwargs.get("coords", None)
        if coords == None:
            coords = {"x": 10, "y": 10, "z": 5, "l": 10, "w": 10, "h": 10, "angle": 10}

        self.name = QtWidgets.QLineEdit(self)
        self.name.setText("Да мне все равно на твои тачки")
        self.widg_layout.addWidget(self.name)

        self.x_layout = QtWidgets.QHBoxLayout()
        self.x_coord_label = QtWidgets.QLabel(self, text= "x:")
        self.x_layout.addWidget(self.x_coord_label)
        self.x_coord = QtWidgets.QLineEdit(self)
        self.x_coord.setText(str(coords["x"]))
        self.x_layout.addWidget(self.x_coord)
        self.widg_layout.addLayout(self.x_layout)

        self.y_layout = QtWidgets.QHBoxLayout()
        self.y_coord_label = QtWidgets.QLabel(self, text="y:")
        self.y_layout.addWidget(self.y_coord_label)
        self.y_coord = QtWidgets.QLineEdit(self)
        self.y_coord.setText(str(coords["y"]))
        self.y_layout.addWidget(self.y_coord)
        self.widg_layout.addLayout(self.y_layout)

        self.z_layout = QtWidgets.QHBoxLayout()
        self.z_coord_label = QtWidgets.QLabel(self, text="z:")
        self.z_layout.addWidget(self.z_coord_label)
        self.z_coord = QtWidgets.QLineEdit(self)
        self.z_coord.setText(str(coords["z"]))
        self.z_layout.addWidget(self.z_coord)
        self.widg_layout.addLayout(self.z_layout)

        self.length_layout = QtWidgets.QHBoxLayout()
        self.length_label = QtWidgets.QLabel(self, text="length:")
        self.length_layout.addWidget(self.length_label)
        self.length_box = QtWidgets.QLineEdit(self)
        self.length_box.setText(str(coords["l"]))
        self.length_layout.addWidget(self.length_box)
        self.widg_layout.addLayout(self.length_layout)

        self.width_layout = QtWidgets.QHBoxLayout()
        self.width_label = QtWidgets.QLabel(self, text="width:")
        self.width_layout.addWidget(self.width_label)
        self.width_box = QtWidgets.QLineEdit(self)
        self.width_box.setText(str(coords["w"]))
        self.width_layout.addWidget(self.width_box)
        self.widg_layout.addLayout(self.width_layout)

        self.depth_layout = QtWidgets.QHBoxLayout()
        self.depth_label = QtWidgets.QLabel(self, text="depth:")
        self.depth_layout.addWidget(self.depth_label)
        self.depth_box = QtWidgets.QLineEdit(self)
        self.depth_box.setText(str(coords["h"]))
        self.depth_layout.addWidget(self.depth_box)
        self.widg_layout.addLayout(self.depth_layout)

        self.angle_layout = QtWidgets.QHBoxLayout()
        self.angle_label = QtWidgets.QLabel(self, text="angle:")
        self.angle_layout.addWidget(self.angle_label)
        self.angle_box = QtWidgets.QLineEdit(self)
        self.angle_box.setText(str(coords["angle"]))
        self.angle_layout.addWidget(self.angle_box)
        self.widg_layout.addLayout(self.angle_layout)

        self.additional_info_label = QtWidgets.QLabel(parent = self, text =  "Additional info")
        self.widg_layout.addWidget(self.additional_info_label)

        self.additional_info = QtWidgets.QLineEdit(self)
        self.additional_info.setText("")
        self.widg_layout.addWidget(self.additional_info)

        # self.class_choice = copy.copy(item.class_combo)
        # # self.class_choice = QtWidgets.QComboBox()
        # # for ind in range(self.item.class_combo.count()):
        # #     self.class_choice.addItem(self.item.class_combo.itemText(ind))
        # self.widg_layout.addWidget(self.class_choice)
        #TODO combobox disappear when InfoWidget initilized

        self.buttons_layout = QtWidgets.QHBoxLayout()

        self.ok_but = QtWidgets.QPushButton("Ok!",self)
        self.ok_but.clicked.connect(self.save_changes)
        self.buttons_layout.addWidget(self.ok_but)

        self.cancel_but = QtWidgets.QPushButton("cancel",self)
        self.cancel_but.clicked.connect(self.close)
        self.buttons_layout.addWidget(self.cancel_but)
        self.widg_layout.addLayout(self.buttons_layout)
        self.setLayout(self.widg_layout)


    def save_changes(self):
        self.SigCloseWidget.emit()
        self.close()

    def get_object(self):
        name = self.name.text()
        x = float(self.x_coord.text())
        y = float(self.y_coord.text())
        z = float(self.z_coord.text())
        length = float(self.length_box.text())
        width = float(self.width_box.text())
        depth = float(self.depth_box.text())
        angle = float(self.angle_box.text())

        combo = "Car"
        # combo = self.class_choice
        # print(combo)
        # class_name = self.class_choice.itemText(self.class_choice.currentIndex())
        # class_name_idx = self.class_choice.current


        return name, {"x": x, "y": y, "z": z, "l": length, "w": width, "h": depth, "angle": angle}, combo


class QCustomQWidget(QtWidgets.QWidget):
    '''
    ListWidgetItem - отображает краткую информацию об объекте разметки.
    Combobox - выбор класса.
    Id - айди объекта
    Coord - вывод координат объектов
    '''

    SigClassChanged = QtCore.pyqtSignal('PyQt_PyObject')

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

        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.setLayout(self.allQHBoxLayout)
        # setStyleSheet
        self.textUpQLabel.setStyleSheet(''' color: rgb(0, 0, 255); ''')
        self.textDownQLabel.setStyleSheet(''' color: rgb(255, 0, 0); ''')

        self.setComboBox()
        self.class_combo.currentIndexChanged.connect(self.change_class)
    # def print_if_change(self):
    #     print(self," CHANGED its class to ", self.class_combo.currentText())

    def setTextUp (self, text):
        self.textUpQLabel.setText(text)
    def setTextDown (self, text):
        self.textDownQLabel.setText(text)
    def setComboBox(self):
        self.class_combo.insertItems(1,class_list)
    def change_class(self):
        self.SigClassChanged.emit(self)
        # TODO как выкидывать измененный объект из класса, который ни наследуется, ни может возвращать

class exampleQMainWindow (QtGui.QMainWindow):
    def __init__ (self):
        super(exampleQMainWindow, self).__init__()
        # Create QListWidget
        # self.myQListWidget = QtGui.QListWidget(self)
        self.myQListWidget = ListWidg(self)
        # self.myQListWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        for index, name, icon in [ ('No.1', 'Meyoko', 'icon.png'), ('No.2', 'Nyaruko', 'icon.png'), ('No.3', 'Louise', 'icon.png')]:
            myQCustomQWidget, myQListWidgetItem = self.myQListWidget.create_item()

            # myQCustomQWidget = QCustomQWidget()
            myQCustomQWidget.setTextUp(index)
            myQCustomQWidget.setTextDown(name)
            # myQListWidgetItem = QtWidgets.QListWidgetItem(self.myQListWidget)
            # myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
            # Add QListWidgetItem into QListWidget
            self.myQListWidget.addItem(myQListWidgetItem)
            self.myQListWidget.setItemWidget(myQListWidgetItem, myQCustomQWidget)

            self.setCentralWidget(self.myQListWidget)


if __name__ == "__main__":
    app = QtGui.QApplication([])
    window = exampleQMainWindow()
    window.show()
    sys.exit(app.exec_())