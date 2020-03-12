import numpy.matlib as matlib
from math import sin, cos, atan2, sqrt
import random
# from window_2d import *
import numpy as np


from libs.canvas import Canvas
from main_windows.info_window import *
from main_windows.bev_window import Bev_Canvas_2
from main_windows.volumetric_window import Volumetric_widget_2

from PyQt5.QtGui import QPixmap


def pointcloud_coords_generation(frame, range_max=67, azimuth_range_max=57, elevation_max=16):
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

def euler_to_so3(rpy):
    R_x = np.matrix([[1, 0, 0],
                     [0, cos(rpy[0]), -sin(rpy[0])],
                     [0, sin(rpy[0]), cos(rpy[0])]])
    R_y = np.matrix([[cos(rpy[1]), 0, sin(rpy[1])],
                     [0, 1, 0],
                     [-sin(rpy[1]), 0, cos(rpy[1])]])
    R_z = np.matrix([[cos(rpy[2]), -sin(rpy[2]), 0],
                     [sin(rpy[2]), cos(rpy[2]), 0],
                     [0, 0, 1]])
    R_zyx = R_z * R_y * R_x
    return R_zyx


def build_se3_transform(xyzrpy):
    se3 = matlib.identity(4)
    se3[0:3, 0:3] = euler_to_so3(xyzrpy[3:6])
    se3[0:3, 3] = np.matrix(xyzrpy[0:3]).transpose()
    return se3



class mainwindows(QtWidgets.QWidget):
# class mainwindows(QtWidgets.QMainWindow):

    max_range = [40,80,10]
    canvas_size = []
    lidar_view_size = []

    def __init__(self):

        self.objects = []

        # self.objects_dict = dict()
        # self.objects_dict.setdefault()

        self.filePath = None
        self.pointcloud_data = None
        self.image_data = None
        self.labels = None

        self.selected_objects = []
        self.selected_objects_idxs = []




        super(mainwindows,self).__init__()

        self.resize(1280,720)

        self.real_main_layout = QtWidgets.QVBoxLayout()

        self.menu = QtGui.QMenuBar(self)
        self.real_main_layout.addWidget(self.menu)

        file = self.menu.addMenu('&File')

        exitAction = QtWidgets.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(app.quit)
        file.addAction(exitAction)

        OpenFileAction = QtWidgets.QAction('&Open_file', self)
        OpenFileAction.setShortcut('Ctrl+N')
        OpenFileAction.setStatusTip('open new file to label')
        OpenFileAction.triggered.connect(app.quit)
        # OpenFileAction.triggered.connect(self.open_file)
        file.addAction(OpenFileAction)
        # TODO функция с загрузкой файлов


        transform = self.menu.addMenu('&Transform')

        LoadCalibAction = QtWidgets.QAction('&Calibration load', self)
        LoadCalibAction.setStatusTip('Exit application')
        LoadCalibAction.triggered.connect(app.quit)
        # LoadCalibAction.triggered.connect(self.load_calib)
        transform.addAction(LoadCalibAction)
        # TODO функция с калибровкой

        annotations = self.menu.addMenu('&Annotations')

        SaveAnnotationsAction = QtWidgets.QAction('&Save annotations', self)
        SaveAnnotationsAction.setStatusTip('Save annotations')
        SaveAnnotationsAction.triggered.connect(app.quit)
        # LoadCalibAction.triggered.connect(self.save_annotations)
        annotations.addAction(SaveAnnotationsAction)

        LoadAnnotationsAction = QtWidgets.QAction('&Load annotations', self)
        LoadAnnotationsAction.setStatusTip('Load annotations')
        LoadAnnotationsAction.triggered.connect(app.quit)
        # LoadCalibAction.triggered.connect(self.save_annotations)
        annotations.addAction(LoadAnnotationsAction)

        self.main_layout = QtWidgets.QHBoxLayout()

        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.showMessage("I'm")

        self.left_layout = QtWidgets.QVBoxLayout()
        self.right_layout = QtWidgets.QVBoxLayout()

        self.main_layout.addLayout(self.left_layout,2)
        self.main_layout.addLayout(self.right_layout)



        self.threed_vis = Volumetric_widget_2(self)
        self.threed_vis.resize(640,640)

        self.canvas = Canvas(self)


        self.bev_widget = Bev_Canvas_2(parent = self, dev_mode = "Main")
        self.bev_widget.SigBevChange.connect(self.synchronize_all_widgets_bev)
        # self.bev_widget.SigBevSelect.connect()

        self.threed = QtWidgets.QPushButton('Load 3d')
        self.threed.clicked.connect(self.threed_vis.load_radar_pointcloud)
        self.threed_vis.SigSelect3dObject.connect(self.update_selection)

        self.twod = QtWidgets.QPushButton('Load 2d')
        self.twod.clicked.connect(self.bev_widget.load_radar)

        self.camera = QtWidgets.QPushButton('Load image')
        # self.camera.clicked.connect(self.)

        self.start = QtWidgets.QPushButton('Start')
        # self.start.clicked.connect(self.printoutboxes)

        self.sync = QtWidgets.QPushButton('synchronize')
        # self.sync.clicked.connect(self.update_3d_boxes)

        self.create_ROI_but = QtWidgets.QPushButton('create ROI')
        self.create_ROI_but.clicked.connect(self.bev_widget.create_ROI)

        self.create_ROI_2 = QtWidgets.QPushButton('select')
        # self.create_ROI_2.clicked.connect(self.select_item)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.start)
        self.button_layout.addWidget(self.sync)
        self.button_layout.addWidget(self.create_ROI_but)
        self.button_layout.addWidget(self.create_ROI_2)

        self.button_layout_2 = QtWidgets.QHBoxLayout()
        self.button_layout_2.addWidget(self.threed)
        self.button_layout_2.addWidget(self.twod)
        self.button_layout_2.addWidget(self.camera)

        self.list_widget = ListWidg(self)
        self.list_widget.SigObjectChanged.connect(self.synchronize_all_widgets_list)
        self.list_widget.SigSelectionChanged.connect(self.update_selection)
        self.list_widget.SigObjectDeleted.connect(self.delete_objects_from_db)

        self.delete = QtWidgets.QPushButton('Delete selected')
        self.delete.clicked.connect(self.delete_selected_items)

        self.info = QtWidgets.QLabel("Nothing still")
        # from main_windows.info_window import InfoWidget
        # self.info_box = InfoWidget(self)

        self.button_layout_2 = QtWidgets.QHBoxLayout()
        self.button_layout_2.addWidget(self.threed)
        self.button_layout_2.addWidget(self.twod)
        self.button_layout_2.addWidget(self.camera)

        self.left_layout.addLayout(self.button_layout)
        self.left_layout.addWidget(self.threed_vis,2)
        self.left_layout.addLayout(self.button_layout_2)
        self.left_layout.addWidget(self.bev_widget,2)

        self.right_layout.addWidget(self.canvas)
        self.right_layout.addWidget(self.list_widget)
        self.right_layout.addWidget(self.delete)
        self.right_layout.addWidget(self.info)

        self.left_layout.addWidget(self.statusbar)

        self.real_main_layout.addLayout(self.main_layout)

        self.setLayout(self.real_main_layout)

        self.load_radar_poincloud()

        self.canvas.mode = self.canvas.CREATE

        image_pixmap = QPixmap('./data/0000000000.png')
        image_pixmap_resized = image_pixmap.scaled(640,480,QtCore.Qt.KeepAspectRatio)
        self.canvas.loadPixmap(image_pixmap_resized)

    def update_selection(self, source = None):

        #Todo Traceback (most recent call last): File "/home/cognitive-comp/Рабочий стол/things2watch/PYQT_experiments/app.py", line 247, in update_selection idx_selected = [item["3d_object"] for item in self.objects ].index(obj_3d) ValueError: <pyqtgraph.opengl.items.GLGridItem.GLGridItem object at 0x7f65f3d50828> is not in list

        print("ПРОИЗОШОЛ СЕЛЕКТ")

        if source == None:
            print("MDA NU I SHIT")
            return 0

        if source == "3d":

            current_selected = self.threed_vis.current_selected

            idxs = []

            for obj_3d in current_selected:
                idx_selected = [item["3d_object"] for item in self.objects ].index(obj_3d)
                idxs.append(idx_selected)

            self.selected_objects_idxs = idxs

            self.list_widget.current_selected = [self.objects[idx]["listitem"] for idx in self.selected_objects_idxs]
            self.list_widget.update_selection()

            print(self.selected_objects_idxs)


        if source == "list":

            current_selected = self.list_widget.current_selected

            idxs = []

            for selected_listitem in current_selected:

                # print(selected_listitem)
                # print(self.objects["listitem"])

                idx_selected = [item["listitem"] for item in self.objects].index(selected_listitem)
                idxs.append(idx_selected)

            self.selected_objects_idxs = idxs

            self.threed_vis.current_selected = [self.objects[idx]["3d_object"] for idx in self.selected_objects_idxs]
            self.threed_vis.highlight_object()


        # self.update_list_widget(idxs)
        # self.update_3d_boxes(idxs)
        # self.update_bev_boxes(idxs)


    def change_status(self,text):
        self.statusbar.showMessage(text)

    def change_random_status(self):
        random_text = ''.join([str(chr(random.randint(90,140))) for _ in range(20)])
        self.statusbar.showMessage(random_text)

    def load_radar_poincloud(self):
        '''
        загружаем в память основного класса облака точек.
        Подключаемые виджеты используют эти облака точек, а не по отдельности
        '''
        data = np.load('data/18.npy')
        data = data[::2, ::2, ::2]
        ptcld, _ = self.pointcloud_coords_generation(frame=data)
        self.pointcloud_data = ptcld
        pass

    def pointcloud_coords_generation(self,frame, range_max=67, azimuth_range_max=57, elevation_max=16):
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

    def load_lidar_pointcloud(self):
        '''
        загружаем в память основного класса облака точек.
        Подключаемые виджеты используют эти облака точек, а не по отдельности
        '''
        pass

    def reset(self):
        '''
        удаляет все объекты со всех виджетов.

        for widget in self.widgets:
            widget.reset()
        '''
        pass

    def create_3d_cube(self, pos, size, angle=0):
        return self.threed_vis.create_3d_cube(pos,size,angle)

    # def update_3d_boxes_selection(self, idxs):
    #     selected_object = [self.objects[idx]["3d_object"] for idx in idxs]
    #
    #     self.threed_vis.current_selected = selected_object
    #     self.threed_vis.highlight_object()
    #
    #     # for item in self.threed_vis.items:
    #     #     if isinstance(item, gl.GLMeshItem):
    #     #         if item in selected_object:
    #     #             item.opts["edgeColor"] = (0,0,1,0.6)
    #     #         else:
    #     #             item.opts["edgeColor"] = (1,1,1,1)
    #     # self.threed_vis.update()



    def update_one_object_db(self, object_ind):
        pass

    def update_db(self):

        print("всего объектов: ", len(self.objects))

        ind = len(self.objects) - 1
        item = self.objects[-1]

        bev_object = item["Bev_object"]
        x, y, l, w, angle = bev_object.pos()[0], bev_object.pos()[1], bev_object.size()[0], bev_object.size()[1], bev_object.angle()
        x, y = x + l / 2, y + w / 2
        cubegl_object = self.threed_vis.create_3d_cube([x, y], [l, w], angle)
        self.threed_vis.addItem(cubegl_object)

        coord = {"x":x, "y":y, "z":5, "l":l, "w":w, "h":10, "angle": angle}
        class_instance = "Cat"
        id_instance = "some_id"

        myListWidgetObject = QCustomQWidget()
        myListWidgetObject.setTextUp(id_instance)
        myListWidgetObject.setTextDown(str(coord))

        ListWidgetItem = QtWidgets.QListWidgetItem(self.list_widget)
        ListWidgetItem.setSizeHint(myListWidgetObject.sizeHint())
        self.list_widget.addItem(ListWidgetItem)
        self.list_widget.setItemWidget(ListWidgetItem, myListWidgetObject)
        #Todo change adding of listitem

        item["coord"] = coord
        item["class"] = class_instance
        item["3d_object"] = cubegl_object
        item["id"] = id_instance
        item["listwidgetitem"] = myListWidgetObject
        item["listitem"] = ListWidgetItem
        item["IsSelected"] = False

        self.objects[ind] = item

        print("INIT: ",self.objects[ind])

    def delete_objects_from_db(self, value):

        # parser of idx
        # idxs =

        print("emitted from function: ", value)
        print("Opa choto nado udalat")


    def delete_selected_items(self):
        print("Перед удалением объектов было: ", len(self.objects))

        for idx in self.selected_objects_idxs:
            selected_object = self.objects.pop(idx)

            selected_listitem = selected_object['listitem']
            self.list_widget.delete_item(selected_listitem)

            selected_3d = selected_object['3d_object']
            self.threed_vis.removeItem(selected_3d)
            # self.threed_vis.update()

            selected_roi = selected_object["Bev_object"]
            self.bev_widget.bev_view.removeItem(selected_roi)

            print("Во время удаления их становится: ", len(self.objects))





    def update_all_widgets(self):
        pass


    def synchronize_all_widgets_bev(self, obj_idx):
        self.threed_vis.synchronize_3d_object(obj_idx)
        # self.bev_widget.synchronize_roi(obj_idx)
        self.list_widget.synchronizeListItem(obj_idx)
        # print(self.objects[obj_idx])

    def synchronize_all_widgets_list(self, obj_idx):
        print(obj_idx)
        self.threed_vis.synchronize_3d_object(obj_idx)
        self.bev_widget.synchronize_roi(obj_idx)
        # print(self.objects[obj_idx])

    def synchronize_all_widgets_3d(self, obj_idx):
        # self.threed_vis.synchronize_3d_object(obj_idx)
        self.bev_widget.synchronize_roi(obj_idx)
        self.list_widget.synchronizeListItem(obj_idx)
        # print(self.objects[obj_idx])


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    main_window = mainwindows()

    # mainwindows.resize(1200,1200)
    main_window.show()
    sys.exit(app.exec())
