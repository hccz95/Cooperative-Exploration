import numpy as np

chemical_inc = 0.30
chemical_eva = 0.80
chemical_dif = 0.05


class Map(object):
    def __init__(self, grids):
        self.grids = grids
        self.region_size = grids.shape
        self.region_height, self.region_width = grids.shape

        self.cell_visited = np.zeros_like(grids, dtype=bool)
        self.cell_visible = np.zeros_like(grids, dtype=bool)
        self.cell_chemical = np.zeros_like(grids, dtype=float)
        self.cell_obstacle = np.array(grids != '.', dtype=bool)
        self.cell_closed = np.zeros_like(grids, dtype=int)

        self.step_cnt = 0

        self.free_grids = []
        self.process_grids(grids)

    def process_grids(self, grids):
        mark = np.zeros_like(grids, dtype=bool)
        from collections import deque
        max_block = deque()
        for r in range(self.region_height):
            for c in range(self.region_width):
                if mark[r][c]:
                    continue
                if grids[r][c] != '.':
                    continue
                block = deque()
                q = deque()
                mark[r][c] = True
                q.append((r, c))
                while len(q) > 0:
                    r_, c_ = q.pop()
                    block.append((r_, c_))
                    if self.in_range(r_+1, c_) and not mark[r_+1][c_] and grids[r_+1][c_] == '.':
                        mark[r_+1][c_] = True
                        q.append((r_+1, c_))
                    if self.in_range(r_-1, c_) and not mark[r_-1][c_] and grids[r_-1][c_] == '.':
                        mark[r_-1][c_] = True
                        q.append((r_-1, c_))
                    if self.in_range(r_, c_+1) and not mark[r_][c_+1] and grids[r_][c_+1] == '.':
                        mark[r_][c_+1] = True
                        q.append((r_, c_+1))
                    if self.in_range(r_, c_-1) and not mark[r_][c_-1] and grids[r_][c_-1] == '.':
                        mark[r_][c_-1] = True
                        q.append((r_, c_-1))
                if len(max_block) < len(block):
                    max_block = block
        self.free_grids = max_block

    def random_free_position(self):
        idx = np.random.randint(0, len(self.free_grids))
        return self.free_grids[idx]

    def is_closed(self, r, c):
        return not self.in_range(r, c) or self.obstacle(r, c) or (self.cell_closed[r][c] > 0)

    def passable(self, r, c):
        if self.in_range(r, c) and not self.obstacle(r, c) and 0 == self.cell_closed[r][c]:
            return True
        return False

    def obstacle(self, r, c):
        return not self.in_range(r, c) or self.cell_obstacle[r][c]

    def chemical(self, r, c):
        return self.cell_chemical[r][c]

    def get_color(self, r, c):
        if not self.cell_visited[r][c]:
            return (127, 127, 127)
        if self.cell_obstacle[r][c]:
            return (0, 0, 0)
        return (255, 255, 255)

    def in_range(self, r, c):
        return 0 <= r < self.region_height and 0 <= c < self.region_width

    def evaporate(self):
        for r in range(self.region_height):
            for c in range(self.region_width):
                self.cell_chemical[r][c] *= chemical_eva

    def passable_neighbors(self, r, c):
        neighbors = []
        if self.passable(r, c-1):
            neighbors.append((r, c-1))
        if self.passable(r, c+1):
            neighbors.append((r, c+1))
        if self.passable(r-1, c):
            neighbors.append((r-1, c))
        if self.passable(r+1, c):
            neighbors.append((r+1, c))
        return neighbors

    def xy2rc(self, pixel):
        x, y = pixel
        r, c = int(y / self.UNIT), int(x // self.UNIT)
        return r, c

    def rc2xy(self, position, mode='center'):
        r, c = position
        x, y = c * self.UNIT, r * self.UNIT
        if mode == 'center':
            x += 0.5 * self.UNIT
            y += 0.5 * self.UNIT
        return x, y


if __name__ == "__main__":
    grids = np.array([['.', '#', '.'], ['.', '.', '.']])
    maps = Map(grids)
    pos = maps.random_free_position()
    print(pos)
