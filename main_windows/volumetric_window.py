from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import numpy as np
import pyqtgraph.opengl as gl

from libs.visualization import pointcloud_coords_generation

class Volumetric_widget_2(gl.GLViewWidget):

    SigCreate3dObject = pyqtSignal()
    SigSelect3dObject = pyqtSignal(str)
    SigChanged3dObject = pyqtSignal(int)
    SigDelete3dObject = pyqtSignal()

    def __init__(self, dev_mode = None, *args, **kwargs):

        self.dev_mode = dev_mode
        self.scale = 1.0

        super(Volumetric_widget_2, self).__init__(*args, **kwargs)

        self.noRepeatKeys = [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down,
                             QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown, QtCore.Qt.Key_W, QtCore.Qt.Key_Q,
                             QtCore.Qt.Key_S, QtCore.Qt.Key_A, QtCore.Qt.Key_D, QtCore.Qt.Key_E]
        # self.keysPressed = {}
        # self.keyTimer = QtCore.QTimer()
        # self.keyTimer.timeout.connect(self.evalKeyState)

        axis_qt = gl.GLAxisItem()
        grid3d_qt = gl.GLGridItem()
        # grid3d_qt.setSize(size=QtGui.QVector3D(ptcld[:, 0].max() * 2, ptcld[:, 1].max() * 2, ptcld[:, 2].max()))

        self.addItem(grid3d_qt)
        self.addItem(axis_qt)

        self.mousePos = QtCore.QPoint(0,0)

        self.setMouseTracking(True)

        self.current_selected = []

        self.threshold = 0.5

        self.objects = self.parent().objects
        self.selected_object_idxs = self.parent().selected_objects_idxs

        # if (self.dev_mode is None):
        #     print("created so")
        #
        # else:
        #     print("created soso")
        #     self.objects = []
        #     self.selected_object_idxs = []


    def mouseMoveEvent(self, ev):

        # super().mouseMoveEvent(ev)

        diff = ev.pos() - self.mousePos
        self.mousePos = ev.pos()

        if (self.parent() is not None) and hasattr(self.parent(),"change_status"):
            self.parent().change_status(''.join(["event in 3d widget:", str(ev.pos().x()), " ", str(ev.pos().y())]))

        if ev.buttons() == QtCore.Qt.LeftButton:
            if (ev.modifiers() == QtCore.Qt.ControlModifier):
                if (self.parent() is not None) and hasattr(self.parent(), "change_status"):
                    self.parent().change_status(
                    ''.join(["event in 3d widget:", str(ev.pos().x()), " ", str(ev.pos().y()), "translate mode"]))
                # self.translate_object(self.parent().selected_boxes, diff.x())
                #self.translate_object(self.current_selected, diff.x()) deprecated use mouse wheel
            elif (ev.modifiers() == QtCore.Qt.ShiftModifier):
                if (self.parent() is not None) and hasattr(self.parent(), "change_status"):
                    self.parent().change_status(
                    ''.join(["event in 3d widget:", str(ev.pos().x()), " ", str(ev.pos().y()), "scale mode"]))
                #self.scale_object(self.current_selected, diff.x()) deprecated use mouse wheel

            else:
                self.orbit(-diff.x(), diff.y())

                if (self.parent() is not None) and hasattr(self.parent(), "change_status"):
                    self.parent().change_status(''.join(["event in 3d widget:", str(ev.pos().x()), " ", str(ev.pos().y()), "orbit"]))
            # print self.opts['azimuth'], self.opts['elevation']
        elif ev.buttons() == QtCore.Qt.MidButton:
            if (ev.modifiers() & QtCore.Qt.ControlModifier):
                self.pan(diff.x(), 0, diff.y(), relative=True)
            else:
                self.pan(diff.x(), diff.y(), 0, relative=True)

            #TODO разобраться с наследованием функций

    def mousePressEvent(self, ev):
        if ev.buttons() == Qt.LeftButton:
            # selected_objects = [self.objects[idx]["3d_object"] for idx in self.selected_object_idxs]
            if  ev.modifiers() == QtCore.Qt.ShiftModifier:
                print("режим множественного выделения")
                new_objects = self.itemsAt([ev.pos().x(), ev.pos().y(), 1,1])

                for object in new_objects:
                    if isinstance(object, gl.GLMeshItem):
                        if object in self.current_selected:
                            self.current_selected.discard(object)
                        else:
                            self.current_selected.add(object)
                        # if object in []
            else:
                new_selected_objects = self.itemsAt([ev.pos().x(), ev.pos().y(), 1, 1])

                self.current_selected = set([object for object in new_selected_objects if isinstance(object, gl.GLMeshItem)])

        self.SigSelect3dObject.emit("3d")
        self.highlight_object()

    def wheelEvent(self, ev):
        delta = ev.angleDelta()
        delta_value = delta.y()/120

        print("we are inside wheel event:", self.objects)

        if ev.modifiers() == QtCore.Qt.ShiftModifier:
            self.scale_object(self.current_selected, [0,0,delta_value])
        elif ev.modifiers() == QtCore.Qt.ControlModifier:
            self.translate_object(self.current_selected, [0,0,delta_value])
        elif ev.modifiers() == QtCore.Qt.AltModifier:
            delta_value = delta.x() / 120
            self.rotate_object(self.current_selected, delta_value)
        else:
            super().wheelEvent(ev)

    def keyPressEvent(self, ev):
        if ev.key() in self.noRepeatKeys:
            ev.accept()
            if ev.isAutoRepeat():
                return
            self.keysPressed[ev.key()] = 1
            self.evalKeyState()

    def keyReleaseEvent(self, ev):
        if ev.key() in self.noRepeatKeys:
            ev.accept()
            if ev.isAutoRepeat():
                return
            try:
                del self.keysPressed[ev.key()]
            except:
                self.keysPressed = {}
            self.evalKeyState()

    def evalKeyState(self):
        speed = 2.0
        if len(self.keysPressed) > 0:
            for key in self.keysPressed:
                if key == QtCore.Qt.Key_Right:
                    self.orbit(azim=-speed, elev=0)
                elif key == QtCore.Qt.Key_Left:
                    self.orbit(azim=speed, elev=0)
                elif key == QtCore.Qt.Key_Up:
                    self.orbit(azim=0, elev=-speed)
                elif key == QtCore.Qt.Key_Down:
                    self.orbit(azim=0, elev=speed)
                elif key == QtCore.Qt.Key_PageUp:
                    pass
                elif key == QtCore.Qt.Key_PageDown:
                    pass
                elif key == QtCore.Qt.Key_W:
                    self.translate_object(self.current_selected, [speed, 0,0])
                elif key == QtCore.Qt.Key_S:
                    self.translate_object(self.current_selected, [-speed, 0, 0])
                elif key == QtCore.Qt.Key_A:
                    self.translate_object(self.current_selected, [0, speed, 0])
                elif key == QtCore.Qt.Key_D:
                    self.translate_object(self.current_selected, [0, -speed, 0])
                elif key == QtCore.Qt.Key_Q:
                    self.translate_object(self.current_selected, [0, 0, speed])
                elif key == QtCore.Qt.Key_E:
                    self.translate_object(self.current_selected, [0, 0, -speed])
                self.keyTimer.start(16)
        else:
            self.keyTimer.stop()



    def update_object(self,object):
        coord = object["coord"]
        # class_name = object["class"]
        x, y, z, l, w, h, angle = coord["x"], coord["y"], coord["z"], coord["l"], coord["w"], coord["h"], coord["angle"]
        # x, y, z = x + l / 2, y + w / 2, z + h / 2
        cubegl_object = self.create_3d_cube([x, y, z], [l, w, h], angle)
        self.addItem(cubegl_object)
        object["3d_object"] = cubegl_object

    def synchronize_3d_object(self, object):
        object_3d = object["3d_object"]
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

    def highlight_object(self):
        for item in self.items:
            if isinstance(item, gl.GLMeshItem):
                if (item in self.current_selected):
                    item.opts["edgeColor"] = (0,0,1,0.6)
                else:
                    item.opts["edgeColor"] = (1,1,1,1)
        self.update()

    # def translate_object(self, object_list , sign):
    #     if (sign != 0) and (len(object_list) > 0):
    #         for item in self.items:
    #             if isinstance(item, gl.GLMeshItem) and (item in object_list):
    #                 # item.translate(0,0,-sign/abs(sign)*0.5)
    #                 #or
    #                 idx = [item["3d_object"] for item in self.objects].index(item)
    #                 coords = self.objects[idx]["coord"] # coords in self.parent().object overriding
    #                 coords["z"] -= sign/abs(sign)*0.5
    #                 meshdata = self.create_meshdata(coords=coords)
    #                 item.setMeshData(**meshdata)
    #         self.SigChanged3dObject.emit(idx)
    #         self.update()

    def translate_object(self, object_list , values):
        #version_2.0
        if ( any([i!= 0 for i in values])) and (len(object_list) > 0) and (len(values) == 3):
            for item in self.items:
                if isinstance(item, gl.GLMeshItem) and (item in object_list):
                    idx = [item["3d_object"] for item in self.objects].index(item)
                    coords = self.objects[idx]["coord"] # coords in self.parent().object overriding
                    if values[0] != 0:
                        coords["x"] -= values[0]/abs(values[0])
                    if values[1] != 0:
                        coords["y"] -= values[1]/abs(values[1])
                    if values[2] != 0:
                        coords["z"] -= values[2]/abs(values[2])
                    meshdata = self.create_meshdata(coords=coords)
                    item.setMeshData(**meshdata)
            self.SigChanged3dObject.emit(idx)
            self.update()

    # def scale_object(self, object_list,  sign):
    #     if sign != 0 and len(object_list) != 0:
    #         for item in self.items:
    #             if isinstance(item, gl.GLMeshItem) and (item in object_list):
    #                 # item.scale(1,1,sign/abs(sign)*0.01+1)
    #                 #or
    #                 idx = [item["3d_object"] for item in self.objects].index(item)
    #                 coords = self.objects[idx]["coord"]
    #                 coords["h"] -= sign / abs(sign) * 0.5
    #                 meshdata = self.create_meshdata(coords=coords)
    #                 item.setMeshData(**meshdata)
    #
    #         self.SigChanged3dObject.emit(idx)
    #         self.update()

    def scale_object(self, object_list, values):
        # version_2.0
        if (any([i != 0 for i in values])) and (len(object_list) > 0) and (len(values) == 3):
            for item in self.items:
                if isinstance(item, gl.GLMeshItem) and (item in object_list):
                    idx = [item["3d_object"] for item in self.objects].index(item)
                    coords = self.objects[idx]["coord"]  # coords in self.parent().object overriding
                    if values[0] != 0:
                        coords["l"] -= values[0] / abs(values[0])
                    if values[1] != 0:
                        coords["w"] -= values[1] / abs(values[1])
                    if values[2] != 0:
                        coords["h"] -= values[2] / abs(values[2])
                    meshdata = self.create_meshdata(coords=coords)
                    item.setMeshData(**meshdata)
            self.SigChanged3dObject.emit(idx)
            self.update()

    def rotate_object(self, object_list,  sign):
        if sign != 0 and len(object_list) != 0:
            for item in self.items:
                if isinstance(item, gl.GLMeshItem) and (item in object_list):
                    idx = [item["3d_object"] for item in self.objects].index(item)
                    coords = self.objects[idx]["coord"]
                    coords["angle"] -= sign / abs(sign) * 10
                    coords["angle"]  = coords["angle"]%360
                    meshdata = self.create_meshdata(coords=coords)
                    item.setMeshData(**meshdata)
            self.SigChanged3dObject.emit(idx)
            self.update()

    def check_data(self):
        if self.parent().pointcloud_data is not None:
            print("Chtoto est")
            return True
        else:
            print("kazhis net")
            return False

    def transform_pointcloud(self, points):
        # maybe deprecated
        point_x_max = np.max(points[:, 0])
        point_y_max = np.max(points[:, 1])
        point_z_max = np.max(points[:, 2])

        points[:, 0] = points[:, 0] * (self.max_range[0] / point_x_max)
        points[:, 1] = points[:, 1] * (self.max_range[1] / point_y_max)
        points[:, 2] = points[:, 2] * (self.max_range[2] / point_z_max)

        return points

    def load_radar_pointcloud(self):

        if self.check_data():
            ptcld = self.parent().pointcloud_data
        else:
            data = np.load('data/18.npy')
            data = data[::2, ::2, ::2]
            ptcld, _ = pointcloud_coords_generation(frame=data)

        # ptcld = self.transform_pointcloud(ptcld)

        ptcld_qtobject = gl.GLScatterPlotItem(pos=ptcld[:, :3], color=(1, 0, 1, 1), size=1)

        # print("максиммальная дальность(x):", np.max(ptcld[:, 0])
        #     , "минимальная дальность(x):", np.min(ptcld[:, 0])
        #     , "максиммальный размах(y):",  np.max(ptcld[:, 1])
        #     ,"минимальный размах(y):",     np.min(ptcld[:, 1])
        #     , "максимальная высота(z):", np.max(ptcld[:,2])
        #     , "минимальная высота(z):", np.min(ptcld[:,2]))

        # self.threed_vis.addItem(grid3d_qt)
        # self.threed_vis.addItem(axis_qt)
        self.addItem(ptcld_qtobject)
        # self.main.addItem(ptcld_qtobject)

    def load_lidar_pointcloud(self):
        # print("loading lidar points")
        # ptcld = np.fromfile('data/1547131046260961.bin', dtype=np.float32).reshape((-1, 4)).astype(np.float64)
        ptcld = np.fromfile('data/example002.bin', dtype=np.float32).reshape((-1, 4)).astype(np.float64)

        ptcld[:, :3] = (ptcld[:, :3] - ptcld[:, :3].min()) / (ptcld[:, :3].max() - ptcld[:, :3].min())
        ptcld_qtobject = gl.GLScatterPlotItem(pos=ptcld[:, :3], color=(1, 1, 1, 1), size=1)
        self.addItem(ptcld_qtobject)


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
    mainwindow = QtWidgets.QWidget()
    ShareWidget = Volumetric_widget_2(parent=mainwindow, dev_mode='solo')
    widg = Volumetric_widget_2(parent = mainwindow, dev_mode = "solo")
    print("sharing ли widg? ", widg.isSharing())



    but_1 = QPushButton("create_box")
    but_1.clicked.connect(widg.create_cube_for_test)
    but_2 = QPushButton("highlight it!")
    but_2.clicked.connect(widg.change_view)
    but_3 = QPushButton("button_3")

    info_text = QtWidgets.QLabel("hoho")
    list_box = QtWidgets.QListWidget()
    list_box.setBaseSize(200,300)

    button_layout = QtWidgets.QHBoxLayout()
    button_layout.addWidget(but_1)
    button_layout.addWidget(but_2)
    button_layout.addWidget(but_3)

    main_layout = QtWidgets.QVBoxLayout()
    main_layout.addLayout(button_layout)
    main_layout.addWidget(widg,3)
    main_layout.addWidget(ShareWidget, 3)
    main_layout.addWidget(info_text)
    main_layout.addWidget(list_box)

    mainwindow.setLayout(main_layout)
    mainwindow.resize(1200,1200)

    mainwindow.show()

    sys.exit(app.exec())