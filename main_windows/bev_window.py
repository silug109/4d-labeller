from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtGui, QtCore
from libs.visualization import pointcloud_coords_generation
import sys
import numpy as np

from math import cos,pi, sqrt, sin

from libs.shape import Shape


CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor


def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())

class BoundingBox(pg.RectROI):

    def __init__(self, pos, size, centered=False, sideScalers=False, **args):
        super().__init__(self, pos, size, centered = centered, sideScalers= sideScalers, **args)
        # print(dir(self))

    # def mousePressEvent(self, ev):

class Bev_Canvas_2(pg.GraphicsView):

    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)

    SigBevChange = pyqtSignal(int)
    SigBevCreate = pyqtSignal()
    SigBevDelete = pyqtSignal()
    SigBevSelect = pyqtSignal()

    CREATE, EDIT = list(range(2))



    epsilon = 11.0

    def __init__(self, dev_mode = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print(f"dev mode {dev_mode}")

        self.dev_mode = dev_mode
        if self.dev_mode == "SOLO":
            self.objects = []
            self.selected_objects_idxs = []
        else:
            self.objects = self.parent().objects
            self.selected_objects_idxs = self.parent().selected_objects_idxs


        # self.objects = self.parent().objects
        # self.selected_objects_idxs = self.parent().selected_objects_idxs

        self.currentSelected = []

        self.bev_view = pg.ViewBox(border = {'color': "FF0", "width": 2})
        self.addItem(self.bev_view)
        self.setCentralWidget(self.bev_view)

        y_axis_item = pg.AxisItem('top', linkView= self.bev_view, showValues=False)
        x_axis_item = pg.AxisItem('left', linkView= self.bev_view, showValues=False)
        self.bev_view.addItem(x_axis_item)
        self.bev_view.addItem(y_axis_item)

        y_axis_item.setScale(5)
        y_axis_item.setRange(0,10)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)


    def highlight_selected(self):
        for roi in self.bev_view.addedItems:
            # if roi in self.currentSelected:
            if roi in [self.objects[idx]["Bev_object"] for idx in self.selected_objects_idxs]:
                print("in")
                self.highlight_roi(roi,True)
            else:
                print("not in")
                self.highlight_roi(roi, False)

    def highlight_roi(self, roi, highlight = True):
        if highlight == True:
            pen = (0, 255, 0)
        else:
            pen = (255,255,255)

        roi.setPen(pen)

    def mouseMoveEvent(self, ev):
        super().mouseMoveEvent(ev)

        if (self.parent() is not None) and hasattr(self.parent(),"change_status"):
            self.parent().change_status(''.join(["event in bev widget:", str(ev.pos().x()), " ", str(ev.pos().y())]))

        rois = [item for item in self.bev_view.addedItems if isinstance(item,pg.RectROI)]

        for roi in rois:
            if roi.isMoving or any([handle['item'].isMoving for handle in roi.handles]):
                print(f"Moving roi: {roi}")
                ind = [item["Bev_object"] for item in self.objects].index(roi)
                self.update_object_db(ind)

    # def mousePressEvent(self, ev):
    #     super().mousePressEvent(ev)
    #
    #     print(ev.pos())
    #     pos = ev.pos()
    #     if ev.button() == Qt.LeftButton:
    #         print("Trying to do selection over object")
    #         for object in self.objects:
    #             bbox = object["Bev_object"]
    #             print(bbox.pos())
    #             # if  bbox.pos.x() <= pos.x() <=


    def update_object_db(self, object_ind):
        object = self.objects[object_ind]
        bev_object = object["Bev_object"]
        x, y, l, w, angle = bev_object.pos()[0], bev_object.pos()[1], bev_object.size()[0], bev_object.size()[1], bev_object.angle()
        # x, y = x + l / 2, y + w / 2 #RECT ROI x,y - left bottom points though move it to logical center
        #TODO координаты меняются при поворотах
        coord = {"x": x, "y": y, "z": 5, "l": l, "w": w, "h": 10, "angle": angle}
        object["coord"] = coord

        # angle = 0
        # diag = sqrt((l/2)**2 + (w/2)**2)
        # init_angle = np.arctan(w/l)
        # cx = float(x + diag*cos((angle)/180*pi + init_angle))
        # cy = float(y + diag*sin((angle)/180*pi + init_angle))
        # cx = x + diag*cos((angle)/180*pi + init_angle)
        # cy = y + diag*sin((angle)/180*pi + init_angle)
        # x += diag * cos((angle) / 180 * pi + init_angle)
        # y += diag * sin((angle) / 180 * pi + init_angle)

        # print(x,diag*cos((angle)/180*pi + init_angle),y, diag*sin((angle)/180*pi + init_angle))
        # print(cx,cy)
        # print(sqrt(cx**2 + cy**2))
        # coord = {"x": cx, "y": cy, "z": 5, "l": l, "w": w, "h": 10, "angle": angle}
        # object["coord"] = coord
        # self.objects[object_ind] = object
        self.SigBevChange.emit(object_ind)

    def reset(self):
        for item in self.bev_view.addedItems:
            print(item)

    def update_object(self,object):
        coords = object["coord"]
        x,y,l,w,angle = coords["x"],coords["y"],coords["l"],coords["w"],coords["angle"]
        # x -= l/2
        # y -= w/2
        bounding_box = self.create_ROI_instance(pos = [x,y], size = [l,w], angle = angle)
        self.bev_view.addItem(bounding_box)
        object["Bev_object"] = bounding_box
        bounding_box.sigClicked.connect(self.print_clicked)
        # #alternative
        # objects = self.parent().objects
        # object = objects[obj_idx]
        # roi = object["Bev_object"]
        # coords = object["coord"]
        # roi.setAngle(coords["angle"])
        # # roi.setPos([coords["x"]-coords["l"]/2, coords["y"] - coords["w"]/2])
        # roi.setPos([coords["x"], coords["y"]])
        # roi.setSize([coords["l"], coords["w"]])

    def synchronize_object(self, object):
        # objects = self.parent().objects
        # object = objects[obj_idx]

        roi = object["Bev_object"]
        coords = object["coord"]

        # roi.setPos([coords["x"]-coords["l"]/2, coords["y"] - coords["w"]/2])
        roi.setPos([coords["x"], coords["y"]])
        roi.setSize([coords["l"],coords["w"]])
        roi.setAngle(coords["angle"])

    def create_ROI_instance(self, pos = [10,10], size = [20,20], angle = 0):
        # bounding_box = pg.RectROI(pos, size, angle = angle, centered=False, sideScalers=True)
        bounding_box = BoundingBox(pos, size, angle = angle, centered= False, sideScalers= True)
        bounding_box.addTranslateHandle([0.5, 0.5], [0.5, 0.5])
        # bounding_box.addRotateHandle([0.5, 1.5], [0.5, 0.5])
        # bounding_box.addRotateHandle([0.5, 1.5], [0.5, 0.5])
        return bounding_box

    def load_radar(self):
        bev_item = pg.ScatterPlotItem()
        bev_item.setData(pos=self.load_bev_project())

        # self.addItem(self.bev_view)

        # self.bev_widget.addItem(self.bev_view)
        self.setCentralWidget((self.bev_view))
        self.bev_view.addItem(bev_item)

    def load_bev_project(self):
        data = np.load('data/18.npy')
        data = data[::2, ::2, ::2]
        ptcld, _ = pointcloud_coords_generation(frame=data)
        xy = ptcld[:, 0:2]
        return xy



    ### test funcs
    def create_obj(self):
        coord = {"x": 0, "y": 0, "z": 5, "l": 10, "w": 10, "h": 10, "angle": 0}
        object = {'coord': coord}
        self.objects.append(object)
        self.update_object(object)


    def print_info(self):
        for object in self.objects:
            print(object)

    def check_synchro(self):
        for object in self.objects:
            object["coord"]["x"] += 10
            self.synchronize_object(object)

    def print_clicked(self,ev):
        print("Кажись, кого-то выбрали!")
        print(ev.pos())

    def check_select(self):
        for object in self.objects:
            bb = object["Bev_object"]
            bb.setSelected(False)
        print("selected")










if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    wind = QtWidgets.QWidget()

    layout = QtWidgets.QVBoxLayout()
    but_layout = QtWidgets.QHBoxLayout()

    canvas = Bev_Canvas_2(dev_mode = "SOLO")
    layout.addWidget(canvas)

    create_roi_but = QtWidgets.QPushButton("CREATE ROI")
    create_roi_but.clicked.connect(canvas.create_obj)
    but_layout.addWidget(create_roi_but)
    print_roi_but = QtWidgets.QPushButton("Print info")
    print_roi_but.clicked.connect(canvas.print_info)
    but_layout.addWidget(print_roi_but)
    sync_roi_but = QtWidgets.QPushButton("lets move")
    sync_roi_but.clicked.connect(canvas.check_synchro)
    but_layout.addWidget(sync_roi_but)
    select_roi_but = QtWidgets.QPushButton("lets select")
    select_roi_but.clicked.connect(canvas.check_select)
    but_layout.addWidget(select_roi_but)
    layout.addLayout(but_layout)


    wind.setLayout(layout)

    wind.show()
    sys.exit(app.exec())
