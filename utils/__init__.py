import numpy as np


def load_grids(map_file):
    with open(map_file, 'r') as f:
        _ = f.readline()
        _, height = f.readline().split()
        height = int(height)
        _, width = f.readline().split()
        width = int(width)
        _ = f.readline()
        grids = []
        for r in range(height):
            row = f.readline().strip()
            grids.append([])
            for c in range(width):
                grids[r].append(row[c])
    grids = np.array(grids)
    return grids


def distance_euclid(pos0, pos1):
    return ((pos0[0] - pos1[0]) ** 2 + (pos0[1] - pos1[1]) ** 2) ** 0.5


def distance_manhattan(pos0, pos1):
    return abs(pos0[0] - pos1[0]) + abs(pos0[1] - pos1[1])
