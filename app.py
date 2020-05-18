from libs.canvas import Canvas
from main_windows.info_window import *
from main_windows.bev_window import Bev_Canvas_2
from main_windows.volumetric_window import Volumetric_widget_2

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import *
from PyQt5 import QtWidgets

import os
import glob
import json
import copy

from PIL import Image

from libs.shape import Shape

from math import cos,sin,pi,tan

from libs.visualization import pointcloud_coords_generation


def euler_to_so3(rpy):
    '''
    create rotational part for transformation matrix
    :param rpy: list of int. contain 3 angles in rads
    :return: np.ndaarray(3,3)
    '''
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
    '''
    create transformation matrix Rotational part + Translate part
    :param xyzrpy: list of 6 int. first three coordinate if translation + 3 angles
    :return: np.ndarray(4,4)
    '''
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

        self.filePath = None
        self.pointcloud_data = None
        self.image_data = None
        self.image_pixmap = None
        # self.labels = None

        self.choose_file = False

        self.selected_objects_idxs = []

        self.data = None

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
        # OpenFileAction.triggered.connect(app.quit)
        OpenFileAction.triggered.connect(self.open_file)
        file.addAction(OpenFileAction)
        # TODO функция с загрузкой файлов


        transform = self.menu.addMenu('&Transform')

        LoadCalibAction = QtWidgets.QAction('&Calibration load', self)
        LoadCalibAction.setStatusTip('Exit application')
        # LoadCalibAction.triggered.connect(app.quit)
        LoadCalibAction.triggered.connect(self.load_calib)
        transform.addAction(LoadCalibAction)
        # TODO функция с калибровкой

        annotations = self.menu.addMenu('&Annotations')

        SaveAnnotationsAction = QtWidgets.QAction('&Save annotations', self)
        SaveAnnotationsAction.setStatusTip('Save annotations')
        # SaveAnnotationsAction.triggered.connect(app.quit)
        SaveAnnotationsAction.triggered.connect(self.save_annotations)
        annotations.addAction(SaveAnnotationsAction)

        LoadAnnotationsAction = QtWidgets.QAction('&Load annotations', self)
        LoadAnnotationsAction.setStatusTip('Load annotations')
        # LoadAnnotationsAction.triggered.connect(app.quit)
        LoadAnnotationsAction.triggered.connect(self.load_annotations)
        annotations.addAction(LoadAnnotationsAction)

        self.main_layout = QtWidgets.QHBoxLayout()

        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.showMessage("Nothing here still")

        self.left_layout = QtWidgets.QVBoxLayout()
        self.right_layout = QtWidgets.QVBoxLayout()

        self.main_layout.addLayout(self.left_layout,2)
        self.main_layout.addLayout(self.right_layout)

        self.threed_vis = Volumetric_widget_2(self) # widget for 3D visualisations
        # self.threed_vis.resize(640,640)
        self.threshold_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.threshold_slider.valueChanged.connect(self.threshold_change)

        self.canvas = Canvas(self) # widget for visualisation of images
        self.canvas.mode = self.canvas.CREATE
        self.checkbox_canvas_mode = QtWidgets.QCheckBox("create mode or draw mode")
        self.checkbox_canvas_mode.stateChanged.connect(self.changeModeCanvas)
        self.canvas.newShape.connect(self.new_shape_canvas)
        self.canvas.shapeMoved.connect(self.some_shape_moved)

        self.canvas_shape_create = QtWidgets.QPushButton("create shape")
        self.canvas_shape_create.clicked.connect(self.create_new_shape_canvas)

        self.canvas_shape_change = QtWidgets.QPushButton("change shape")
        # self.canvas_shape_change.clicked.connect(self.change_canvas_shape)
        self.canvas_shape_change.clicked.connect(self.make_shape_unvisible)
        self.canvas.shapeMoved.connect(self.print_info_if_shape_moved)



        self.bev_widget = Bev_Canvas_2(parent = self, dev_mode = "Main") # widget for visualisation of bird eye view
        self.bev_widget.SigBevChange.connect(self.synchronize_all_widgets)
        self.bev_widget.SigBevCreate.connect(self.true_update_db)

        #buttons
        self.threed = QtWidgets.QPushButton('Load 3d')
        self.threed.clicked.connect(self.threed_vis.load_radar_pointcloud)
        self.threed_vis.SigSelect3dObject.connect(self.update_selection)
        self.threed_vis.SigChanged3dObject.connect(self.synchronize_all_widgets)

        cam_object = self.create_camera_view_vis()
        self.threed_vis.addItem(cam_object)


        self.twod = QtWidgets.QPushButton('Load 2d')
        self.twod.clicked.connect(self.bev_widget.load_radar)

        self.camera = QtWidgets.QPushButton('Load image')
        # self.camera.clicked.connect(self.)

        self.start = QtWidgets.QPushButton('Start')
        # self.start.clicked.connect(self.printoutboxes)

        self.sync = QtWidgets.QPushButton('synchronize')
        # self.sync.clicked.connect(self.update_3d_boxes)

        self.create_ROI_but = QtWidgets.QPushButton('create ROI')
        self.create_ROI_but.clicked.connect(self.create_obj_main)

        self.create_ROI_2 = QtWidgets.QPushButton('Print info')
        # self.create_ROI_2.clicked.connect(self.print_info)
        # self.create_ROI_2.clicked.connect(self.print_coord_of_GLMESH)
        # self.create_ROI_2.clicked.connect(self.print_info_about_object)
        self.create_ROI_2.clicked.connect(self.filter_objects)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.start)
        self.button_layout.addWidget(self.sync)
        self.button_layout.addWidget(self.create_ROI_but)
        self.button_layout.addWidget(self.create_ROI_2)

        self.button_layout_2 = QtWidgets.QHBoxLayout()
        self.button_layout_2.addWidget(self.threed)
        self.button_layout_2.addWidget(self.twod)
        self.button_layout_2.addWidget(self.camera)

        self.list_widget = ListWidg(self) # widget for info visualisation about boxes
        # self.list_widget.SigObjectChanged.connect(self.synchronize_all_widgets_list)
        self.list_widget.SigObjectChanged.connect(self.synchronize_all_widgets)
        self.list_widget.SigSelectionChanged.connect(self.update_selection)
        self.list_widget.SigObjectDeleted.connect(self.delete_objects_from_db)
        # self.list_widget.SigCreateObject.connect(self.list_object_created)
        self.list_widget.SigCreateObject.connect(self.true_update_db)

        self.delete = QtWidgets.QPushButton('Delete selected')
        self.delete.clicked.connect(self.delete_selected_items)

        self.create_bb = QtWidgets.QPushButton("Create bbox")
        self.create_bb.clicked.connect(self.list_widget.create_new_bb_item)

        self.button_layout_2 = QtWidgets.QHBoxLayout()
        self.button_layout_2.addWidget(self.threed)
        self.button_layout_2.addWidget(self.twod)
        self.button_layout_2.addWidget(self.camera)

        self.left_layout.addLayout(self.button_layout)
        self.left_layout.addWidget(self.threed_vis,2)
        self.left_layout.addWidget(self.threshold_slider)
        self.left_layout.addLayout(self.button_layout_2)
        self.left_layout.addWidget(self.bev_widget,2)

        # self.right_splitter = QtWidgets.QSplitter(Qt.Vertical)
        # self.right_splitter.addWidget(self.canvas)
        # self.right_splitter.addWidget(self.list_widget)
        # self.right_layout.addWidget(self.right_splitter)

        self.right_layout.addWidget(self.checkbox_canvas_mode)
        self.right_layout.addWidget(self.canvas_shape_create)
        self.right_layout.addWidget(self.canvas_shape_change)
        self.right_layout.addWidget(self.canvas)
        self.right_layout.addWidget(self.list_widget)

        self.right_button_layout = QtWidgets.QHBoxLayout()
        self.right_button_layout.addWidget(self.delete)
        self.right_button_layout.addWidget(self.create_bb)
        self.right_layout.addLayout(self.right_button_layout)
        #or
        # self.right_layout.addWidget(self.delete)



        self.left_layout.addWidget(self.statusbar)

        self.real_main_layout.addLayout(self.main_layout)

        self.setLayout(self.real_main_layout)

        self.load_radar_poincloud()

        canvas_size = (340,480)
        null_image = np.zeros((340,480,3))
        null_image[30:340, 320:340, :] = 240

        null_Qimage = QtGui.QImage(null_image, null_image.shape[1], \
                             null_image.shape[0], null_image.shape[1] * 3, QtGui.QImage.Format_RGB888)
        null_pixmap = QtGui.QPixmap(null_Qimage)
        self.canvas.loadPixmap(null_pixmap)

        # self.scene.addPixmap(pix)

        # height, width, channel = null_image.shape
        # bytesPerLine = 3 * width
        # null_Qimage = QImage(null_image, width, height, bytesPerLine, QImage.Format_RGB888)
        # null_Qimage = QImage()
        # null_Qimage.loadFromData(null_image)

        # null_pixmap =  QPixmap(640,480)
        # null_pixmap.fromImage(null_Qimage)
        # print("null pixamap", null_pixmap.size().width(),null_pixmap.size().height() )
        # self.canvas.loadPixmap(null_pixmap)
        # image_pixmap = QPixmap('./data/0000000000.png')
        # image_pixmap_resized = image_pixmap.scaled(640,480,QtCore.Qt.KeepAspectRatio)
        # self.canvas.loadPixmap(image_pixmap_resized)

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

            self.bev_widget.currentSelected = [self.objects[idx]["Bev_object"] for idx in self.selected_objects_idxs]
            print("im here")
            self.bev_widget.highlight_selected()

            print(self.selected_objects_idxs)

        if source == "list":

            current_selected = self.list_widget.current_selected
            print("list selected: ", len(current_selected))

            idxs = []

            for selected_listitem in current_selected:

                # print(selected_listitem)
                # print(self.objects["listitem"])

                idx_selected = [item["listitem"] for item in self.objects].index(selected_listitem)
                idxs.append(idx_selected)

            self.selected_objects_idxs = idxs

            self.threed_vis.current_selected = [self.objects[idx]["3d_object"] for idx in self.selected_objects_idxs]
            self.threed_vis.highlight_object()

            self.bev_widget.currentSelected = [self.objects[idx]["Bev_object"] for idx in self.selected_objects_idxs]
            self.bev_widget.highlight_selected()


        # self.update_list_widget(idxs)
        # self.update_3d_boxes(idxs)
        # self.update_bev_boxes(idxs)

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

    def pointcloud_coords_generation(self,frame, range_max=67, azimuth_range_max=57, elevation_max=16, threshold = 0.5):
        '''
        :param frame: (config.size[1], size[2], config.size[3])
        :return: ndarray(num_points, 4)
        '''
        R = np.arange(0, range_max, range_max / frame.shape[0])
        theta = np.arange(-azimuth_range_max, azimuth_range_max, 2 * azimuth_range_max / frame.shape[1])
        epsilon = np.arange(0, elevation_max, elevation_max / frame.shape[2])

        theta_sin = np.sin(theta * np.pi / 180)
        theta_cos = np.cos(theta * np.pi / 180)
        epsilon_sin = np.sin(epsilon * np.pi / 180)
        epsilon_cos = np.cos(epsilon * np.pi / 180)

        tup_coord = np.nonzero(frame > threshold)

        x = np.expand_dims((R[tup_coord[0]] * theta_cos[tup_coord[1]] * epsilon_cos[tup_coord[2]]), 1)
        y = np.expand_dims((R[tup_coord[0]] * theta_sin[tup_coord[1]] * epsilon_cos[tup_coord[2]]), 1)
        z = np.expand_dims((R[tup_coord[0]] * epsilon_sin[tup_coord[2]]), 1)

        points = np.concatenate((x, y, z, np.expand_dims(frame[tup_coord], 1)), axis=1)

        points_cord = np.array(points)
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

    def update_one_object_db(self, object_ind):
        pass


    def true_update_db(self):
        # должен вызываться после создания в одном из виджетов объекта.

        # object = self.objects[idx]
        # or
        object = self.objects[-1]

        idx = len(self.objects)-1

        # # self.db_fields = ["coord", "class","Bev_object","3d_object", "id", "listwidgetitem", "listitem", "IsSelected"]
        # self.db_fields = ["Bev_object", "3d_object","listitem"]
        # # for field in self.db_fields:
        # #     if sel
        #
        if object.get("Bev_object") is None:
            print("Update db in bev widget")
            self.bev_widget.update_object(object)
            print(object)
        if object.get("3d_object") is None:
            print("Update db in 3d widget")
            self.threed_vis.update_object(object)
            print(object)
        if object.get("listitem") is None:
            print("update in list widget")
            self.list_widget.update_object(object)
        if object.get("Canvas_object") is None:
            print("update in canvas")
            self.update_canvas_shape(object)
        print(object)

    def create_obj_main(self):
        self.objects.append({"coord":{"x": 0, "y": 0, "z": 5, "l": 10, "w": 10, "h": 10, "angle": 0}, "id":"shit"})
        self.true_update_db()

    # def update_db(self):
    #
    #     print("всего объектов: ", len(self.objects))
    #
    #     ind = len(self.objects) - 1
    #     item = self.objects[-1]
    #
    #     bev_object = item["Bev_object"]
    #     x, y, l, w, angle = bev_object.pos()[0], bev_object.pos()[1], bev_object.size()[0], bev_object.size()[1], bev_object.angle()
    #     x, y = x + l / 2, y + w / 2
    #     cubegl_object = self.threed_vis.create_3d_cube([x, y], [l, w], angle)
    #     self.threed_vis.addItem(cubegl_object)
    #
    #     coord = {"x":x, "y":y, "z":5, "l":l, "w":w, "h":10, "angle": angle}
    #     class_instance = "Cat"
    #     id_instance = "some_id"
    #
    #
    #     myListWidgetObject, ListWidgetItem = self.list_widget.create_item()
    #
    #     # myListWidgetObject = QCustomQWidget()
    #     myListWidgetObject.setTextUp(id_instance)
    #     myListWidgetObject.setTextDown(str(coord))
    #
    #     # ListWidgetItem = QtWidgets.QListWidgetItem(self.list_widget)
    #     # ListWidgetItem.setSizeHint(myListWidgetObject.sizeHint())
    #
    #     self.list_widget.add_item(item = ListWidgetItem, item_object= myListWidgetObject)
    #     # self.list_widget.addItem(ListWidgetItem)
    #     # self.list_widget.setItemWidget(ListWidgetItem, myListWidgetObject)
    #     #Todo change adding of listitem
    #
    #     item["coord"] = coord
    #     item["class"] = class_instance
    #     item["3d_object"] = cubegl_object
    #     item["id"] = id_instance
    #     item["listwidgetitem"] = myListWidgetObject
    #     item["listitem"] = ListWidgetItem
    #     item["IsSelected"] = False
    #
    #     self.objects[ind] = item
    #
    #     print("INIT: ",self.objects[ind])

    def list_object_created(self):

        self.new_object = self.list_widget.object_instance
        print(f"inside main workflow, got {self.new_object['coord']}")
        print(self.new_object)

        coord = self.new_object['coord']
        x,y,z,l,w,h,angle = coord["x"],coord["y"],coord["z"],coord["l"],coord["w"],coord["h"],coord["angle"]
        print(x,y,z,l,w,h,angle)

        x, y, z = x + l / 2, y + w / 2, z + h/2

        cubegl_object = self.threed_vis.create_3d_cube([x, y, z], [l, w, h], angle)
        self.threed_vis.addItem(cubegl_object)

        bounding_box = pg.RectROI([x, y], [l, w], angle =  angle ,centered=True, sideScalers=True)
        bounding_box.addTranslateHandle([0.5, 0.5], [0.5, 0.5])
        bounding_box.addRotateHandle([0.5, 1.5], [0.5, 0.5])
        self.bev_widget.bev_view.addItem(bounding_box)


        item = self.new_object
        item["3d_object"] = cubegl_object
        item["Bev_object"] = bounding_box
        # item["id"] = id_instance
        # item["listwidgetitem"] = myListWidgetObject
        # item["listitem"] = ListWidgetItem
        item["IsSelected"] = False

        self.objects.append(item)
        pass


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

    def synchronize_all_widgets(self, obj_idx):
        object = self.objects[obj_idx]

        self.bev_widget.synchronize_object(object)
        self.threed_vis.synchronize_3d_object(object)
        self.list_widget.synchronizeListItem(object)
        self.synchronize_canvas_shape(object)
        self.test_all_objects_are_same()

    # Menu functions
    # FILE MENU

    def open_file(self):
        self.change_status("opening file")
        print("opening file")

        # dialog = QtWidgets.QFileDialog
        # fname = dialog.getOpenFileName(self, 'Open file', os.getcwd())[0]
        fname = "D:/Programming/Github/4d-labeller/data/18.npy"
        print("Selected file: ", fname)

        # print(f"SOMWTHING with {fname}")

        print(fname.rindex("/"))

        print("Base scene name: ", fname[fname.rindex("/")+1:fname.rindex(".")])

        scene_name = fname[fname.rindex("/")+1:fname.rindex(".")]
        directory_name = fname[:fname.rindex("/")]
        print(directory_name)

        self.filePath = f"{directory_name}/{scene_name}"

        for filename in glob.glob( f"{directory_name}/{scene_name}*"):
            print(filename)

            if filename.endswith(".png"):
                print("think, it is image")

                try:
                    img = Image.open(filename)
                except:
                    print("something wrong")
                    break

                self.image_data = np.array(img)
                print("Loaded image, ", type(self.image_data), self.image_data.shape)
                # self.image_pixmap = QPixmap(QImage().fromData(self.image_data))
                # self.image_pixmap = QPixmap().fromImage(QImage().fromData((self.image_data)))
                self.image_pixmap = QPixmap(filename)
                image_pixmap_resized = self.image_pixmap.scaled(640,480,QtCore.Qt.KeepAspectRatio)
                self.canvas.loadPixmap(image_pixmap_resized)
                print(image_pixmap_resized.size())
                # self.canvas.update()

            elif filename.endswith(".npy"):
                print("think, it is 3d points")
                data = np.load(filename)
                data = data[::2, ::2, ::2]
                ptcld, _ = self.pointcloud_coords_generation(frame=data)
                self.data = data
                self.pointcloud_data = ptcld
                self.threed_vis.load_radar_pointcloud()







        # fname = dialog.getOpenFileNames(self, 'Open file', os.getcwd())
        #
        # print("Selected: ", fname[0])
        #
        # for filename in fname[0]:
        #     print(filename, " is processing")
        #




        # with f:
        #     data = f.read()
        #     self.textEdit.setText(data)
        pass
    def open_files(self):
        pass

    #Transform menu
    def load_calib(self):
        self.change_status("loading calib")
        print("loading calib")

        dialog = QtWidgets.QFileDialog
        fname = dialog.getOpenFileNames(self, 'Open file', os.getcwd())

        pass
    #Annotation menu
    def save_annotations(self):
        self.change_status("saving annotations")

        if not(self.filePath is None):
            annotation_file = self.filepath+".json"
        else:
            annotation_file = "annotation.json"

        print(len(self.objects))

        objects_arr = []
        for object in self.objects:
            print(object)
            object_dict = {"coord":object["coord"], "class":object["class"]}
            objects_arr.append(object_dict)

        with open(annotation_file, "w") as file:
            json.dump(objects_arr, file)

        print("annotations saved")
        pass

    def load_annotations(self):
        self.change_status("loading annotations")
        print("loading annotations")

        if self.choose_file:
            dialog = QtWidgets.QFileDialog
            filename = dialog.getOpenFileNames(self, 'Open file', os.getcwd())
            if not(filename.endswith(".json")):
                print("Error, loading annotation.json")
                filename = "annotation.json"
        else:
            filename = "annotation.json"

        with open(filename, "r") as file:
            objects_dict = json.load(file)

        for object in objects_dict:
            item = {}
            coord_str = object['coord']
            x, y, z,  l, w, d, angle = coord_str.values()
            class_instance = object["class"]

            cubegl_object = self.threed_vis.create_3d_cube([x, y, z], [l, w, d], angle)
            self.threed_vis.addItem(cubegl_object)

            id_instance = "some_id"

            myListWidgetObject, ListWidgetItem = self.list_widget.create_item()

            myListWidgetObject.setTextUp(id_instance)
            myListWidgetObject.setTextDown(str(coord_str))
            self.list_widget.add_item(ListWidgetItem, myListWidgetObject)

            bounding_box = pg.RectROI([x, y], [l, w], angle = angle,centered=True, sideScalers=True)
            bounding_box.addTranslateHandle([0.5, 0.5], [0.5, 0.5])
            bounding_box.addRotateHandle([0.5, 1.5], [0.5, 0.5])
            self.bev_widget.bev_view.addItem(bounding_box)

            item["Bev_object"] = bounding_box
            item["coord"] = object["coord"]
            item["class"] = class_instance
            item["3d_object"] = cubegl_object
            item["id"] = id_instance
            item["listwidgetitem"] = myListWidgetObject
            item["listitem"] = ListWidgetItem
            item["IsSelected"] = False
            self.objects.append(item)
        return "success"

    # UTILS functions
    def change_status(self,text):
        self.statusbar.showMessage(text)

    def change_random_status(self):
        random_text = ''.join([str(chr(random.randint(90,140))) for _ in range(20)])
        self.statusbar.showMessage(random_text)

    def print_info(self):
        for object in self.objects:
            print("coords: ", object['coord'], " class: ",object["class"] )

    def print_coord_of_GLMESH(self):
        print(self.selected_objects_idxs)
        for object_idxs in self.selected_objects_idxs:
            object = self.objects[object_idxs]["3d_object"]
            print(object.vertexes, object)

    def print_info_about_object(self):
        print(len(self.canvas.shapes),self.canvas.shapes)

    def test_all_objects_are_same(self):
        objects_bev = copy.copy(self.bev_widget.objects)
        objects_3d = copy.copy(self.threed_vis.objects)
        objects_listwidget = copy.copy(self.list_widget.objects)
        objects_original = copy.copy(self.objects)
        # print("bev: ", objects_bev)
        # print("3d: ",objects_3d)
        # print("list: ",objects_listwidget)
        # print("original:", objects_original)
        print("are equal:", objects_original == objects_listwidget == objects_3d == objects_bev)




    #other functions to move to another libraries

    def create_camera_view_vis(self):
        fov = 90  # degrees
        elevation = 30
        distance = 100  # if needed
        angle = [0, 0]  # phi, theta
        pos_camera = [0, 10, 0]

        phi_right = (angle[0] - fov / 2) / 180 * pi
        phi_left = (angle[0] + fov / 2) / 180 * pi
        theta_bottom = (angle[1] - elevation / 2) / 180 * pi
        theta_up = (angle[1] + elevation / 2) / 180 * pi

        range_xy = [tan(phi_right), tan(phi_left)]
        range_yz = [tan(theta_bottom), tan(theta_up)]
        corners = [[0,0,0],
                   [distance, distance*range_xy[0], distance*range_yz[0]],
                   [distance, distance*range_xy[0], distance*range_yz[1]],
                   [distance, distance*range_xy[1], distance*range_yz[0]],
                   [distance, distance*range_xy[1], distance*range_yz[1]]]
        corners = np.array(corners)
        faces = np.array([[0,1,2],[0,2,3],[0,3,4],[0,4,1],[1,2,3],[2,3,4]])
        Camera_view = gl.GLMeshItem(vertexes=corners, faces=faces, faceColors=(0.3, 0.3, 0.7, 0.1), drawEdges=True,
                             drawFaces=False)
        return Camera_view

    def filter_objects(self, coords):
        fov = 90  # degrees
        elevation = 30
        distance = 100  # if needed
        angle = [0, 0]  # phi, theta
        pos_camera = [0, 10, 0]

        phi_right = (angle[0] - fov / 2) / 180 * pi
        phi_left = (angle[0] + fov / 2) / 180 * pi
        theta_bottom = (angle[1] - elevation / 2) / 180 * pi
        theta_up = (angle[1] + elevation / 2) / 180 * pi

        range_xy = [tan(phi_right), tan(phi_left)]
        range_xz = [tan(theta_bottom), tan(theta_up)]

        #     frame[:,1] y
        #     frame[:,2] z
        #
        # for object in self.objects:
        #     coords = object['coord']
        #     x = coords["x"]
        #     y = coords["y"]
        #     z = coords["z"]
        #
        #     if (y > range_xy[0]*x) and (y < range_xy[1]*x) and (z  > range_xz[0]*x) and (z < range_xz[1]*x):
        #         print(coords)


        x = coords["x"]
        y = coords["y"]
        z = coords["z"]

        if (y > range_xy[0]*x) and (y < range_xy[1]*x) and (z  > range_xz[0]*x) and (z < range_xz[1]*x):
            print(coords)
            return True
        return False

        # mask = (frame[:, 1] > range_xy[0] * frame[:, 0] +) * (frame[:, 1] < range_xy[1] * frame[:, 0]) * (
        #             frame[:, 2] > range_xz[0] * frame[:, 0]) * (frame[:, 2] < range_xz[1] * frame[:, 0])
        #
        # return frame[mask]

    def changeModeCanvas(self, state):
        self.change_status(f"state of checkbox has changed to {state == Qt.Checked}")
        self.canvas.setEditing(value = state)

        return "success"

    def threshold_change(self, value):
        self.change_status(f"value of threshold slider has changed to {value}")
        self.threed_vis.change_threshold(value)



    def new_shape_canvas(self):
        shape = self.canvas.shapes[-1]
        corners = [(item.x(), item.y()) for item in shape.points]
        width = abs(corners[0][0] - corners[1][0])
        height = abs(corners[0][1] - corners[2][1])
        cx  = corners[0][0] + width/2
        cy = corners[0][1] + height/2
        # print(width, height)

        default_length = 10
        default_angle = 0

        coords = {"x":0, "y": cx, "z": cy, "l": default_length, "w":width , "h": height, "angle":default_angle}

        object_instance = {}
        object_instance["Canvas_object"] = shape
        object_instance["coord"] = coords
        object_instance["id"] = "shit"
        self.objects.append(object_instance)
        self.true_update_db()
        #
        #
        # print(len(self.canvas.shapes), self.canvas.shapes)
        # for shape in self.canvas.shapes:
        #     print(shape.points)
        self.change_status(f"new shape created, do something")

    def update_canvas_shape(self, object):
        coords = object["coord"]

        x, y, z, l, w, h, angle = coords.values()

        canvas_size = (340, 480)

        pos = [y, z]
        size = [w, h]
        left_corner_1 = QPoint(canvas_size[0]/2 -  (pos[0] - size[0] / 2) ,canvas_size[1]/2 -  (pos[1] - size[1] / 2))
        left_corner_2 = QPoint(canvas_size[0]/2 -  (pos[0] - size[0] / 2), canvas_size[1]/2 -  (pos[1] + size[1] / 2))
        right_corner_1 = QPoint(canvas_size[0]/2 - (pos[0] + size[0] / 2), canvas_size[1]/2 -  (pos[1] - size[1] / 2))
        right_corner_2 = QPoint(canvas_size[0]/2 - (pos[0] + size[0] / 2), canvas_size[1]/2 -  (pos[1] + size[1] / 2))

        shape_instance = Shape()
        shape_instance.addPoint(left_corner_1)
        shape_instance.addPoint(right_corner_1)
        shape_instance.addPoint(right_corner_2)
        shape_instance.addPoint(left_corner_2)

        self.canvas.shapes.append(shape_instance)
        shape_instance.close()
        self.canvas.setHiding(False)
        # self.canvas.newShape.emit()
        self.canvas.update()

        object["Canvas_object"] = shape_instance




    def create_new_shape_canvas(self):

        canvas_size = (340, 480)

        pos = [100,100]
        size = [50,50]
        left_corner_1 = QPoint(canvas_size[0]/2 - (pos[0] - size[0] / 2), canvas_size[1]/2 - (pos[1] - size[1] / 2))
        left_corner_2 = QPoint(canvas_size[0]/2 - (pos[0] - size[0] / 2), canvas_size[1]/2 - (pos[1] + size[1] / 2))
        right_corner_1 = QPoint(canvas_size[0]/2 - (pos[0] + size[0] / 2), canvas_size[1]/2 - (pos[1] - size[1] / 2))
        right_corner_2 = QPoint(canvas_size[0]/2 - (pos[0] + size[0] / 2), canvas_size[1]/2 - (pos[1] + size[1] / 2))

        shape_instance  = Shape()
        shape_instance.addPoint(left_corner_1)
        shape_instance.addPoint(right_corner_1)
        shape_instance.addPoint(right_corner_2)
        shape_instance.addPoint(left_corner_2)

        self.canvas.shapes.append(shape_instance)
        shape_instance.close()
        self.canvas.setHiding(False)
        self.canvas.newShape.emit()
        self.canvas.update()

    def print_info_if_shape_moved(self):
        for shape in self.canvas.shapes:
            self.change_canvas_shape(shape)
        self.change_status("shape moved")

    def make_shape_unvisible(self):
        for shape in self.canvas.shapes:
            self.canvas.setShapeVisible(shape, False)
        self.canvas.repaint()
        print("made unvisible")

    def change_canvas_shape(self, shape):

        canvas_size = (340, 480)

        shape_coords = shape.points
        y = (shape_coords[0].x() + shape_coords[2].x())/2
        z = (shape_coords[0].y() + shape_coords[2].y())/2
        width = (shape_coords[0].x() - shape_coords[2].x())/ 2
        height = (shape_coords[0].y() - shape_coords[2].y()) / 2
        object = [object for object in self.objects if object["Canvas_object"] == shape][0]
        print("object:", object)
        print("objects:", self.objects)
        obj_idx = self.objects.index(object)
        coords = object["coord"]
        coords["y"] = y
        coords["z"] = z
        coords["w"] = width
        coords["h"] = height
        self.synchronize_all_widgets(obj_idx= obj_idx)

    def synchronize_canvas_shape(self, object):

        canvas_size = (340, 480)


        shape = object["Canvas_object"]
        coords = object["coord"]
        x,y,z,l,w,h,angle = coords.values()

        if self.filter_objects(coords):
            self.canvas.setShapeVisible(shape, True)
        else:
            self.canvas.setShapeVisible(shape, False)
        self.canvas.setShapeVisible(shape, self.filter_objects(coords))

        pos = [y, z]
        size = [w, h]
        left_corner_1 = QPoint(canvas_size[0]/2 - (pos[0] - size[0] / 2), canvas_size[1]/2 - (pos[1] - size[1] / 2))
        left_corner_2 = QPoint(canvas_size[0]/2 - (pos[0] - size[0] / 2), canvas_size[1]/2 - (pos[1] + size[1] / 2))
        right_corner_1 = QPoint(canvas_size[0]/2 - (pos[0] + size[0] / 2), canvas_size[1]/2 - (pos[1] - size[1] / 2))
        right_corner_2 = QPoint(canvas_size[0]/2 - (pos[0] + size[0] / 2), canvas_size[1]/2 - (pos[1] + size[1] / 2))
        shape.points = [left_corner_1, right_corner_1, right_corner_2, left_corner_2]
        # self.canvas.update()
        self.canvas.repaint()

    def highlight_select(self, object):
        shape = object["Canvas_object"]
        self.canvas.selectShape(shape)
        self.canvas.repaint()

    def some_shape_moved(self):
        self.change_status(f"shape has moved, do something")



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    # pg.dbg()
    main_window = mainwindows()
    main_window.show()
    sys.exit(app.exec())
