import logging
import numpy as np
from Components.Components import MoveComponent
from collections import deque

T = 100

chemical_inc = 0.30
chemical_eva = 0.9995
chemical_dif = 0.05

pos_dt = [
    [(0, 0)],
    [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)],
    [(0, -2), (-1, -2), (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (2, -1), (2, -2), (1, -2)],
]
#  2  3  4  5  6
#  1  1  2  3  7
#  0  0  C  4  8
# 15  7  6  5  9
# 14 13 12 11 10


class Predator(MoveComponent):
    '''This is the class of intruder.'''
    _name = 'Predator'

    aco_c = 0.02  # Husain_2022中c为20，但是这里将信息素归一化了，所以对应c也要成比例减小
    aco_alpha = 2
    stuck_ratio = 25

    def __init__(self, position, orientation, num, region_size, sight=1, maps=None):
        super(Predator, self).__init__(position, num, region_size, maps)
        self.__region_size = region_size
        self.__sight = sight
        self.maps = maps
        self.orientation = orientation #新加头部朝向

        self.history = {"pos": deque(maxlen=T), "chemical": deque(maxlen=T), "act": deque(maxlen=T)}

        self.stuck = False
        self.chosen = False
        self.goal = None
        self.planned_path = deque()

        self.visit()

    def visit(self, act='START'):
        r, c = self.position
        o = self.orientation
        self.maps.cell_visited[r][c] = 1
        self.maps.cell_chemical[r][c] += chemical_inc

        self.history["pos"].append((r, c, o))
        self.history["chemical"].append(self.maps.cell_chemical[r][c])
        self.history["act"].append(act)
        for r_, c_ in self.visible_positions():
            if self.maps.in_range(r_, c_) and not self.maps.cell_visible[r_][c_]:
                self.maps.cell_visible[r_][c_] = True
                self.maps.explored_cnt += ~self.maps.cell_obstacle[r_][c_]

        if Predator.args.alg == 'hsi':
            self.detect()

    def visible_positions(self):
        """Flood fill"""
        motions = [(0, -1), (-1, 0), (0, +1), (+1, 0)]
        r, c = self.position
        positions = [(r, c)]

        mark = np.zeros((self.__sight * 2 + 1, self.__sight * 2 + 1), dtype=bool)
        mark[0][0] = True

        q = deque()
        q.append((0, 0))
        while len(q) > 0:
            dr, dc = q.popleft()
            for mr, mc in motions:
                dr_, dc_ = dr + mr, dc + mc
                if abs(dr_)<=self.__sight and abs(dc_)<=self.__sight and self.maps.in_range(r+dr_, c+dc_) and not mark[dr_][dc_]:
                    mark[dr_][dc_] = True
                    positions.append((r+dr_, c+dc_))
                    if not self.maps.obstacle(r+dr_, c+dc_):
                        q.append((dr_, dc_))

        return positions

    def move_toward(self, orientation):
        ori2id = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
        ori_delta = ori2id[orientation] - ori2id[self.orientation]

        if self.orientation == orientation:
            self.move("MF")
        elif ori_delta in [-2, 2]:
            self.move('TR')
            self.move('TR')
        elif ori_delta in [-1, 3]:
            self.move("TL")
        elif ori_delta in [1, -3]:
            self.move("TR")

    def move(self, act):

        if act == 'TL':
            self.turn_left()
        elif act == 'TR':
            self.turn_right()
        elif act == 'MF':
            act_cmd = self.go_forward()
            cmd_list, neighbor_list = self.moveable_directions()
            for cmd, nb in zip(cmd_list, neighbor_list):
                if cmd == act_cmd:
                    super(Predator, self).move(cmd)
        elif act == 'MB':
            act_cmd = self.go_backward()
            cmd_list, neighbor_list = self.moveable_directions()
            for cmd, nb in zip(cmd_list, neighbor_list):
                if cmd == act_cmd:
                    super(Predator, self).move(cmd)
        self.visit(act)

    def detect(self):
        return False

    def turn_left(self):
        turn_left_dict = {
            'N':'W',
            'W':'S',
            'S':'E',
            'E':'N'
        }
        self.orientation = turn_left_dict.get(self.orientation, 'Invalid orientation')

    def turn_right(self):
        turn_right_dict = {
            'N':'E',
            'E':'S',
            'S':'W',
            'W':'N'
        }
        self.orientation = turn_right_dict.get(self.orientation, 'Invalid orientation')

    def go_forward(self):
        go_forward_dict = {
            'N':'U',
            'W':'L',
            'S':'D',
            'E':'R'
        }
        return go_forward_dict.get(self.orientation, 'Invalid orientation')

    def go_backward(self):
        go_backward_dict = {
            'N':'D',
            'W':'R',
            'S':'U',
            'E':'L'
        }
        return go_backward_dict.get(self.orientation, 'Invalid orientation')
