import numpy as np
from Components.Components import MoveComponent

chemical_inc = 0.30
chemical_eva = 0.80
chemical_dif = 0.05

pos_dt = [
    [(0, 0)],
    [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)],
    [(0, -2), (-1, -2), (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (2, -1), (2, -2), (1, -2)]
]


class Predator(MoveComponent):
    '''This is the class of intruder.'''
    _name = 'Predator'

    aco_c = 0.02  # Husain_2022中c为20，但是这里将信息素归一化了，所以对应c也要成比例减小
    aco_alpha = 2

    def __init__(self, position, num, region_size, sight=1, maps=None):
        super(Predator, self).__init__(position, num, region_size, maps)
        self.__region_size = region_size
        self.__sight = sight
        self.maps = maps

        self.visit()

    def visit(self):
        r, c = self.position
        self.maps.cell_visited[r][c] = 1
        for d in range(self.__sight+1):
            for dr, dc in pos_dt[d]:
                r_, c_ = r + dr, c + dc
                if self.maps.in_range(r_, c_):
                    self.maps.cell_visable[r_][c_] = 1
                    if d == 0:
                        self.maps.cell_chemical[r_][c_] += chemical_inc

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

    def move(self):
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

        super(Predator, self).move(cmd)
        self.visit()
