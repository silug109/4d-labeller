from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import numpy as np

from libs.shape import Shape


CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor


def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())


class Bev_Canvas_2(pg.GraphicsView):

    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)

    CREATE, EDIT = list(range(2))

    epsilon = 11.0

    def __init__(self, dev_mode = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
    #     # Initialise local state.
    #     self.mode = self.EDIT
    #     self.shapes = []
    #     self.current = None
    #     self.selectedShape = None  # save the selected shape here
    #     self.selectedShapeCopy = None
    #     self.drawingLineColor = QColor(0, 0, 255)
    #     self.drawingRectColor = QColor(0, 0, 255)
    #     self.line = Shape(line_color=self.drawingLineColor)
    #     self.prevPoint = QPointF()
    #     self.offsets = QPointF(), QPointF()
    #     self.scale = 1.0
    #     self.pixmap = QPixmap()

        # self.bev_widget = pg.GraphicsView(self)
        # self.bev_widget.resize(640,640)

        self.bev_view = pg.ViewBox()
        self.addItem(self.bev_view)
        self.setCentralWidget(self.bev_view)

        y_axis_item = pg.AxisItem('top', showValues=False)
        y_axis_item.setStyle(tickTextHeight=1, tickTextWidth=1)
        y_axis_item.linkToView(self.bev_view)
        x_axis_item = pg.AxisItem('left', showValues=False)
        x_axis_item.setStyle(tickTextHeight=1, tickTextWidth=1)
        x_axis_item.linkToView(self.bev_view)
        self.bev_view.addItem(x_axis_item)
        self.bev_view.addItem(y_axis_item)

        self.dev_mode = dev_mode

        # self.load_radar()

        # self.visible = {}
        # self._hideBackround = False
        # self.hideBackround = False
        # self.hShape = None
        # self.hVertex = None
        # self._painter = QPainter()
        # self._cursor = CURSOR_DEFAULT
        # Menus:
        # self.menus = (QMenu(), QMenu())
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        # self.verified = False
        # self.drawSquare = False
    #
    # def enterEvent(self, ev):
    #     self.overrideCursor(self._cursor)
    #
    # def leaveEvent(self, ev):
    #     self.restoreCursor()
    #
    # def focusOutEvent(self, ev):
    #     self.restoreCursor()
    #
    # def isVisible(self, shape):
    #     return self.visible.get(shape, True)
    #
    # def drawing(self):
    #     return self.mode == self.CREATE
    #
    # def editing(self):
    #     return self.mode == self.EDIT
    #
    # def setEditing(self, value=True):
    #     self.mode = self.EDIT if value else self.CREATE
    #     if not value:  # Create
    #         self.unHighlight()
    #         self.deSelectShape()
    #     self.prevPoint = QPointF()
    #     self.repaint()


    def create_ROI(self):
        bounding_box = pg.RectROI([10, 10], [20, 20], centered= True, sideScalers=True)
        bounding_box.addScaleHandle([125,125],[25,25])
        # bounding_box.addTranslateHandle([0.5,0.5],[0.5,0.5])
        bounding_box.addRotateHandle([0.5, 1.5], [0.5, 0.5])
        # bounding_box.setZValue(20)

        # class_box = self.choose_class_for_box();
        class_box = "Cat"

        self.bev_view.addItem(bounding_box)
        return "Success"

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
        ptcld, _ = self.pointcloud_coords_generation(frame=data)
        xy = ptcld[:,0:2]

        return xy

    # def unHighlight(self):
    #     if self.hShape:
    #         self.hShape.highlightClear()
    #     self.hVertex = self.hShape = None
    #
    # def selectedVertex(self):
    #     return self.hVertex is not None


    def mouseMoveEvent(self, ev):
        super().mouseMoveEvent(ev)

        if (self.parent() is not None) and hasattr(self.parent(),"change_status"):
            self.parent().change_status(''.join(["event in bev widget:", str(ev.pos().x()), " ", str(ev.pos().y())]))

        rois = [item for item in self.bev_view.addedItems if isinstance(item,pg.RectROI)]


        for roi in rois:
            # if roi.isMoving:
            #     print("УГОЛ: ",roi.angle())

            print("pos:", roi.pos()[0]," ",roi.pos()[1]," size: ", roi.size()[0], " ", roi.size()[1], " angle ", roi.angle())
            ind = [item["Bev_object"] for item in self.parent().objects].index(roi)
            self.update_object_db(ind)

            self.parent().update_3d_boxes()

                # if self.dev_mode == "Main":
                #     ind =  [item["Bev_object"] for item in self.parent().objects].index(roi)
                #     print(ind)
                #     # ind =  [number for number,item in enumerate(self.parent().objects) if item["Bev_object"] == roi]
                #     if len(ind) != 0:
                #         self.update_object_db(ind[0])
                #
                #         self.parent().update_3d_boxes()
                #         # self.parent().update_list_widget()
            #TODO логику синхронизации переписать

    def update_object_db(self, object_ind):
        object = self.parent().objects[object_ind]

        bev_object = object["Bev_object"]
        x, y, l, w, angle = bev_object.pos()[0], bev_object.pos()[1], bev_object.size()[0], bev_object.size()[1], bev_object.angle()
        x, y = x + l / 2, y + w / 2 #RECT ROI x,y - left bottom points though move it to logical center
        cubegl_object = self.parent().create_3d_cube([x, y], [l, w], angle)

        coord = {"x": x, "y": y, "z": 5, "l": l, "w": w, "h": 10}

        object["coord"] = coord
        object["3d_object"] = cubegl_object
        self.parent().objects[object_ind] = object

    def reset(self):
        for item in self.bev_view.addedItems:
            print(item)



    # def mouseDragEvent(self, ev):
    #     super().mouseDragEvent(ev)
    #     self.parent().change_status(''.join([" Drag event in bev widget:", str(ev.pos().x()), " ", str(ev.pos().y())]))
    #
    #     rois = [item for item in self.bev_view.addedItems if isinstance(item, pg.RectROI)]
    #     # print(rois)
    #     for roi in rois:
    #         if roi.isMoving:
    #             print(roi, "is dragging")

    # def mousePressEvent(self, ev):
    #     pos = self.transformPos(ev.pos())
    #
    #     if ev.button() == Qt.LeftButton:
    #         if self.drawing():
    #             self.handleDrawing(pos)
    #         else:
    #             self.selectShapePoint(pos)
    #             self.prevPoint = pos
    #             self.repaint()
    #     elif ev.button() == Qt.RightButton and self.editing():
    #         self.selectShapePoint(pos)
    #         self.prevPoint = pos
    #         self.repaint()
    #
    # def mouseReleaseEvent(self, ev):
    #     if ev.button() == Qt.RightButton:
    #         menu = self.menus[bool(self.selectedShapeCopy)]
    #         self.restoreCursor()
    #         if not menu.exec_(self.mapToGlobal(ev.pos()))\
    #            and self.selectedShapeCopy:
    #             # Cancel the move by deleting the shadow copy.
    #             self.selectedShapeCopy = None
    #             self.repaint()
    #     elif ev.button() == Qt.LeftButton and self.selectedShape:
    #         if self.selectedVertex():
    #             self.overrideCursor(CURSOR_POINT)
    #         else:
    #             self.overrideCursor(CURSOR_GRAB)
    #     elif ev.button() == Qt.LeftButton:
    #         pos = self.transformPos(ev.pos())
    #         if self.drawing():
    #             self.handleDrawing(pos)
    #
    # def endMove(self, copy=False):
    #     assert self.selectedShape and self.selectedShapeCopy
    #     shape = self.selectedShapeCopy
    #     #del shape.fill_color
    #     #del shape.line_color
    #     if copy:
    #         self.shapes.append(shape)
    #         self.selectedShape.selected = False
    #         self.selectedShape = shape
    #         self.repaint()
    #     else:
    #         self.selectedShape.points = [p for p in shape.points]
    #     self.selectedShapeCopy = None
    #
    # def hideBackroundShapes(self, value):
    #     self.hideBackround = value
    #     if self.selectedShape:
    #         # Only hide other shapes if there is a current selection.
    #         # Otherwise the user will not be able to select a shape.
    #         self.setHiding(True)
    #         self.repaint()
    #
    # def handleDrawing(self, pos):
    #     if self.current and self.current.reachMaxPoints() is False:
    #         initPos = self.current[0]
    #         minX = initPos.x()
    #         minY = initPos.y()
    #         targetPos = self.line[1]
    #         maxX = targetPos.x()
    #         maxY = targetPos.y()
    #         self.current.addPoint(QPointF(maxX, minY))
    #         self.current.addPoint(targetPos)
    #         self.current.addPoint(QPointF(minX, maxY))
    #         self.finalise()
    #     elif not self.outOfPixmap(pos):
    #         self.current = Shape()
    #         self.current.addPoint(pos)
    #         self.line.points = [pos, pos]
    #         self.setHiding()
    #         self.drawingPolygon.emit(True)
    #         self.update()
    #
    # def setHiding(self, enable=True):
    #     self._hideBackround = self.hideBackround if enable else False
    #
    # def canCloseShape(self):
    #     return self.drawing() and self.current and len(self.current) > 2
    #
    # def mouseDoubleClickEvent(self, ev):
    #     # We need at least 4 points here, since the mousePress handler
    #     # adds an extra one before this handler is called.
    #     if self.canCloseShape() and len(self.current) > 3:
    #         self.current.popPoint()
    #         self.finalise()
    #
    # def selectShape(self, shape):
    #     self.deSelectShape()
    #     shape.selected = True
    #     self.selectedShape = shape
    #     self.setHiding()
    #     self.selectionChanged.emit(True)
    #     self.update()
    #
    # def selectShapePoint(self, point):
    #     """Select the first shape created which contains this point."""
    #     self.deSelectShape()
    #     if self.selectedVertex():  # A vertex is marked for selection.
    #         index, shape = self.hVertex, self.hShape
    #         shape.highlightVertex(index, shape.MOVE_VERTEX)
    #         self.selectShape(shape)
    #         return
    #     for shape in reversed(self.shapes):
    #         if self.isVisible(shape) and shape.containsPoint(point):
    #             self.selectShape(shape)
    #             self.calculateOffsets(shape, point)
    #             return
    #
    # def calculateOffsets(self, shape, point):
    #     rect = shape.boundingRect()
    #     x1 = rect.x() - point.x()
    #     y1 = rect.y() - point.y()
    #     x2 = (rect.x() + rect.width()) - point.x()
    #     y2 = (rect.y() + rect.height()) - point.y()
    #     self.offsets = QPointF(x1, y1), QPointF(x2, y2)
    #
    # def snapPointToCanvas(self, x, y):
    #     """
    #     Moves a point x,y to within the boundaries of the canvas.
    #     :return: (x,y,snapped) where snapped is True if x or y were changed, False if not.
    #     """
    #     if x < 0 or x > self.pixmap.width() or y < 0 or y > self.pixmap.height():
    #         x = max(x, 0)
    #         y = max(y, 0)
    #         x = min(x, self.pixmap.width())
    #         y = min(y, self.pixmap.height())
    #         return x, y, True
    #
    #     return x, y, False
    #
    # def boundedMoveVertex(self, pos):
    #     index, shape = self.hVertex, self.hShape
    #     point = shape[index]
    #     if self.outOfPixmap(pos):
    #         pos = self.intersectionPoint(point, pos)
    #
    #     if self.drawSquare:
    #         opposite_point_index = (index + 2) % 4
    #         opposite_point = shape[opposite_point_index]
    #
    #         min_size = min(abs(pos.x() - opposite_point.x()), abs(pos.y() - opposite_point.y()))
    #         directionX = -1 if pos.x() - opposite_point.x() < 0 else 1
    #         directionY = -1 if pos.y() - opposite_point.y() < 0 else 1
    #         shiftPos = QPointF(opposite_point.x() + directionX * min_size - point.x(),
    #                            opposite_point.y() + directionY * min_size - point.y())
    #     else:
    #         shiftPos = pos - point
    #
    #     shape.moveVertexBy(index, shiftPos)
    #
    #     lindex = (index + 1) % 4
    #     rindex = (index + 3) % 4
    #     lshift = None
    #     rshift = None
    #     if index % 2 == 0:
    #         rshift = QPointF(shiftPos.x(), 0)
    #         lshift = QPointF(0, shiftPos.y())
    #     else:
    #         lshift = QPointF(shiftPos.x(), 0)
    #         rshift = QPointF(0, shiftPos.y())
    #     shape.moveVertexBy(rindex, rshift)
    #     shape.moveVertexBy(lindex, lshift)
    #
    # def boundedMoveShape(self, shape, pos):
    #     if self.outOfPixmap(pos):
    #         return False  # No need to move
    #     o1 = pos + self.offsets[0]
    #     if self.outOfPixmap(o1):
    #         pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
    #     o2 = pos + self.offsets[1]
    #     if self.outOfPixmap(o2):
    #         pos += QPointF(min(0, self.pixmap.width() - o2.x()),
    #                        min(0, self.pixmap.height() - o2.y()))
    #     # The next line tracks the new position of the cursor
    #     # relative to the shape, but also results in making it
    #     # a bit "shaky" when nearing the border and allows it to
    #     # go outside of the shape's area for some reason. XXX
    #     #self.calculateOffsets(self.selectedShape, pos)
    #     dp = pos - self.prevPoint
    #     if dp:
    #         shape.moveBy(dp)
    #         self.prevPoint = pos
    #         return True
    #     return False
    #
    # def deSelectShape(self):
    #     if self.selectedShape:
    #         self.selectedShape.selected = False
    #         self.selectedShape = None
    #         self.setHiding(False)
    #         self.selectionChanged.emit(False)
    #         self.update()
    #
    # def deleteSelected(self):
    #     if self.selectedShape:
    #         shape = self.selectedShape
    #         self.shapes.remove(self.selectedShape)
    #         self.selectedShape = None
    #         self.update()
    #         return shape
    #
    # def copySelectedShape(self):
    #     if self.selectedShape:
    #         shape = self.selectedShape.copy()
    #         self.deSelectShape()
    #         self.shapes.append(shape)
    #         shape.selected = True
    #         self.selectedShape = shape
    #         self.boundedShiftShape(shape)
    #         return shape
    #
    # def boundedShiftShape(self, shape):
    #     # Try to move in one direction, and if it fails in another.
    #     # Give up if both fail.
    #     point = shape[0]
    #     offset = QPointF(2.0, 2.0)
    #     self.calculateOffsets(shape, point)
    #     self.prevPoint = point
    #     if not self.boundedMoveShape(shape, point - offset):
    #         self.boundedMoveShape(shape, point + offset)
    #
    # def paintEvent(self, event):
    #     if not self.pixmap:
    #         return super(Bev_Canvas, self).paintEvent(event)
    #
    #     p = self._painter
    #     p.begin(self)
    #     p.setRenderHint(QPainter.Antialiasing)
    #     p.setRenderHint(QPainter.HighQualityAntialiasing)
    #     p.setRenderHint(QPainter.SmoothPixmapTransform)
    #
    #     p.scale(self.scale, self.scale)
    #     p.translate(self.offsetToCenter())
    #
    #     p.drawPixmap(0, 0, self.pixmap)
    #     Shape.scale = self.scale
    #     for shape in self.shapes:
    #         if (shape.selected or not self._hideBackround) and self.isVisible(shape):
    #             shape.fill = shape.selected or shape == self.hShape
    #             shape.paint(p)
    #     if self.current:
    #         self.current.paint(p)
    #         self.line.paint(p)
    #     if self.selectedShapeCopy:
    #         self.selectedShapeCopy.paint(p)
    #
    #     # Paint rect
    #     if self.current is not None and len(self.line) == 2:
    #         leftTop = self.line[0]
    #         rightBottom = self.line[1]
    #         rectWidth = rightBottom.x() - leftTop.x()
    #         rectHeight = rightBottom.y() - leftTop.y()
    #         p.setPen(self.drawingRectColor)
    #         brush = QBrush(Qt.BDiagPattern)
    #         p.setBrush(brush)
    #         p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)
    #
    #     if self.drawing() and not self.prevPoint.isNull() and not self.outOfPixmap(self.prevPoint):
    #         p.setPen(QColor(0, 0, 0))
    #         p.drawLine(self.prevPoint.x(), 0, self.prevPoint.x(), self.pixmap.height())
    #         p.drawLine(0, self.prevPoint.y(), self.pixmap.width(), self.prevPoint.y())
    #
    #     self.setAutoFillBackground(True)
    #     if self.verified:
    #         pal = self.palette()
    #         pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
    #         self.setPalette(pal)
    #     else:
    #         pal = self.palette()
    #         pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
    #         self.setPalette(pal)
    #
    #     p.end()
    #
    # def transformPos(self, point):
    #     """Convert from widget-logical coordinates to painter-logical coordinates."""
    #     return point / self.scale - self.offsetToCenter()
    #
    # def offsetToCenter(self):
    #     s = self.scale
    #     area = super(Bev_Canvas, self).size()
    #     w, h = self.pixmap.width() * s, self.pixmap.height() * s
    #     aw, ah = area.width(), area.height()
    #     x = (aw - w) / (2 * s) if aw > w else 0
    #     y = (ah - h) / (2 * s) if ah > h else 0
    #     return QPointF(x, y)
    #
    # def outOfPixmap(self, p):
    #     w, h = self.pixmap.width(), self.pixmap.height()
    #     return not (0 <= p.x() <= w and 0 <= p.y() <= h)
    #
    # def finalise(self):
    #     assert self.current
    #     if self.current.points[0] == self.current.points[-1]:
    #         self.current = None
    #         self.drawingPolygon.emit(False)
    #         self.update()
    #         return
    #
    #     self.current.close()
    #     self.shapes.append(self.current)
    #     self.current = None
    #     self.setHiding(False)
    #     self.newShape.emit()
    #     self.update()
    #
    # def closeEnough(self, p1, p2):
    #     #d = distance(p1 - p2)
    #     #m = (p1-p2).manhattanLength()
    #     # print "d %.2f, m %d, %.2f" % (d, m, d - m)
    #     return distance(p1 - p2) < self.epsilon
    #
    # def intersectionPoint(self, p1, p2):
    #     # Cycle through each image edge in clockwise fashion,
    #     # and find the one intersecting the current line segment.
    #     # http://paulbourke.net/geometry/lineline2d/
    #     size = self.pixmap.size()
    #     points = [(0, 0),
    #               (size.width(), 0),
    #               (size.width(), size.height()),
    #               (0, size.height())]
    #     x1, y1 = p1.x(), p1.y()
    #     x2, y2 = p2.x(), p2.y()
    #     d, i, (x, y) = min(self.intersectingEdges((x1, y1), (x2, y2), points))
    #     x3, y3 = points[i]
    #     x4, y4 = points[(i + 1) % 4]
    #     if (x, y) == (x1, y1):
    #         # Handle cases where previous point is on one of the edges.
    #         if x3 == x4:
    #             return QPointF(x3, min(max(0, y2), max(y3, y4)))
    #         else:  # y3 == y4
    #             return QPointF(min(max(0, x2), max(x3, x4)), y3)
    #
    #     # Ensure the labels are within the bounds of the image. If not, fix them.
    #     x, y, _ = self.snapPointToCanvas(x, y)
    #
    #     return QPointF(x, y)
    #
    # def intersectingEdges(self, x1y1, x2y2, points):
    #     """For each edge formed by `points', yield the intersection
    #     with the line segment `(x1,y1) - (x2,y2)`, if it exists.
    #     Also return the distance of `(x2,y2)' to the middle of the
    #     edge along with its index, so that the one closest can be chosen."""
    #     x1, y1 = x1y1
    #     x2, y2 = x2y2
    #     for i in range(4):
    #         x3, y3 = points[i]
    #         x4, y4 = points[(i + 1) % 4]
    #         denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    #         nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
    #         nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
    #         if denom == 0:
    #             # This covers two cases:
    #             #   nua == nub == 0: Coincident
    #             #   otherwise: Parallel
    #             continue
    #         ua, ub = nua / denom, nub / denom
    #         if 0 <= ua <= 1 and 0 <= ub <= 1:
    #             x = x1 + ua * (x2 - x1)
    #             y = y1 + ua * (y2 - y1)
    #             m = QPointF((x3 + x4) / 2, (y3 + y4) / 2)
    #             d = distance(m - QPointF(x2, y2))
    #             yield d, i, (x, y)
    #
    # # These two, along with a call to adjustSize are required for the
    # # scroll area.
    # def sizeHint(self):
    #     return self.minimumSizeHint()
    #
    # def minimumSizeHint(self):
    #     if self.pixmap:
    #         return self.scale * self.pixmap.size()
    #     return super(Bev_Canvas, self).minimumSizeHint()
    #
    # def wheelEvent(self, ev):
    #     qt_version = 4 if hasattr(ev, "delta") else 5
    #     if qt_version == 4:
    #         if ev.orientation() == Qt.Vertical:
    #             v_delta = ev.delta()
    #             h_delta = 0
    #         else:
    #             h_delta = ev.delta()
    #             v_delta = 0
    #     else:
    #         delta = ev.angleDelta()
    #         h_delta = delta.x()
    #         v_delta = delta.y()
    #
    #     mods = ev.modifiers()
    #     if Qt.ControlModifier == int(mods) and v_delta:
    #         self.zoomRequest.emit(v_delta)
    #     else:
    #         v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
    #         h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
    #     ev.accept()
    #
    # def keyPressEvent(self, ev):
    #     key = ev.key()
    #     if key == Qt.Key_Escape and self.current:
    #         print('ESC press')
    #         self.current = None
    #         self.drawingPolygon.emit(False)
    #         self.update()
    #     elif key == Qt.Key_Return and self.canCloseShape():
    #         self.finalise()
    #     elif key == Qt.Key_Left and self.selectedShape:
    #         self.moveOnePixel('Left')
    #     elif key == Qt.Key_Right and self.selectedShape:
    #         self.moveOnePixel('Right')
    #     elif key == Qt.Key_Up and self.selectedShape:
    #         self.moveOnePixel('Up')
    #     elif key == Qt.Key_Down and self.selectedShape:
    #         self.moveOnePixel('Down')
    #
    # def moveOnePixel(self, direction):
    #     # print(self.selectedShape.points)
    #     if direction == 'Left' and not self.moveOutOfBound(QPointF(-1.0, 0)):
    #         # print("move Left one pixel")
    #         self.selectedShape.points[0] += QPointF(-1.0, 0)
    #         self.selectedShape.points[1] += QPointF(-1.0, 0)
    #         self.selectedShape.points[2] += QPointF(-1.0, 0)
    #         self.selectedShape.points[3] += QPointF(-1.0, 0)
    #     elif direction == 'Right' and not self.moveOutOfBound(QPointF(1.0, 0)):
    #         # print("move Right one pixel")
    #         self.selectedShape.points[0] += QPointF(1.0, 0)
    #         self.selectedShape.points[1] += QPointF(1.0, 0)
    #         self.selectedShape.points[2] += QPointF(1.0, 0)
    #         self.selectedShape.points[3] += QPointF(1.0, 0)
    #     elif direction == 'Up' and not self.moveOutOfBound(QPointF(0, -1.0)):
    #         # print("move Up one pixel")
    #         self.selectedShape.points[0] += QPointF(0, -1.0)
    #         self.selectedShape.points[1] += QPointF(0, -1.0)
    #         self.selectedShape.points[2] += QPointF(0, -1.0)
    #         self.selectedShape.points[3] += QPointF(0, -1.0)
    #     elif direction == 'Down' and not self.moveOutOfBound(QPointF(0, 1.0)):
    #         # print("move Down one pixel")
    #         self.selectedShape.points[0] += QPointF(0, 1.0)
    #         self.selectedShape.points[1] += QPointF(0, 1.0)
    #         self.selectedShape.points[2] += QPointF(0, 1.0)
    #         self.selectedShape.points[3] += QPointF(0, 1.0)
    #     self.shapeMoved.emit()
    #     self.repaint()
    #
    # def moveOutOfBound(self, step):
    #     points = [p1+p2 for p1, p2 in zip(self.selectedShape.points, [step]*4)]
    #     return True in map(self.outOfPixmap, points)
    #
    # def setLastLabel(self, text, line_color  = None, fill_color = None):
    #     assert text
    #     self.shapes[-1].label = text
    #     if line_color:
    #         self.shapes[-1].line_color = line_color
    #
    #     if fill_color:
    #         self.shapes[-1].fill_color = fill_color
    #
    #     return self.shapes[-1]
    #
    # def undoLastLine(self):
    #     assert self.shapes
    #     self.current = self.shapes.pop()
    #     self.current.setOpen()
    #     self.line.points = [self.current[-1], self.current[0]]
    #     self.drawingPolygon.emit(True)
    #
    # def resetAllLines(self):
    #     assert self.shapes
    #     self.current = self.shapes.pop()
    #     self.current.setOpen()
    #     self.line.points = [self.current[-1], self.current[0]]
    #     self.drawingPolygon.emit(True)
    #     self.current = None
    #     self.drawingPolygon.emit(False)
    #     self.update()
    #
    # def loadPixmap(self, pixmap):
    #     self.pixmap = pixmap
    #     self.shapes = []
    #     self.repaint()
    #
    # def loadShapes(self, shapes):
    #     self.shapes = list(shapes)
    #     self.current = None
    #     self.repaint()
    #
    # def setShapeVisible(self, shape, value):
    #     self.visible[shape] = value
    #     self.repaint()
    #
    # def currentCursor(self):
    #     cursor = QApplication.overrideCursor()
    #     if cursor is not None:
    #         cursor = cursor.shape()
    #     return cursor
    #
    # def overrideCursor(self, cursor):
    #     self._cursor = cursor
    #     if self.currentCursor() is None:
    #         QApplication.setOverrideCursor(cursor)
    #     else:
    #         QApplication.changeOverrideCursor(cursor)
    #
    # def restoreCursor(self):
    #     QApplication.restoreOverrideCursor()
    #
    # def resetState(self):
    #     self.restoreCursor()
    #     self.pixmap = None
    #     self.update()
    #
    # def setDrawingShapeToSquare(self, status):
    #     self.drawSquare = status



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    wind = QtWidgets.QWidget()

    layout = QtWidgets.QVBoxLayout()
    but_layout = QtWidgets.QHBoxLayout()



    canvas = Bev_Canvas_2(dev_mode = "SOLO")
    layout.addWidget(canvas)

    create_roi_but = QtWidgets.QPushButton("CREATE ROI")
    create_roi_but.clicked.connect(canvas.create_ROI)
    but_layout.addWidget(create_roi_but)
    layout.addLayout(but_layout)

    wind.setLayout(layout)

    wind.show()
    sys.exit(app.exec())
