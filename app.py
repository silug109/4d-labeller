import numpy.matlib as matlib
from math import sin, cos, atan2, sqrt
import random
# from window_2d import *
import numpy as np

from libs.canvas import Canvas
from main_windows.info_window import *

# from extra_windows import Pointcloud_Canvas


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

        self.selected_boxes = []
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


        from main_windows.volumetric_window import Volumetric_widget_2
        self.threed_vis = Volumetric_widget_2(self)
        # self.threed_vis.setMouseTracking(True)
        # self.threed_vis.main.resize(640,640)
        self.threed_vis.resize(640,640)

        self.canvas = Canvas(self)

        from main_windows.bev_window import Bev_Canvas_2
        self.bev_widget = Bev_Canvas_2(parent = self, dev_mode = "Main")
        # self.bev_widget.SigBevChange.connect(self.synchronize_all_widgets)
        self.bev_widget.SigBevChange.connect(self.synchronize_all_widgets)

        self.threed = QtWidgets.QPushButton('Load 3d')
        self.threed.clicked.connect(self.threed_vis.load_radar_pointcloud)

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
        # self.list_widget = QtWidgets.QListWidget(self)
        # self.list_widget.setSelectionMode( QtWidgets.QAbstractItemView.ExtendedSelection)
        # self.list_widget.SigSelectionChanged.connect(self.SignalListCheck)

        self.delete = QtWidgets.QPushButton('Delete selected')
        # self.delete.clicked.connect(self.delete_item)

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
        # print(len(self.pointcloud_data))


    def SignalListCheck(self):
        print("Update in list widget")

        SelectedListItems = self.list_widget.current_selected
        # print("In main: ",len(SelectedListItems))

        selected_idxs = []
        for ListItem in SelectedListItems:
            idx = [item["listitem"] for item in self.objects].index(ListItem)
            selected_idxs.append(idx)

        print(selected_idxs)

        self.update_selection(selected_idxs, source = "ListWidget")

    def Signal3DCheck(self):
        pass

    def SignalBevCheck(self, value):
        print("returned into main index: ",value)
        pass

    def update_selection(self, idxs, source = None):

        if source not in ["ListWidget", "threed_vis", "BevWidget"]:
            raise Exception

        self.selected_objects_idxs = idxs

        if source == "ListWidget":
            self.update_3d_boxes_selection(idxs)
            # self.update_3d_boxes(idxs)
            # self.bev_update(idxs)


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

    # def printoutboxes(self):
    #     list_bb = self.bev_view.addedItems
    #     if len(list_bb) > 1:
    #         print("There're some boxes Yo!")
    #
    #         for items in list_bb:
    #             if isinstance(items,pg.RectROI):
    #                 print(items.pos()[0], items.pos()[1], items.size()[0], items.size()[1])

    # def update_3d_boxes(self):
    #
    #     # for item in self.objects:
    #     #     if item["3d_object"] not in self.threed_vis.items:
    #     #         self.threed_vis.addItem(item["3d_object"])
    #
    #
    #     # print("СИНХРОНИЗАЦИЯ")
    #     list_bb = [item for item in self.threed_vis.items if isinstance(item, gl.GLMeshItem)]
    #     # print(list_bb)
    #
    #     for item in list_bb:
    #         self.threed_vis.removeItem(item)
    #
    #     for item in self.objects:
    #         self.threed_vis.addItem(item["3d_object"])
    #
    #     #
    #     # # list_bb = self.bev_widget.bev_view.addedItems
    #     # list_bb = [item[1] for item in self.objects]
    #     #
    #     # if len(list_bb) > 0:
    #     #     print("There're some boxes Yo!")
    #     #
    #     #     for items in list_bb:
    #     #         if isinstance(items, pg.RectROI):
    #     #             x,y,l,w = items.pos()[0], items.pos()[1], items.size()[0], items.size()[1]
    #     #             x,y = x+l/2, y+w/2
    #     #             cube_object = self.create_3d_cube([x,y], [l,w])
    #     #
    #     #             self.bev_lid_dict[items] = cube_object
    #     #             print(x,y,l,w)

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

    # def create_ROI(self):
    #
    #     bounding_box = pg.RectROI([10, 10], [20, 20], centered=True, sideScalers=True)
    #     bounding_box.addTranslateHandle([0.5, 0.5], [0.5, 0.5])
    #     bounding_box.addRotateHandle([0.5, 1.5], [0.5, 0.5])
    #
    #     # class_box = self.choose_class_for_box();
    #     class_box = "Cat"
    #
    #     # self.bev_view.addItem(bounding_box)
    #
    #     self.bev_widget.bev_view.addItem(bounding_box)
    #
    #     object_instance = {}
    #     object_instance["Bev_object"] = bounding_box
    #
    #     self.objects.append(object_instance)
    #
    #     self.update_db()
    #     # self.update_3d_boxes()
    #     # self.update_list_widget()
    #
    #     # self.objects.append((class_box, bounding_box))
    #
    #     # self.list_widget.addItem("Box" + str(len(self.objects)))
    #
    #     return bounding_box

    def update_one_object_db(self, object_ind):
        pass

    def update_db(self):

        for ind,item in enumerate(self.objects):
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

            item["coord"] = coord
            item["class"] = class_instance
            item["3d_object"] = cubegl_object
            item["id"] = id_instance
            # item["listitem"] = list_object
            item["listwidgetitem"] = myListWidgetObject
            item["listitem"] = ListWidgetItem
            item["IsSelected"] = False

            self.objects[ind] = item

            print("INIT: ",self.objects[ind])

    def update_all_widgets(self):
        pass


    def synchronize_all_widgets(self, obj_idx):
        # print(obj_idx)
        self.threed_vis.synchronize_3d_object(obj_idx)
        # self.bev_widget.synchronize_roi(obj_idx)
        self.list_widget.synchronizeListItem(obj_idx)
        # print(self.objects[obj_idx])
        pass

    # def update_list_widget(self):
    #     self.list_widget.clear()
    #     for ind,item in enumerate(self.objects):
    #         MyListWidgetObject = item["listwidgetitem"]
    #         ListWidgetItem = QtWidgets.QListWidgetItem(self.list_widget)
    #         ListWidgetItem.setSizeHint(MyListWidgetObject.sizeHint())
    #         self.list_widget.addItem(ListWidgetItem)
    #         self.list_widget.setItemWidget(ListWidgetItem, MyListWidgetObject)
    #         item["listitem"] = ListWidgetItem

    # def update_list_widget_selection(self):
    #     for idx in self.selected_objects_idxs:
    #         list_item = self.objects[idx]["listitem"]
    #         list_item.setSelected(True)
    #         list_ind = self.list_widget.row(list_item)
    #         list_instance = self.list_widget.item(list_ind)
    #         list_instance.setSelected(True)
    #
    # def delete_item(self):
    #
    #     for list_item in self.list_widget.selectedItems():
    #         self.list_widget.takeItem(self.list_widget.row(list_item))
    #
    #         # print(list_item)
    #         # print(self.objects)
    #
    #         # print([item["listitem"] for item in self.objects], list_item)
    #         object_ind = [item["listitem"] for item in self.objects].index(list_item)
    #
    #         object_2_del = self.objects.pop(object_ind)
    #
    #         # print(object_2_del["3d_object"])
    #         # print(self.threed_vis.items[object_ind[0]])
    #
    #         # print(object_2_del["Bev_object"])
    #         # print(self.bev_widget.bev_view.addedItems[object_ind[0]])
    #
    #         # self.threed_vis.items.pop(object_ind)
    #         self.bev_widget.bev_view.removeItem(object_2_del["Bev_object"])
    #
    #         self.threed_vis.removeItem(object_2_del["3d_object"])
    #
    # def select_item(self):
    #
    #     self.selected_boxes = []
    #
    #     for list_item in self.list_widget.selectedItems():
    #         object_tuple = self.objects[self.list_widget.row(list_item)]
    #
    #         self.selected_boxes.append(object_tuple["3d_object"])


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    main_window = mainwindows()

    # mainwindows.resize(1200,1200)
    main_window.show()
    sys.exit(app.exec())
