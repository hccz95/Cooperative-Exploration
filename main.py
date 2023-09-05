import argparse
import random
import os
import numpy as np
from qt_runner import Runner
from sim_env import SimEnv


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, help='random seed', default=1)
    parser.add_argument('--gui', action='store_true', help='open gui', default=False)
    parser.add_argument('--alg', choices=["hsi", "aco", "random"], default="hsi")
    parser.add_argument('--mode', choices=["all", "single", "multiple"], default="all")
    parser.add_argument('--nosync', action='store_true', help='not sync the step time', default=False)
    parser.add_argument('--use_heuristic', action='store_true', help='use heuristic rule', default=False)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    scenes = [map_name for map_name in os.listdir('scenes/')]

    env = SimEnv(scenes=scenes, args=args)
    runner = Runner(env=env, args=args)
    runner.run()
