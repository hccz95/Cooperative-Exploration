import random, os
import numpy as np
from runner import SimEnv
seed = 1


if __name__ == "__main__":
    random.seed(seed)
    np.random.seed(seed)

    scenes = ['scenes/' + map_name for map_name in os.listdir('scenes/')]
    runner = SimEnv(scenes=scenes)
    runner.run()
