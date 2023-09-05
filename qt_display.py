import os, sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
    QInputDialog, QGraphicsPixmapItem, QSizePolicy
)
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem
from PyQt5.QtGui import QColor, QBrush, QPen, QPixmap, QPolygonF
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5 import uic
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

Ui_MainWindow, QtBaseClass = uic.loadUiType("interface.ui")

# 方向与角度的对应关系
ori2deg = {"N": 0, "E": 90, "S": 180, "W": 270}

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
        # 先清除掉上一个场景的所有图形
        self.scene.clear()

        cell_size = self.UNIT
        self.grids = np.empty((self.region_height, self.region_width), dtype=object)
        for r in range(self.region_height):
            for c in range(self.region_width):
                # 注意这里，新建ellipse组件时，给的是其局部坐标，setPos设置的是其相对场景的全局坐标
                rect = QGraphicsRectItem(0, 0, cell_size, cell_size)
                rect.setPos(c * cell_size, r * cell_size)
                self.scene.addItem(rect)
                self.grids[r][c] = rect

                if self.maps.obstacle(r, c):
                    # 加载树的图片，并调整大小为网格大小
                    pixmap_item = self.scene.addPixmap(QPixmap('figs/tree.png').scaled(cell_size, cell_size))
                    x, y = self.maps.rc2xy((r, c), 'corner')
                    pixmap_item.setPos(x, y)

        delta = int(self.UNIT * 0.15)
        radius = int(self.UNIT * 0.35)
        self.agents = []
        for predator in predators:
            x, y = self.maps.rc2xy(predator.position, mode='center')
            # 由于涉及到rotation，这里的坐标必须以agent的中心点为原点！
            agent_poly = QPolygonF([QPointF(0, -delta),
                                    QPointF(-delta, delta),
                                    QPointF(0, 0),
                                    QPointF(delta, delta)])
            agent = QGraphicsPolygonItem()
            agent.setPolygon(agent_poly)
            agent.setPos(x, y)
            agent.setRotation(ori2deg[predator.orientation])
            agent.setBrush(QBrush(QColor(0xff0000)))    # 设置填充色
            agent.setPen(QPen(QColor(0x00ff00)))        # 设置边框颜色

            self.scene.addItem(agent)
            self.agents.append(agent)

        # 这里定义一个cover，在场景开始之前遮住地图，等开始之后设置为不可见即可
        cover = QGraphicsRectItem(0, 0, self.region_height * cell_size, self.region_width * cell_size)
        cover.setPos(0, 0)
        cover.setVisible(True)      # 初始时可见，且位于顶层，会遮住其他元素
        cover.setBrush(QBrush(QColor(0x0000ff)))
        self.scene.addItem(cover)
        self.cover = cover

    def update_map(self, predators=[], key_region=[]):
        self.cover.setVisible(False)    # 将cover设置为不可见，显露出地图

        cell_size = self.UNIT

        # draw predators
        for i, predator in enumerate(predators):
            x, y = self.maps.rc2xy(predator.position, mode='center')
            self.agents[i].setPos(x, y)
            self.agents[i].setRotation(ori2deg[predator.orientation])

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
