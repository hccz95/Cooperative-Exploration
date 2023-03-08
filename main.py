import argparse
import logging
import random
import os
import numpy as np
from runner import SimEnv


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, help='user name', default="Anonymous")
    parser.add_argument('--seed', type=int, help='random seed', default=1)
    args = parser.parse_args()

    if not os.path.exists('logs/'):
        os.makedirs('logs')
    logging.basicConfig(filename=f'logs/{args.name}.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    random.seed(args.seed)
    np.random.seed(args.seed)

    scenes = ['scenes/' + map_name for map_name in os.listdir('scenes/')]
    runner = SimEnv(scenes=scenes)
    runner.run()
