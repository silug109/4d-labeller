import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import matplotlib.pyplot as plt
import numpy.matlib as matlib
from math import sin, cos, atan2, sqrt
import random
from window_2d import *
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


class ListWidg(QtWidgets.QListWidget):

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def mouseDoubleClickEvent(self, ev: QtGui.QMouseEvent) -> None:

        super().mouseDoubleClickEvent(ev)
        item = self.itemAt(ev.x(),ev.y())
        # print(item)
        print("DOUBLE CLICK YO")



class QCustomQWidget (QtGui.QWidget):
    def __init__ (self, parent = None):
        super(QCustomQWidget, self).__init__(parent)
        self.textQVBoxLayout = QtGui.QVBoxLayout()
        self.textUpQLabel = QtGui.QLabel()
        self.textDownQLabel = QtGui.QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.allQHBoxLayout = QtGui.QHBoxLayout()
        self.iconQLabel = QtGui.QLabel()
        self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.setLayout(self.allQHBoxLayout)
        # setStyleSheet
        self.textUpQLabel.setStyleSheet(''' color: rgb(0, 0, 255); ''')
        self.textDownQLabel.setStyleSheet(''' color: rgb(255, 0, 0); ''')
    def setTextUp (self, text):
        self.textUpQLabel.setText(text)
    def setTextDown (self, text):
        self.textDownQLabel.setText(text)
    def setIcon (self, imagePath):
       self.iconQLabel.setPixmap(QtGui.QPixmap(imagePath))


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
            # Create QListWidgetItem
            myQListWidgetItem = QtWidgets.QListWidgetItem(self.myQListWidget)
            # Set size hint
            myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
            # Add QListWidgetItem into QListWidget
            self.myQListWidget.addItem(myQListWidgetItem)
            self.myQListWidget.setItemWidget(myQListWidgetItem, myQCustomQWidget)
            self.setCentralWidget(self.myQListWidget)


if __name__ == "__main__":
    app = QtGui.QApplication([])
    window = exampleQMainWindow()
    window.show()
    sys.exit(app.exec_())