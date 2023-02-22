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
