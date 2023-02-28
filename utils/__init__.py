import numpy as np

def load_scene(scene_file):
    with open(scene_file, 'r') as f:
        _, height = f.readline().split()
        height = int(height)
        _, width = f.readline().split()
        width = int(width)
        _, base_r, base_c = f.readline().split()
        try:
            base_r = int(base_r)
            base_c = int(base_c)
        except:
            pass
        _, num_agents = f.readline().split()
        num_agents = int(num_agents)
        grids = []
        for r in range(height):
            row = f.readline().strip()
            grids.append([])
            for c in range(width):
                grids[r].append(row[c])
    grids = np.array(grids)
    return grids, base_r, base_c, num_agents


def distance_euclid(pos0, pos1):
    return ((pos0[0] - pos1[0]) ** 2 + (pos0[1] - pos1[1]) ** 2) ** 0.5


def distance_manhattan(pos0, pos1):
    return abs(pos0[0] - pos1[0]) + abs(pos0[1] - pos1[1])
