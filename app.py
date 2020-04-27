from libs.canvas import Canvas
from main_windows.info_window import *
from main_windows.bev_window import Bev_Canvas_2
from main_windows.volumetric_window import Volumetric_widget_2

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import *

import os
import glob
import json

from PIL import Image


def pointcloud_coords_generation(frame, range_max = 67, azimuth_range_max = 57, elevation_max = 16, threshold = 0.5):
    '''
    Generate poincloud coordinates, points color list from tensor contatining positional information of 3d scene
    :param
    frame: np.ndarray (config.size[1], size[2], config.size[3])
    range_max: int max range in meters for radar(should be config info)
    azimuth_range_max: int max azimuth in degrees for radar(should be in config info)
    elevation_max:int max elevation in degrees for radar(should be in  config info)
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

        self.canvas = Canvas(self) # widget for visualisation of images
        self.canvas.mode = self.canvas.CREATE

        self.bev_widget = Bev_Canvas_2(parent = self, dev_mode = "Main") # widget for visualisation of bird eye view
        self.bev_widget.SigBevChange.connect(self.synchronize_all_widgets_bev)
        # self.bev_widget.SigBevSelect.connect()

        #buttons
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

        self.create_ROI_2 = QtWidgets.QPushButton('Print info')
        # self.create_ROI_2.clicked.connect(self.print_info)
        self.create_ROI_2.clicked.connect(self.make_roi_selected)

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
        self.list_widget.SigObjectChanged.connect(self.synchronize_all_widgets_list)
        self.list_widget.SigSelectionChanged.connect(self.update_selection)
        self.list_widget.SigObjectDeleted.connect(self.delete_objects_from_db)

        self.delete = QtWidgets.QPushButton('Delete selected')
        self.delete.clicked.connect(self.delete_selected_items)

        self.button_layout_2 = QtWidgets.QHBoxLayout()
        self.button_layout_2.addWidget(self.threed)
        self.button_layout_2.addWidget(self.twod)
        self.button_layout_2.addWidget(self.camera)

        self.left_layout.addLayout(self.button_layout)
        self.left_layout.addWidget(self.threed_vis,2)
        self.left_layout.addLayout(self.button_layout_2)
        self.left_layout.addWidget(self.bev_widget,2)

        # self.right_splitter = QtWidgets.QSplitter(Qt.Vertical)
        # self.right_splitter.addWidget(self.canvas)
        # self.right_splitter.addWidget(self.list_widget)
        # self.right_layout.addWidget(self.right_splitter)

        self.right_layout.addWidget(self.canvas)
        self.right_layout.addWidget(self.list_widget)
        self.right_layout.addWidget(self.delete)

        self.left_layout.addWidget(self.statusbar)

        self.real_main_layout.addLayout(self.main_layout)

        self.setLayout(self.real_main_layout)

        self.load_radar_poincloud()

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


        myListWidgetObject, ListWidgetItem = self.list_widget.create_item()

        # myListWidgetObject = QCustomQWidget()
        myListWidgetObject.setTextUp(id_instance)
        myListWidgetObject.setTextDown(str(coord))

        # ListWidgetItem = QtWidgets.QListWidgetItem(self.list_widget)
        # ListWidgetItem.setSizeHint(myListWidgetObject.sizeHint())

        self.list_widget.add_item(ListWidgetItem, myListWidgetObject)
        # self.list_widget.addItem(ListWidgetItem)
        # self.list_widget.setItemWidget(ListWidgetItem, myListWidgetObject)
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
        print("inside synchronization")
        self.threed_vis.synchronize_3d_object(obj_idx)
        print("3d visualization:success")
        # self.bev_widget.synchronize_roi(obj_idx)
        self.list_widget.synchronizeListItem(obj_idx)
        print("list visualization:success")
        # print(self.objects[obj_idx])

    def synchronize_all_widgets_list(self, obj_idx):
        print("Изменение в ",obj_idx, " объекте в ListWidget")
        self.threed_vis.synchronize_3d_object(obj_idx)
        self.bev_widget.synchronize_roi(obj_idx)
        # print(self.objects[obj_idx])

    def synchronize_all_widgets_3d(self, obj_idx):
        # self.threed_vis.synchronize_3d_object(obj_idx)
        self.bev_widget.synchronize_roi(obj_idx)
        self.list_widget.synchronizeListItem(obj_idx)
        # print(self.objects[obj_idx])

    def make_roi_selected(self):
        pen = (0, 255, 0)
        for roi in self.bev_widget.bev_view.addedItems:
            roi.setPen(pen)
            # roi.setSelected(False)



    # Menu functions
    # FILE MENU
    def open_file(self):
        self.change_status("opening file")
        print("opening file")

        # dialog = QtWidgets.QFileDialog
        # fname = dialog.getOpenFileName(self, 'Open file', os.getcwd())[0]
        fname = "D:\Programming\Github\\4d-labeller\data\\18.npy"
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
        return pass

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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = mainwindows()
    # mainwindows.resize(1200,1200)
    main_window.show()
    sys.exit(app.exec())
