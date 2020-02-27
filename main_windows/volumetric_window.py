from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import numpy as np
import pyqtgraph.opengl as gl
import matplotlib.pyplot as plt


class Volumetric_widget_2(gl.GLViewWidget):
    def __init__(self, *args, **kwargs):
        self.scale = 1.0
        super(Volumetric_widget_2, self).__init__(*args, **kwargs)

        axis_qt = gl.GLAxisItem()
        grid3d_qt = gl.GLGridItem()
        # grid3d_qt.setSize(size=QtGui.QVector3D(ptcld[:, 0].max() * 2, ptcld[:, 1].max() * 2, ptcld[:, 2].max()))

        self.addItem(grid3d_qt)
        self.addItem(axis_qt)

        self.mousePos = QtCore.QPoint(0,0)

        self.setMouseTracking(True)

    def mouseMoveEvent(self, ev):

        # super().mouseMoveEvent(ev)



        diff = ev.pos() - self.mousePos
        self.mousePos = ev.pos()

        if (self.parent() is not None) and hasattr(self.parent(),"change_status"):
            self.parent().change_status(''.join(["event in 3d widget:", str(ev.pos().x()), " ", str(ev.pos().y())]))
        else:
            print(''.join(["event in 3d widget:", str(ev.pos().x()), " ", str(ev.pos().y())," ", str(diff.x())]))

            objecs = self.itemsAt([ev.pos().x(), ev.pos().y(),20,20])
            print("Тута есть обжектс", objecs)

        if ev.buttons() == QtCore.Qt.LeftButton:
            if (ev.modifiers() == QtCore.Qt.ControlModifier):

                if (self.parent() is not None) and hasattr(self.parent(), "change_status"):
                    self.parent().change_status(
                    ''.join(["event in 3d widget:", str(ev.pos().x()), " ", str(ev.pos().y()), "translate mode"]))
                # self.translate_object(self.parent().selected_boxes, diff.x())
                self.translate_object(self.objects_selected, diff.x())
            elif (ev.modifiers() == QtCore.Qt.ShiftModifier):

                # self.highlight_object(None)
                if (self.parent() is not None) and hasattr(self.parent(), "change_status"):
                    self.parent().change_status(
                    ''.join(["event in 3d widget:", str(ev.pos().x()), " ", str(ev.pos().y()), "scale mode"]))
                # print(diff.x())
                # self.scale_object(self.parent().selected_boxes, diff.x())
                self.scale_object(self.objects_selected, diff.x())

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
            self.objects_selected = self.itemsAt([ev.pos().x(), ev.pos().y(), 1,1])
            print("выделено объектов:", len(self.objects_selected))


    def update_3d_boxes(self):

        for item in self.main.items:
            if isinstance(item, gl.GLMeshItem):
                self.main.removeItem(item)

        list_bb = self.bev_view.addedItems
        if len(list_bb) > 1:
            print("There're some boxes Yo!")

            for items in list_bb:
                if isinstance(items, pg.RectROI):
                    x, y, l, w = items.pos()[0], items.pos()[1], items.size()[0], items.size()[1]
                    x, y = x + l / 2, y + w / 2
                    self.create_3d_cube([x, y], [l, w])
                    print(x, y, l, w)

    def create_3d_cube(self, pos, size):

        x, y = pos
        l, w = size

        x_top = x + l / 2
        x_bot = x - l / 2
        y_top = y + w / 2
        y_bot = y - w / 2
        z_top = 10
        z_bot = 0

        corners = []
        for i in [x_top, x_bot]:
            for j in [y_top, y_bot]:
                for k in [z_top, z_bot]:
                    corners.append([i, j, k])

        corners = [[x_top, y_bot, z_bot],
                   [x_bot, y_bot, z_bot],
                   [x_bot, y_top, z_bot],
                   [x_bot, y_bot, z_top],
                   [x_top, y_top, z_bot],
                   [x_top, y_top, z_top],
                   [x_bot, y_top, z_top],
                   [x_top, y_bot, z_top]]
        corners = np.array(corners)

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

        Cube = gl.GLMeshItem(vertexes=corners, faces=faces, faceColors=(1.0, 0, 0, 0.3), drawEdges=True)
        self.addItem(Cube)


    def select_objects(self):
        pass

    def highlight_object(self, object):
        for item in self.items:
            if isinstance(item, gl.GLMeshItem):
                item.opts["colors"] = (0,0,1,0.6)
        self.update()

    def translate_object(self, object_list ,  sign):
        if (sign != 0) and (len(object_list) > 0 ):
            for item in self.items:
                if isinstance(item, gl.GLMeshItem) and (item in object_list):
                    item.translate(0,0,-sign/abs(sign)*0.5)
            self.update()

    def scale_object(self, object_list ,  sign):
        if sign != 0 and len(object_list) != 0:
            for item in self.items:
                if isinstance(item, gl.GLMeshItem)  and (item in object_list):
                    item.scale(1,1,sign/abs(sign)*0.01+1)
            self.update()

    def check_data(self):
        if self.parent().pointcloud_data is not None:
            print("Chtoto est")
            return True
        else:
            print("kazhis net")
            return False

    def load_radar_pointcloud(self):

        if self.check_data():
            ptcld = self.parent().pointcloud_data
        else:
            data = np.load('data/18.npy')
            data = data[::2, ::2, ::2]
            ptcld, _ = self.pointcloud_coords_generation(frame=data)

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

        # ptcld = self.transform_pointcloud(ptcld)

        # ptcld = (ptcld - ptcld.min()) / (ptcld.max() - ptcld.min())
        # ptcld_color_norm = (ptcld[3] - ptcld[3].min()) / (ptcld[3].max() - ptcld[3].min())
        # ptcld__color = np.array([ptcld_color_norm, ptcld_color_norm, ptcld_color_norm, ptcld_color_norm])
        # ptcld_size = ptcld_color_norm
        # trans_matrix = build_se3_transform([0, 0, 0, np.pi, 0, -np.pi / 2])
        # ptcld[:, 3] = np.ones(ptcld[:, 3].shape)
        # ptcld = ptcld.dot(trans_matrix)
        ptcld_qtobject = gl.GLScatterPlotItem(pos=ptcld[:, :3], color=(1, 1, 1, 1), size=1)
        self.main.addItem(ptcld_qtobject)

    def transform_pointcloud(self, points):

        point_x_max = np.max(points[:, 0])
        point_y_max = np.max(points[:, 1])
        point_z_max = np.max(points[:, 2])

        points[:, 0] = points[:, 0] * (self.max_range[0] / point_x_max)
        points[:, 1] = points[:, 1] * (self.max_range[1] / point_y_max)
        points[:, 2] = points[:, 2] * (self.max_range[2] / point_z_max)

        return points

    def pointcloud_coords_generation(self, frame, range_max=67, azimuth_range_max=57, elevation_max=16):
        '''
        :param frame: (config.size[1], size[2], config.size[3])
        :return: ndarray(num_points, 4)
        '''
        R = np.arange(0, range_max, range_max / 512)
        theta = np.arange(-azimuth_range_max, azimuth_range_max, 2 * azimuth_range_max / 128)
        epsilon = np.arange(0, elevation_max, elevation_max / 40)

        points_cord = []
        for i in range(frame.shape[0]):
            for j in range(frame.shape[1]):
                for k in range(0, frame.shape[2] - 6):
                    if frame[i, j, k] > 0.1:
                        x = R[i] * np.cos(theta[j] * np.pi / 180) * np.cos(epsilon[k] * np.pi / 180)
                        y = R[i] * np.sin(theta[j] * np.pi / 180) * np.cos(epsilon[k] * np.pi / 180)
                        z = R[i] * np.sin(epsilon[k] * np.pi / 180)
                        points_cord.append([x, y, z, frame[i, j, k]])

        points_cord = np.array(points_cord)
        colors_arr = np.swapaxes(np.vstack((points_cord[:, 3], points_cord[:, 3], points_cord[:, 3])) / 255, 0, 1)
        return points_cord, colors_arr




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)



    mainwindow = QtWidgets.QWidget()
    widg = Volumetric_widget_2(mainwindow)
    widg.create_3d_cube((10,10),(20,20))
    widg.create_3d_cube((-110, 20), (20, 20))

    but_1 = QPushButton("button_1")
    # but_1.clicked.connect()
    but_2 = QPushButton("button_2")
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
    main_layout.addWidget(info_text)
    main_layout.addWidget(list_box)

    mainwindow.setLayout(main_layout)
    mainwindow.resize(1200,1200)

    mainwindow.show()

    sys.exit(app.exec())