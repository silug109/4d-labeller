from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg
import pyqtgraph.opengl as gl
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

# class BoundingBox(pg.RectROI):
#
#     # def __init__(self, pos, size, centered=False, sideScalers=False, **args):
#     #     super().__init__(pos, size, **args)
#     #     if centered:
#     #         center = [0.5, 0.5]
#     #     else:
#     #         center = [0, 0]
#     #
#     #     self.addScaleHandle([1, 1], center)
#     #     if sideScalers:
#     #         self.addScaleHandle([1, 0.5], [center[0], 0.5])
#     #         self.addScaleHandle([0.5, 1], [0.5, center[1]])
#
#     def __init__(self, pos, size, centered=False, sideScalers=False, **args):
#         print("creating inside class")
#         super().__init__(pos, size, centered = centered, sideScalers= sideScalers, **args)
#         self.extra = None
#         print("Lookkkk")
#         # print(dir(self))
#     #
#     def mousePressEvent(self, ev):
#         print("AAAAAA SUKA")

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
        bounding_box = pg.RectROI(pos, size, angle = angle, centered=False, sideScalers=True)
        # bounding_box = BoundingBox(pos, size, centered= False, sideScalers= True)
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

    ### t est funcs
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


class Volumetric_widget_BEV(gl.GLViewWidget):

    SigCreate3dObject = pyqtSignal()
    SigSelect3dObject = pyqtSignal(str)
    SigChanged3dObject = pyqtSignal(int)
    SigDelete3dObject = pyqtSignal()

    def __init__(self, dev_mode = None, *args, **kwargs):

        self.dev_mode = dev_mode
        self.scale = 1.0

        super().__init__(*args, **kwargs)



        axis_qt = gl.GLAxisItem()
        grid3d_qt = gl.GLGridItem()
        self.addItem(grid3d_qt)
        self.addItem(axis_qt)

        self.mousePos = QtCore.QPoint(0,0)
        self.setMouseTracking(True)
        self.current_selected = []
        self.threshold = 0.5

        self.setCameraPosition(elevation= 90, azimuth= 0)
        self.opts["center"] = QVector3D(0,0,10)
        self.update()

        self.objects = self.parent().objects
        self.selected_object_idxs = self.parent().selected_objects_idxs

        # if (self.dev_mode is None):
        #     self.objects = self.parent().objects
        #     self.selected_object_idxs = self.parent().selected_objects_idxs
        # else:
        #     self.objects = []
        #     self.selected_object_idxs = []


    def mouseMoveEvent(self, ev):

        # super().mouseMoveEvent(ev)

        diff = ev.pos() - self.mousePos
        self.mousePos = ev.pos()

        if ev.buttons() == QtCore.Qt.LeftButton:
            if ev.modifiers() == QtCore.Qt.ControlModifier:

                self.orbit(-diff.x(), 0)
        elif ev.buttons() == QtCore.Qt.RightButton:
            self.pan(diff.x(), diff.y(), 0, relative = True)

    def mousePressEvent(self, ev):
        if ev.buttons() == Qt.LeftButton:
            if  ev.modifiers() == QtCore.Qt.ShiftModifier:
                print("режим множественного выделения")
                new_objects = self.itemsAt([ev.pos().x(), ev.pos().y(), 1,1])
                for object in new_objects:
                    if isinstance(object, gl.GLMeshItem):
                        if object in self.current_selected:
                            self.current_selected.discard(object)
                        else:
                            self.current_selected.add(object)
            else:
                new_selected_objects = self.itemsAt([ev.pos().x(), ev.pos().y(), 1, 1])

                self.current_selected = set([object for object in new_selected_objects if isinstance(object, gl.GLMeshItem)])

        self.SigSelect3dObject.emit("Bev")
        self.highlight_selected()

    def wheelEvent(self, ev):
        delta = ev.angleDelta()
        delta_value = delta.y()/120

        if ev.modifiers() == QtCore.Qt.ShiftModifier:
            self.scale_object(self.current_selected, delta_value)
        elif ev.modifiers() == QtCore.Qt.ControlModifier:
            self.translate_object(self.current_selected, delta_value)
        elif ev.modifiers() == QtCore.Qt.AltModifier:
            delta_value = delta.x() / 120
            self.rotate_object(self.current_selected, delta_value)
        else:
            super().wheelEvent(ev)


    def update_object(self,object):
        coord = object["coord"]
        # class_name = object["class"]
        x, y, z, l, w, h, angle = coord["x"], coord["y"], coord["z"], coord["l"], coord["w"], coord["h"], coord["angle"]
        # x, y, z = x + l / 2, y + w / 2, z + h / 2
        cubegl_object = self.create_3d_cube([x, y, z], [l, w, h], angle)
        self.addItem(cubegl_object)
        object["3d_object_2"] = cubegl_object

    def synchronize_3d_object(self, object):
        object_3d = object["3d_object_2"]
        new_coords = object["coord"]
        meshdata = self.create_meshdata(coords = new_coords)
        object_3d.setMeshData(**meshdata)

    def create_meshdata(self, coords):
        x = coords["x"]
        y = coords["y"]
        z = coords["z"]
        length = coords["l"]
        width = coords["w"]
        depth = coords["h"]
        angle = coords["angle"]

        cubegl = self.create_3d_cube([x, y, z], [length, width , depth], angle)
        new_meshdata = cubegl.opts["meshdata"]
        meshdata_dict = {"meshdata": new_meshdata}
        return meshdata_dict

    def change_threshold(self, value):
        self.threshold = value

        data = self.parent().data
        if not(data is None):
            pcd_object = [object for object in self.items if isinstance(object, gl.GLScatterPlotItem)]

            self.removeItem(pcd_object[0])

            ptcld,_ = pointcloud_coords_generation(data, threshold= self.threshold)
            pcd_object = gl.GLScatterPlotItem(pos=ptcld[:, :3], color=(1, 0, 1, 1), size=1)
            self.parent().pointcloud_data = ptcld
            self.addItem(pcd_object)
        else:
            print("Артем не крути ручки, пока не добавил облака")

    def create_3d_cube(self, pos, size, angle=0):
        if len(pos) == 2:
            x, y = pos
            l, w = size
            z = 5
            d = 10
        else:
            x,y,z = pos
            l,w,d = size

        x_top = x + l / 2
        x_bot = x - l / 2
        y_top = y + w / 2
        y_bot = y - w / 2
        z_top = z + d/2
        z_bot = z - d/2
        # x_top = x + l
        # x_bot = x
        # y_top = y + w
        # y_bot = y
        # z_top = z + d
        # z_bot = z
        # Todo check

        corners = [[x_top, y_bot, z_bot],
                   [x_bot, y_bot, z_bot],
                   [x_bot, y_top, z_bot],
                   [x_bot, y_bot, z_top],
                   [x_top, y_top, z_bot],
                   [x_top, y_top, z_top],
                   [x_bot, y_top, z_top],
                   [x_top, y_bot, z_top]]
        corners = np.array(corners)

        angle = angle * np.pi / 180
        Rotational_matrix = np.array([[np.cos(angle), np.sin(angle), 0]
                                         , [-np.sin(angle), np.cos(angle), 0]
                                         , [0, 0, 1]])

        # corners[:, 0] -= x - l / 2
        # corners[:, 1] -= y - w / 2

        corners = corners.dot(Rotational_matrix)

        # corners[:, 0] += x - l / 2
        # corners[:, 1] += y - w / 2

        vertexes = np.array([[1, 0, 0],  # 0
                             [0, 0, 0],  # 1
                             [0, 1, 0],  # 2
                             [0, 0, 1],  # 3
                             [1, 1, 0],  # 4
                             [1, 1, 1],  # 5
                             [0, 1, 1],  # 6
                             [1, 0, 1]])  # 7

        faces = np.array([[1, 0, 7], [1, 3, 7],
                          [1, 2, 4], [1, 0, 4],
                          [1, 2, 6], [1, 3, 6],
                          [0, 4, 5], [0, 7, 5],
                          [2, 4, 5], [2, 6, 5],
                          [3, 6, 5], [3, 7, 5]])

        Cube = gl.GLMeshItem(vertexes=corners, faces=faces, faceColors=(0.3, 0.3, 0.7, 0.1), drawEdges=True,
                             drawFaces=True)

        return Cube

    def highlight_selected(self):
        for item in self.items:
            if isinstance(item, gl.GLMeshItem):
                if (item in self.current_selected):
                    item.opts["edgeColor"] = (0,0,1,0.6)
                else:
                    item.opts["edgeColor"] = (1,1,1,1)
        self.update()

    def translate_object(self, object_list ,  sign):
        if (sign != 0) and (len(object_list) > 0 ):
            for item in self.items:
                if isinstance(item, gl.GLMeshItem) and (item in object_list):
                    idx = [item["3d_object_2"] for item in self.objects].index(item)
                    coords = self.objects[idx]["coord"] # coords in self.parent().object overriding
                    coords["z"] -= sign/abs(sign)*0.5
                    meshdata = self.create_meshdata(coords=coords)
                    item.setMeshData(**meshdata)
            self.SigChanged3dObject.emit(idx)
            self.update()

    def scale_object(self, object_list,  sign):
        if sign != 0 and len(object_list) != 0:
            for item in self.items:
                if isinstance(item, gl.GLMeshItem) and (item in object_list):
                    # item.scale(1,1,sign/abs(sign)*0.01+1)
                    #or
                    idx = [item["3d_object_2"] for item in self.objects].index(item)
                    coords = self.objects[idx]["coord"]
                    coords["h"] -= sign / abs(sign) * 0.5
                    meshdata = self.create_meshdata(coords=coords)
                    item.setMeshData(**meshdata)

            self.SigChanged3dObject.emit(idx)
            self.update()

    def rotate_object(self, object_list,  sign):
        if sign != 0 and len(object_list) != 0:
            for item in self.items:
                if isinstance(item, gl.GLMeshItem) and (item in object_list):
                    idx = [item["3d_object_2"] for item in self.objects].index(item)
                    coords = self.objects[idx]["coord"]
                    coords["angle"] -= sign / abs(sign) * 10
                    coords["angle"]  = coords["angle"]%360
                    meshdata = self.create_meshdata(coords=coords)
                    item.setMeshData(**meshdata)
            self.SigChanged3dObject.emit(idx)
            self.update()

    def transform_pointcloud(self, points):
        # maybe deprecated
        point_x_max = np.max(points[:, 0])
        point_y_max = np.max(points[:, 1])
        point_z_max = np.max(points[:, 2])

        points[:, 0] = points[:, 0] * (self.max_range[0] / point_x_max)
        points[:, 1] = points[:, 1] * (self.max_range[1] / point_y_max)
        points[:, 2] = points[:, 2] * (self.max_range[2] / point_z_max)

        return points

    def create_cube_for_test(self):
        coord = {"x":0, "y": 0, "z": 0, "l": 10, "w":10 , "h": 10, "angle":0}
        object = {"coord": coord}
        self.objects.append(object)
        self.update_object(object)

    def change_view(self):
        print("this params were:", self.opts)
        print("viewport = ", self.getViewport())
        print("camera position: ", self.cameraPosition())
        # print("change to another")
        self.setCameraPosition(elevation= -90, azimuth= 0)
        self.opts["center"] = QVector3D(0,0,10)
        # print("this params were:", self.opts)
        self.update()

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    wind = QtWidgets.QWidget()

    layout = QtWidgets.QVBoxLayout()
    but_layout = QtWidgets.QHBoxLayout()


    canvas = Volumetric_widget_BEV(dev_mode= "solo")


    # canvas = Bev_Canvas_2(dev_mode = "SOLO")
    layout.addWidget(canvas)

    # create_roi_but = QtWidgets.QPushButton("CREATE ROI")
    # create_roi_but.clicked.connect(canvas.create_obj)
    # but_layout.addWidget(create_roi_but)
    # print_roi_but = QtWidgets.QPushButton("Print info")
    # print_roi_but.clicked.connect(canvas.print_info)
    # but_layout.addWidget(print_roi_but)
    # sync_roi_but = QtWidgets.QPushButton("lets move")
    # sync_roi_but.clicked.connect(canvas.check_synchro)
    # but_layout.addWidget(sync_roi_but)
    # select_roi_but = QtWidgets.QPushButton("lets select")
    # select_roi_but.clicked.connect(canvas.check_select)
    # but_layout.addWidget(select_roi_but)
    # layout.addLayout(but_layout)


    wind.setLayout(layout)

    wind.show()
    sys.exit(app.exec())
