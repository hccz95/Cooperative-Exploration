#!/usr/bin/python
# -*-coding:utf-8-*-

import logging
from Components.Map import Map
from Components.Predator import Predator
from collections import deque
from utils import load_scene


class SimEnv(object):
    def __init__(self, scenes=None, args=None):

        #self.scenes = deque(scenes)
        self.args = args
        Predator.args = args

        super(SimEnv, self).__init__()

    def load_scene(self, scene=None):
        # 如果指定了文件，则加载；否则从self.scenes队列中加载

        print(f"Scene \"{scene}\" start....")
        logging.info(f"Scene \"{scene}\" start....")

        grids, base_r, base_c, num_predator, max_steps = load_scene(scene)
        self.max_steps = max_steps
        self.maps = Map(grids)
        self.scene = scene
        #self.scenes.popleft()

        self.region_size = self.maps.region_size
        self.region_height, self.region_width = self.region_size
        self.num_predator = num_predator

        if base_r == 'random':
            base_r, base_c = self.maps.random_free_position()

        self.maps.base_r = base_r
        self.maps.base_c = base_c
        base_o = self.maps.random_orientation()
        self.predators = [Predator(position=(base_r, base_c), orientation=base_o,num=idx, region_size=self.region_size, sight=10, maps=self.maps)
                          for idx in range(num_predator)]

        self.step_cnt = 0
        self.chosen_predator = None
        self.stat = []
        self.key_region = []
        self.last_slow = None

        return True
            

if __name__ == "__main__":
    default_config = {
        "seed": 1,
        "alg": "aco",
        "use_heuristic": False
    }


