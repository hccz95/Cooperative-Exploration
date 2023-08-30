#!/usr/bin/python
# -*-coding:utf-8-*-

import random
import numpy as np
import logging
from utils import distance_euclid
from utils.AStar import AStar
from Components.Map import Map
from Components.Predator import Predator
from collections import deque
from utils import load_scene


class SimEnv(object):
    goal_coverage = 0.99

    def __init__(self, scenes=None, args=None):

        self.scenes = deque(scenes)
        self.args = args
        Predator.args = args

        super(SimEnv, self).__init__()

    def load_scene(self, ):
        if len(self.scenes) == 0:
            return False

        print(f"Scene \"{self.scenes[0]}\" start....")
        logging.info(f"Scene \"{self.scenes[0]}\" start....")

        grids, base_r, base_c, num_predator, max_steps = load_scene(self.scenes[0])
        self.max_steps = max_steps
        self.maps = Map(grids)
        self.scene = self.scenes[0]
        self.scenes.popleft()

        self.region_size = self.maps.region_size
        self.region_height, self.region_width = self.region_size
        self.num_predator = num_predator

        if base_r == 'random':
            base_r, base_c = self.maps.random_free_position()

        self.maps.base_r = base_r
        self.maps.base_c = base_c
        self.predators = [Predator(position=(base_r, base_c), num=idx, region_size=self.region_size, sight=2, maps=self.maps)
                          for idx in range(num_predator)]
        self.maps.prune_frontier()

        self.step_cnt = 0
        self.planner = AStar(self.maps, "manhattan")
        self.chosen_predator = None
        self.stat = []
        self.key_region = []
        self.last_slow = None

        return True

    def step(self):
        self.step_cnt += 1
        logging.info(f"Step# {self.step_cnt} start.")

        stuck_cnt = 0
        # predator move
        self.stuck_agent_ids = []
        for predator in self.predators:
            predator.maps.step_cnt = self.step_cnt
            predator.move()
            if predator.stuck:
                stuck_cnt += 1
                self.stuck_agent_ids.append(predator.num)

        self.maps.prune_frontier()

        # count coverage rate
        coverage = self.maps.get_coverage()
        self.stat.append(coverage)

        if self.step_cnt % 100 == 0:
            print('Step#', self.step_cnt, ' Coverage:', coverage)

        logging.info(f"Coverage: {round(coverage*100, 1)} %")
        logging.info(f"Step# {self.step_cnt} end.")

        # 检测是否存在新stuck_agent，或者slow
        self.stuck_cnt = stuck_cnt
        self.is_slow = False
        if self.args.alg == "hsi" or self.args.use_heuristic:
            # 计算覆盖率的微分，如果太慢则报警
            T = 50
            min_dt = 0.1        # 这里设置阈值为0.3 (平均一个agent每步能探索的新网格数，[0, 2*sight+1])
            self.is_slow = False
            if self.step_cnt >= T and (self.stat[-1] - self.stat[-T]) * len(self.maps.free_grids) / T / self.num_predator < min_dt:
                # print("Slow", (self.stat[-1] - self.stat[-T]) * cnt_total / T / self.num_predator)
                self.is_slow = True

                if self.last_slow is None or self.step_cnt - self.last_slow >= T:
                    self.last_slow = self.step_cnt

            self.stuck_new = False
            for predator in self.predators:
                if predator.stuck_new:
                    self.stuck_new = True
                    break

        # # 设置一些禁区，避免重复访问
        # for predator in self.predators:
        #     predator.close()

        # self.maps.evaporate()

    def left_click(self, x, y):

        print("Left Click")
        logging.info("Left Click mark")

        min_pred = None
        min_dis = 1e8
        stuck_cnt = 0
        for predator in self.predators:
            if predator.stuck:
                stuck_cnt += 1
                r, c = predator.position
                px, py = self.maps.rc2xy((r, c))
                distance_to_mouse = distance_euclid((x, y), (px, py))
                if distance_to_mouse < min_dis and distance_to_mouse < self.maps.UNIT * 1.0:
                    min_dis = distance_to_mouse
                    min_pred = predator

        if self.chosen_predator is not None:
            if min_pred:        # 之前选定了一个stuck_agent，但是现在选中了另一个
                self.chosen_predator.chosen = False
                self.chosen_predator = min_pred
                min_pred.chosen = True
                logging.info(f"Left Click: Select agent# {min_pred.num}!")
            else:               # 之前选定了一个stuck_agent，现在为其选定了Temp_Goal
                r, c = self.maps.xy2rc((x, y))
                path = self.planner.searching(self.chosen_predator.position, (r, c))
                if len(path) > 0:           # Temp_Goal可达
                    self.chosen_predator.stuck = False
                    self.chosen_predator.chosen = False
                    self.chosen_predator.goal = (r, c)
                    self.chosen_predator.planned_path = path
                    logging.info(f"Left Click: Select a valid goal ({r}, {c}) for the chosen agent# {self.chosen_predator.num}!")

                    self.chosen_predator = None
                else:                       # Temp_Goal不可达
                    # TODO: label_tips与gui相关，不应该放在这里
                    # self.label_tips.config(bg='red', text="You chose an INVALID Goal!")
                    logging.info(f"Left Click: Select a invalid goal!")
        else:
            if min_pred:        # 选定了一个新的stuck_agent
                self.chosen_predator = min_pred
                self.chosen_predator.chosen = True
                logging.info(f"Left Click: Select agent# {min_pred.num}!")
            else:       # 选定了一个Temp_Goal，需要自动分配stuck_agent，如果没有stuck_agent，分配给最近的aco agent
                r, c = self.maps.xy2rc((x, y))
                # 将Temp_Goal分配到最近的stuck_agent
                predator_num = []
                predator_pos = []
                for predator in self.predators:
                    if predator.stuck or (stuck_cnt == 0 and len(predator.planned_path) == 0):  # 已经规划过路径的agent不受影响
                        predator_num.append(predator.num)
                        predator_pos.append(predator.position)
                idx = self._find_the_nearest_goal(r, c, predator_pos)
                if idx != -1:
                    predator = self.predators[predator_num[idx]]
                    path = self.planner.searching(predator.position, (r, c))
                    if len(path) > 0:
                        logging.info(f"Left Click: Select goal ({r}, {c}) for agent# {predator.num}!")
                        if predator.stuck:
                            logging.info(f"Event: Agent# {predator.num} turn back to unstuck")
                            predator.stuck = False
                        predator.chosen = False
                        predator.goal = (r, c)
                        predator.planned_path = path

    def right_click(self, x, y):

        r, c = self.maps.xy2rc((x, y))

        if not self.maps.cell_visible[r][c] or self.maps.obstacle(r, c):
            print("Invalid source")
            logging.info("Invalid Right Click!")
            return

        print("Right Click")
        logging.info("Right Click mark")

        self.key_region.append([x, y, 10])

        predator_num = []
        for predator in self.predators:
            pr, pc = predator.position
            px, py = self.maps.rc2xy((pr, pc))
            distance_to_mouse = distance_euclid((x, y), (px, py))
            if distance_to_mouse / self.maps.UNIT < 0.25 * self.region_height:
                if predator.stuck:
                    logging.info(f"Agent# {predator.num} turn back to unstuck")
                    predator.stuck = False
                # predator.goal = (r, c)
                from utils.AStar import AStar
                planner = AStar(self.maps, "manhattan")
                path = planner.searching((pr, pc), (r, c), global_visible=True)
                if len(path) > 0:
                    predator.planned_path = path
                    predator_num.append(predator.num)

        logging.info(f"Right Click: Select a key point ({r}, {c}), Affected agents' ids are {predator_num}")

    def _find_the_nearest_goal(self, r, c, goals):
        from collections import deque
        q = deque()
        q.append((r, c))
        mark = np.zeros_like(self.maps.grids, dtype=int)
        mark[r][c] = 1
        while len(q) > 0:
            r, c = q.popleft()
            for r_, c_ in self.maps.passable_neighbors(r, c):
                if mark[r_][c_]:
                    continue
                mark[r_][c_] = mark[r][c] + 1
                if (r_, c_) in goals:
                    return goals.index((r_, c_))
                q.append((r_, c_))
        return -1

    def max_steps_exceeded(self):
        return self.step_cnt >= self.max_steps

    def completed(self):
        return self.maps.get_coverage() >= self.goal_coverage

    def generate_left_event(self):

        agent_id = np.random.choice(self.stuck_agent_ids)
        predator = self.predators[agent_id]
        frontier = random.choice(self.maps.frontiers)

        px, py = self.maps.rc2xy(predator.position)
        fx, fy = self.maps.rc2xy(frontier)

        return px, py, fx, fy

    def generate_right_event(self):

        best_frontier = random.choice(self.maps.frontiers)
        best_p_cnt = 0
        for frontier in self.maps.frontiers:
            p_cnt = 0
            for predator in self.predators:
                if distance_euclid(predator.position, frontier) < 0.25 * self.region_height / self.maps.UNIT:
                    p_cnt += 1
            if p_cnt > best_p_cnt:
                best_frontier = frontier
                best_p_cnt = p_cnt
        fx, fy = self.maps.rc2xy(best_frontier)

        return fx, fy


if __name__ == "__main__":
    default_config = {
        "seed": 1,
        "alg": "aco",
        "use_heuristic": False
    }

    import types, os
    args = types.SimpleNamespace(**default_config)
    scenes = [map_name for map_name in os.listdir('scenes/')]
    env = SimEnv(scenes=scenes, args=args)

    while env.load_scene():
        while True:
            env.step()
            if env.max_steps_exceeded() or env.completed():
                print(env.maps.get_coverage())
                break
