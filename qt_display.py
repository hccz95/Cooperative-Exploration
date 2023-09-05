import os, sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsEllipseItem,
    QInputDialog, QGraphicsPixmapItem, QSizePolicy
)
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem
from PyQt5.QtGui import QColor, QBrush, QPen, QPixmap
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5 import uic
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

Ui_MainWindow, QtBaseClass = uic.loadUiType("interface.ui")


class MapVisualization(Ui_MainWindow, QMainWindow):
    def __init__(self, args=None):
        super().__init__()

        self.args = args

        self.timer = QTimer(self)

        self.initUI()

    def initUI(self):
        self.setupUi(self)

        self.setWindowTitle("Path Planning Visualization")
        self.setWindowIcon(QApplication.style().standardIcon(0))
        # self.setGeometry(100, 100, 800, 800)

        self.scene = QGraphicsScene()
        self.map.setScene(self.scene)

        # 窗口置顶
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def load_scene(self, maps, predators):
        self.maps = maps
        self.region_height, self.region_width = maps.region_height, maps.region_width
        h_max, w_max = self.map.height(), self.map.width()
        self.UNIT = min((h_max - 5) / self.region_height, (w_max - 5) / self.region_width)
        self.maps.UNIT = self.UNIT

        self.draw_init(predators)

    def draw_init(self, predators):
        cell_size = self.UNIT
        self.grids = np.empty((self.region_height, self.region_width), dtype=object)
        for r in range(self.region_height):
            for c in range(self.region_width):
                rect = QGraphicsRectItem(0, 0, cell_size, cell_size)
                rect.setPos(c * cell_size, r * cell_size)
                rect.setVisible(False)
                self.scene.addItem(rect)
                self.grids[r][c] = rect

        delta = int(self.UNIT * 0.15)
        radius = int(self.UNIT * 0.35)
        self.agents = []
        self.rings = []
        for predator in predators:
            x, y = self.maps.rc2xy(predator.position, mode='corner')
            # 注意这里，新建ellipse组件时，给的是其局部坐标，setPos设置的是其相对场景的全局坐标
            agent = QGraphicsEllipseItem(0, 0, radius * 2, radius * 2)
            ring = QGraphicsEllipseItem(0, 0, radius * 2 + delta * 4, radius * 2 + delta * 4)
            agent.setPos(x + delta, y + delta)
            ring.setPos(x - delta * 2, y - delta * 2)
            agent.setVisible(False)
            ring.setVisible(False)
            self.scene.addItem(agent)
            self.scene.addItem(ring)
            self.agents.append(agent)
            self.rings.append(ring)

    def update_map(self, predators=[], key_region=[]):
        cell_size = self.UNIT
        for r in range(self.region_height):
            for c in range(self.region_width):
                rect = self.grids[r][c]
                if not rect.isVisible():
                    rect.setVisible(True)

                if not self.maps.cell_visible[r][c]:
                    fill = 0xbfbfbf
                    outline = 0x7f7f7f
                elif self.maps.cell_obstacle[r][c]:
                    fill = 0x000000
                    outline = 0x000000
                elif self.maps.is_closed(r, c):
                    fill = 0x3f3f3f
                    outline = 0x7f7f7f
                else:
                    pheromone = self.maps.cell_chemical[r][c]
                    from utils.color import get_color_by_pheromone
                    color = get_color_by_pheromone(pheromone)
                    fill = int('0x' + color[1:], 16)
                    outline = 0x7f7f7f

                rect.setBrush(QBrush(QColor(fill)))
                rect.setPen(QPen(QColor(outline), 1))

        # draw predators
        delta = int(self.UNIT * 0.15)
        radius = int(self.UNIT * 0.35)
        for i, predator in enumerate(predators):
            x, y = self.maps.rc2xy(predator.position, mode='corner')
            self.agents[i].setVisible(True)
            self.agents[i].setPos(x + delta, y + delta)
            self.rings[i].setVisible(False)
            self.rings[i].setPos(x - delta , y - delta)

            if predator.stuck:
                self.rings[i].setVisible(True)
                fill = 0x0000ff if predator.chosen else 0xff0000
                outline = 0x000000
                width = 0
            elif len(predator.planned_path) > 0:
                fill = 0x00ff00
                outline = 0x00ff00
                width = 0
            else:
                fill = 0xff0000
                outline = 0xff0000
                width = 0

            brush = QBrush(QColor(fill))
            pen = QPen(QColor(outline))
            if width == 0:
                pen = QPen(Qt.NoPen)
            else:
                pen.setWidth(width)

            self.agents[i].setBrush(brush)
            self.agents[i].setPen(pen)

    def set_start(self, enable=True):
        if enable:
            self.start.setEnabled(True)
        else:
            self.start.setDisabled(True)

    def set_next(self, enable=True):
        if enable:
            self.next.setEnabled(True)
        else:
            self.next.setDisabled(True)

    def get_name(self):

        # 用对话框收集用户姓名
        if self.args.use_heuristic:
            name = f"heuristic_seed_{self.args.seed:02d}"
        elif self.args.alg == "hsi":
            name, ok = QInputDialog.getText(self, 'Input', 'Your name:')
            if not ok:
                name = "Anonymous"
        else:
            name = f"{self.args.alg}_seed_{self.args.seed:02d}"
        self.args.name = name

        if not os.path.exists(f'logs/{self.args.name}'):
            os.makedirs(f'logs/{self.args.name}')
        # logging.basicConfig(filename=f'logs/{self.args.name}/{self.args.name}.log', level=logging.INFO,
        #                     format='%(asctime)s %(levelname)s %(message)s'
        #                     )
        # logging.info(f"New Experiment, Username is [{self.args.name}], Mode is [{self.args.mode}]")
