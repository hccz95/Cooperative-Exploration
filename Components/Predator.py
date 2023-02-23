import numpy as np
from Components.Components import MoveComponent
from collections import deque

T = 20

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
    stuck_ratio = 25

    def __init__(self, position, num, region_size, sight=1, maps=None):
        super(Predator, self).__init__(position, num, region_size, maps)
        self.__region_size = region_size
        self.__sight = sight
        self.maps = maps

        self.history = deque(maxlen=T)

        self.stuck = False
        self.chosen = False
        self.goal = None
        self.planned_path = deque()

        self.visit()

    def visit(self):
        r, c = self.position
        self.history.append((r, c))
        self.maps.cell_visited[r][c] = 1
        self.maps.cell_chemical[r][c] += chemical_inc

        for r_, c_ in self.visible_positions():
            self.maps.cell_visable[r_][c_] = 1

        self.detect()

    def visible_positions(self):
        """向各方向做主序，遇到障碍则该方向中断"""
        positions = []
        motions = [(0, -1), (-1, 0), (0, +1), (+1, 0), (0, -1)]
        r, c = self.position
        for m in motions[:4]:
            rr, cc = r, c
            for d in range(1, self.__sight + 1):
                rr += m[0]
                cc += m[1]
                positions.append((rr, cc))
                if self.maps.obstacle(rr, cc):
                    break
        for _ in range(4):
            m1 = motions[_]
            m2 = motions[_+1]
            rr, cc = r, c
            for d in range(1, self.__sight + 1):
                rr += m1[0] + m2[0]
                cc += m1[1] + m2[1]
                if not self.maps.obstacle(rr, cc) and not self.maps.obstacle(r - m1[0], c - m1[1]) and not self.maps.obstacle(r - m2[0], c - m2[1]):
                    positions.append((rr, cc))
                else:
                    break
                rrr, ccc = rr, cc
                for dd in range(1, self.__sight - d + 1):
                    rrr += m1[0]
                    ccc += m1[1]
                    positions.append((rrr, ccc))
                    if not self.maps.passable(rrr, ccc):
                        break

                rrr, ccc = rr, cc
                for dd in range(1, self.__sight - d + 1):
                    rrr += m2[0]
                    ccc += m2[1]
                    positions.append((rrr, ccc))
                    if not self.maps.passable(rrr, ccc):
                        break
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
            probs = np.ones_like(cmd_list) / len(cmd_list)
            cmd = np.random.choice(cmd_list, p=probs)       # probabilistic
            # cmd = cmd_list[np.argmax(probs)]                # deterministic

        super(Predator, self).move(cmd)
        self.visit()

    def detect(self):
        if self.stuck:
            return
        if len(self.planned_path) > 0:
            return
        if len(self.history) == self.history.maxlen:
            bin = set()
            for x in self.history:
                bin.add(x)
            if len(bin) < len(self.history) * Predator.stuck_ratio / 100:
                print('Depression Agent#', self.num)
                self.stuck = True
                self.history.clear()
