import numpy as np
from Components.Components import MoveComponent
from collections import deque

T = 25

chemical_inc = 0.30
chemical_eva = 0.9995
chemical_dif = 0.05

pos_dt = [
    [(0, 0)],
    [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)],
    [(0, -2), (-1, -2), (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (2, -1), (2, -2), (1, -2)],
]


class Predator(MoveComponent):
    '''This is the class of intruder.'''
    _name = 'Predator'

    aco_c = 0.02  # Husain_2022中c为20，但是这里将信息素归一化了，所以对应c也要成比例减小
    aco_alpha = 2
    stuck_ratio = 30

    def __init__(self, position, num, region_size, sight=1, maps=None):
        super(Predator, self).__init__(position, num, region_size, maps)
        self.__region_size = region_size
        self.__sight = sight
        self.maps = maps

        self.history = {"pos": deque(maxlen=T), "chemical": deque(maxlen=T)}

        self.stuck = False
        self.chosen = False
        self.goal = None
        self.planned_path = deque()

        self.visit()

    def visit(self):
        r, c = self.position
        self.maps.cell_visited[r][c] = 1
        self.maps.cell_chemical[r][c] += chemical_inc

        self.history["pos"].append((r, c))
        self.history["chemical"].append(self.maps.cell_chemical[r][c])

        for r_, c_ in self.visible_positions():
            if self.maps.in_range(r_, c_):
                self.maps.cell_visible[r_][c_] = 1

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

    def close(self):
        mask_1 = 0
        r, c = self.position
        for idx, (dr, dc) in enumerate(pos_dt[1]):
            r_, c_ = r + dr, c + dc
            if self.maps.is_closed(r_, c_):
                mask_1 |= 1 << idx

        mask_1 = mask_1 << len(pos_dt[1]) | mask_1
        for idx in range(0, len(pos_dt[1]), 2):
            if (mask_1 >> idx) & 31 == 31:      # 被5个匚形格子包围
                self.maps.cell_closed[r][c] = self.maps.step_cnt
                break
            if (mask_1 >> idx) & 15 == 15 and (mask_1 >> idx >> 5) & 1 == 0:    #
                self.maps.cell_closed[r][c] = self.maps.step_cnt
                break
        for idx in range(1, len(pos_dt[1]), 2):
            if (mask_1 >> idx) & 15 == 15 and (mask_1 >> idx >> 6) & 1 == 0:
                self.maps.cell_closed[r][c] = self.maps.step_cnt
                break

    def move(self, mode="aco"):
        if self.stuck:
            return None

        if len(self.planned_path) > 0:
            nxt_nb = self.planned_path.popleft()
            cmd_list, neighbor_list = self.moveable_directions()
            for cmd, nb in zip(cmd_list, neighbor_list):
                if nb == nxt_nb:
                    break
        elif mode == "aco":     # aco move
            probs = []
            cmd_list, neighbor_list = self.moveable_directions()
            for cmd, nb in zip(cmd_list, neighbor_list):
                r, c = nb
                pheromone = max(1e-8, self.maps.cell_chemical[r][c])
                p = (self.aco_c + pheromone) ** -self.aco_alpha
                probs.append(p)
            probs = np.array(probs) / sum(probs)
            cmd = np.random.choice(cmd_list, p=probs)       # probabilistic
            # cmd = cmd_list[np.argmax(probs)]                # deterministic
        else:                   # random move
            cmd_list, neighbor_list = self.moveable_directions()
            probs = np.ones_like(cmd_list, dtype=float) / len(cmd_list)
            cmd = np.random.choice(cmd_list, p=probs)       # probabilistic
            # cmd = cmd_list[np.argmax(probs)]                # deterministic

        super(Predator, self).move(cmd)
        self.visit()

    def detect(self):
        if self.stuck:
            return True
        if len(self.planned_path) > 0:
            return False
        if len(self.history["pos"]) == self.history["pos"].maxlen:
            bin = set()
            for x in self.history["pos"]:
                bin.add(x)
            if len(bin) < len(self.history["pos"]) * Predator.stuck_ratio / 100:
                print('Depression Agent#', self.num)
                self.stuck = True
                self.history["pos"].clear()

                import winsound
                winsound.Beep(1000, 800)        # 发出警报声

                return True
        return False
