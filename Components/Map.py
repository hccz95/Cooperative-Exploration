import numpy as np

chemical_inc = 0.30
chemical_eva = 0.80
chemical_dif = 0.05

class Map(object):
    def __init__(self, grids):
        self.grids = grids
        self.region_size = grids.shape
        self.region_height, self.region_width = grids.shape

        self.cell_visited = np.zeros_like(grids, dtype=int)
        self.cell_chemical = np.zeros_like(grids, dtype=float)
        self.cell_obstacle = np.array(grids == '.', dtype=int)

        self.free_grids = []
        for r in range(self.region_height):
            for c in range(self.region_width):
                if self.cell_obstacle[r][c]:
                    self.free_grids.append((r, c))

    def random_free_position(self):
        idx = np.random.randint(0, len(self.free_grids))
        return self.free_grids[idx]

    def is_obstacle(self, r, c):
        return self.cell_obstacle[r][c]

    def chemical(self, r, c):
        return self.cell_chemical[r][c]

    def get_color(self, r, c):
        if not self.cell_visited[r][c]:
            return (127, 127, 127)
        if self.cell_obstacle:
            return (0, 0, 0)
        return (255, 255, 255)


if __name__ == "__main__":
    grids = np.array([['.', '#', '.'], ['.', '.', '.']])
    maps = Map(grids)
    pos = maps.random_free_position()
    print(pos)
