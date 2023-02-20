import random
import numpy as np
from utils import load_grids
from runner import SimEnv
from Components.Map import Map
seed = 1


if __name__ == "__main__":
    random.seed(seed)
    np.random.seed(seed)

    map_file = 'maps/empty.map'
    grids = load_grids(map_file)
    maps = Map(grids)

    runner = SimEnv(maps)
    runner.run()
