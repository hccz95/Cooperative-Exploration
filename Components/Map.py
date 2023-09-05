import numpy as np
import random

class Map(object):
    def __init__(self, grids):
        self.grids = grids
        self.region_size = grids.shape
        self.region_height, self.region_width = grids.shape

        self.free_grids = []
        self.process_grids(grids)
        self.optional_orientation = ['N','E','S','W']   #'NE','NW','SE','SW'
        self.cell_visited = np.zeros_like(grids, dtype=bool)
        self.cell_visible = np.zeros_like(grids, dtype=bool)
        self.cell_chemical = np.zeros_like(grids, dtype=float)
        self.cell_obstacle = np.array(grids != '.', dtype=bool)
        self.cell_closed = np.zeros_like(grids, dtype=int)

        self.step_cnt = 0
        self.explored_cnt = 0

        self.frontiers = []

    def process_grids(self, grids):
        anc = np.zeros((self.region_height * self.region_width), dtype=int)
        siz = np.zeros((self.region_height * self.region_width), dtype=int)
        for i in range(self.region_height * self.region_width):
            anc[i] = i
            siz[i] = 1
        def find_anc(x):
            if anc[x] != x:
                anc[x] = find_anc(anc[x])
            return anc[x]
        def union(p, q):
            if p != q:
                if siz[p] > siz[q]:
                    anc[q] = p
                    siz[p] += siz[q]
                else:
                    anc[p] = q
                    siz[q] += siz[p]

        max_block_anc = None
        for r in range(self.region_height):
            for c in range(self.region_width):
                if grids[r][c] == '.':
                    id = self.rc2id((r, c))
                    for dr, dc in [(0, -1), (-1, 0), (0, +1), (+1, 0)]:
                        if self.in_range(r + dr, c + dc) and grids[r + dr][c + dc] == '.':
                            id_ = self.rc2id((r + dr, c + dc))
                            fa, fa_ = find_anc(id), find_anc(id_)
                            union(fa, fa_)
                    if max_block_anc is None or siz[find_anc(id)] > siz[max_block_anc]:
                        max_block_anc = anc[id]

        for r in range(self.region_height):
            for c in range(self.region_width):
                fa = find_anc(self.rc2id((r, c)))
                if fa == max_block_anc:
                    self.free_grids.append((r, c))
                else:
                    grids[r][c] = '#'
        print('Free Grids:', len(self.free_grids), )

    def random_free_position(self):
        idx = np.random.randint(0, len(self.free_grids))
        return self.free_grids[idx]

    def random_orientation(self):
        # 新增随机方向生成
        return random.choice(self.optional_orientation)

    def passable(self, r, c):
        if self.in_range(r, c) and not self.obstacle(r, c):
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

    def rc2id(self, position):
        r, c = position
        return r * self.region_width + c

    def get_coverage(self):
        return self.explored_cnt / len(self.free_grids)


if __name__ == "__main__":
    grids = np.array([['.', '#', '.'], ['.', '.', '.']])
    maps = Map(grids)
    pos = maps.random_free_position()
    print(pos)
