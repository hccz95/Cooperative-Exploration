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

        self.pixmap_high_ground = QPixmap('figs/high_ground.png')
        self.pixmap_river = QPixmap('figs/river.png')
        self.pixmap_tree = QPixmap('figs/tree.png')
        self.pixmap_munition_storage = QPixmap('figs/munition_storage.png')
        self.pixmap_fence = QPixmap('figs/fence.png')
        self.pixmap_tank  = QPixmap('figs/tank.png')
        self.pixmap_troop_carrier  = QPixmap('figs/troop_carrier.png')
        self.pixmap_minefield = QPixmap('figs/minefield.png')
        self.pixmap_supply_station = QPixmap('figs/supply_station.png')
        self.pixmap_repair_shop = QPixmap('figs/repair_shop.png')
        self.pixmap_bunker = QPixmap('figs/bunker.png')
        self.pixmap_fortification = QPixmap('figs/fortification.png')
        self.pixmap_mountain = QPixmap('figs/mountain.png')
        self.pixmap_solider = QPixmap('figs/solider.png')
        self.pixmap_bridge = QPixmap('figs/bridge.png')
        self.pixmap_legend = QPixmap('figs/legend.png')
        
        self.initUI()

    def initUI(self):
        self.setupUi(self)

        self.setWindowTitle("Path Planning Visualization")
        self.setWindowIcon(QApplication.style().standardIcon(0))
        # self.setGeometry(100, 100, 800, 800)

        self.canvas = QGraphicsScene()
        self.map.setScene(self.canvas)

        l_h, l_w = self.legend.height(), self.legend.width()
        pixmap_legend = QGraphicsPixmapItem(self.pixmap_legend.scaled(l_w*0.9, l_h*0.9))
        scene_legend = QGraphicsScene()
        scene_legend.addItem(pixmap_legend)
        self.legend.setScene(scene_legend)

        # 窗口置顶
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def draw_win(self, maps, predators):
        self.maps = maps
        self.region_height, self.region_width = maps.region_height, maps.region_width
        h_max, w_max = self.map.height(), self.map.width()
        self.UNIT = min((h_max - 5) / self.region_height, (w_max - 5) / self.region_width)
        self.maps.UNIT = self.UNIT

        self.draw_init(predators)

    def draw_init(self, predators):
        # 先清除掉上一个场景的所有图形
        self.canvas.clear()
        self.actions_text.setPlainText("")
        self.instruction_text.setPlainText("")

        cell_size = self.UNIT
        pixmap_size = cell_size*0.9
        pixmap_gap = cell_size*0.05
        self.grids = np.empty((self.region_height, self.region_width), dtype=object)
        for r in range(self.region_height):
            for c in range(self.region_width):
                # 注意这里，新建ellipse组件时，给的是其局部坐标，setPos设置的是其相对场景的全局坐标
                rect = QGraphicsRectItem(0, 0, cell_size, cell_size)
                rect.setPos(c * cell_size, r * cell_size)
                if self.maps.grids[r, c] == '=':
                    rect.setBrush(QBrush(QColor(0xEEEEEE)))
                self.canvas.addItem(rect)
                self.grids[r][c] = rect
                
                if self.maps.grids[r, c] in ['$', '~', '?', '*', '#', '&', '@', '!', '+', '^', ':', '-', '=', '<', '>']:
                    if self.maps.grids[r, c] == '$':
                        # 加载图片，并调整大小为网格大小
                        pixmap_item = self.canvas.addPixmap(self.pixmap_high_ground.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '~':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_river.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '?':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_tree.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '*':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_munition_storage.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '#':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_fence.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '&':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_tank.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '@':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_troop_carrier.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '!':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_minefield.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '+':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_supply_station.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '^':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_repair_shop.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '-':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_fortification.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == ':':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_bunker.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '=':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_mountain.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '<':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_solider.scaled(pixmap_size, pixmap_size))
                    elif self.maps.grids[r, c] == '>':
                        pixmap_item = self.canvas.addPixmap(self.pixmap_bridge.scaled(pixmap_size, pixmap_size))
 
                    x, y = self.maps.rc2xy((r, c), 'corner')
                    pixmap_item.setPos(x+pixmap_gap, y+pixmap_gap)

        delta = int(self.UNIT * 0.25)
        self.agents = []
        for predator in predators:
            x, y = self.maps.rc2xy(predator.position, mode='center')
            self.grids[predator.position].setBrush(QBrush(QColor(0x00ff00)))
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

            self.canvas.addItem(agent)
            self.agents.append(agent)

        # 这里定义一个cover，在场景开始之前遮住地图，等开始之后设置为不可见即可
        # cover = QGraphicsRectItem(0, 0, self.region_height * cell_size, self.region_width * cell_size)
        # cover.setPos(0, 0)
        # cover.setVisible(True)      # 初始时可见，且位于顶层，会遮住其他元素
        # cover.setBrush(QBrush(QColor(0x0000ff)))
        # self.canvas.addItem(cover)
        # self.cover = cover

    def update_map(self, predators=[], key_region=[]):
        #self.cover.setVisible(False)    # 将cover设置为不可见，显露出地图

        cell_size = self.UNIT

        # draw predators
        for i, predator in enumerate(predators):
            color = self.grids[predator.position].brush().color()
            opacity = self.grids[predator.position].opacity()
            if color.name() == '#000000':
                self.grids[predator.position].setBrush(QBrush(QColor(0xffff00)))
                self.grids[predator.position].setOpacity(0.2)
            else:
                self.grids[predator.position].setOpacity(opacity + 0.2)

            x, y = self.maps.rc2xy(predator.position, mode='center')
            self.agents[i].setPos(x, y)
            self.agents[i].setRotation(ori2deg[predator.orientation])
            
    def set_start(self, enable=True):
        if enable:
            self.btn_start.setEnabled(True)
        else:
            self.btn_start.setDisabled(True)
    def set_clear(self, enable=True):
        if enable:
            self.btn_clear.setEnabled(True)
        else:
            self.btn_clear.setDisabled(True)
    def set_save(self, enable=True):
        if enable:
            self.btn_save.setEnabled(True)
        else:
            self.btn_save.setDisabled(True)
    def set_next(self, enable=True):
        if enable:
            self.btn_next.setEnabled(True)
        else:
            self.btn_next.setDisabled(True)
    def get_name(self):

        # 用对话框收集用户姓名
        if self.args.use_heuristic:
            name = f"heuristic_seed_{self.args.seed:02d}"
        elif self.args.alg == "hsi":
            name, ok = QInputDialog.getText(self, 'Input', 'Your name:')
            if not ok or name == '':
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
