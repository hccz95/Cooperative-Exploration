#!/usr/bin/python
# -*-coding:utf-8-*-

import tkinter as tk
import display
from utils.AStar import AStar
import numpy as np
import time
from utils import distance_euclid
from Components.Predator import Predator
from Components.Components import Component as Prey


class SimEnv(object):
    def __init__(self,
                 maps,
                 num_predator=10
                 ):

        self.region_size = maps.region_size
        self.region_height, self.region_width = self.region_size
        self.num_predator = num_predator
        self.maps = maps

        base_r, base_c = self.maps.random_free_position()
        self.predators = [Predator(position=(base_r, base_c), num=idx, region_size=self.region_size, sight=2, maps=maps)
                          for idx in range(num_predator)]

        prey_r, prey_c = self.maps.random_free_position()
        self.preys = [Prey(position=(prey_r, prey_c), region_size=self.region_size, num=0)]

        ############################

        self.win = display.Maze(self.maps)
        self.win.title('HSI')
        self.win.bind("g", self.cmd_start)

        self.maps.UNIT = self.win.UNIT

        # 绑定鼠标左键事件
        self.win.canvas.bind("<Button-1>", self.click)

        # 绑定Start按钮事件
        self.b_start = tk.Button(self.win.indicate, text="START", command=self.cmd_start, font=("Times New Roman", 15, "bold"))
        self.b_start.place(x=5, y=10, anchor='nw')

        self.scale_aco_c = tk.Scale(self.win.indicate, label="aco_c", from_=0., to=1., orient=tk.HORIZONTAL, length=200, resolution=0.05, tickinterval=0.2)
        self.scale_aco_c.set(0.05)
        self.scale_aco_c.place(x=5, y=60, anchor='nw')

        self.scale_aco_a = tk.Scale(self.win.indicate, label="aco_a", from_=1, to=20, orient=tk.HORIZONTAL, length=200, resolution=1, tickinterval=5)
        self.scale_aco_a.set(2)
        self.scale_aco_a.place(x=5, y=150, anchor='nw')

        self.scale_stuck_ratio = tk.Scale(self.win.indicate, label="ratio (%)", from_=0, to=100, orient=tk.HORIZONTAL, length=200, resolution=5, tickinterval=20)
        self.scale_stuck_ratio.set(40)
        self.scale_stuck_ratio.place(x=5, y=240, anchor='nw')

        # 底部信息
        self.label_tips = tk.Label(self.win.f_header, text="Click START to start the search process", width=50, height=4, bg="white", font=("Times New Roman", 14), wraplength=self.win.f_header.winfo_vrootwidth())
        self.label_tips.place(x=5, y=60, anchor="nw")

        self.step_cnt = 0

        self.planner = AStar(self.maps, "manhattan")
        self.chosen_predator = None

        super(SimEnv, self).__init__()

    def run(self):
        self.win.draw_reset(self.predators)
        self.win.canvas.update()

        self.win.mainloop()

    def cmd_start(self, key=None):
        print('Cmd: Start')
        self.label_tips.config(text="The main process is running")

        while True:
            time_stamp = time.time()

            self.step_cnt += 1

            # get scale value
            Predator.aco_c = self.scale_aco_c.get()
            Predator.aco_alpha = self.scale_aco_a.get()
            Predator.stuck_ratio = self.scale_stuck_ratio.get()

            self.step()

            self.win.draw_reset(self.predators)
            self.win.canvas.update()

            # count coverage rate

            cnt_visable = self.maps.cell_visable.sum()
            cnt_total = self.maps.cell_visable.size
            coverage = cnt_visable / cnt_total
            if coverage > 0.95:
                self.label_tips.config(text="Mission Completed!")
                # break
            if self.step_cnt % 100 == 0:
                print('Step#', self.step_cnt, ' Coverage:', coverage)

            if key:
                break

            if time.time() - time_stamp < 0.5:
                time.sleep(time.time() - time_stamp)

    def click(self, pos):
        x, y = pos.x, pos.y

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
            else:               # 之前选定了一个stuck_agent，现在为其选定了Temp_Goal
                r, c = self.maps.xy2rc((x, y))
                path = self.planner.searching(self.chosen_predator.position, (r, c))
                if len(path) > 0:           # Temp_Goal可达
                    self.chosen_predator.stuck = False
                    self.chosen_predator.chosen = False
                    self.chosen_predator.goal = (r, c)
                    self.chosen_predator.planned_path = path

                    self.chosen_predator = None
                else:                       # Temp_Goal不可达
                    self.label_tips.config(text="You chose an INVALID Goal!")
        else:
            if min_pred:        # 选定了一个新的stuck_agent
                self.chosen_predator = min_pred
                self.chosen_predator.chosen = True
            elif stuck_cnt > 0: # 选定了一个Temp_Goal，需要自动分配stuck_agent
                r, c = self.maps.xy2rc((x, y))
                # 将Temp_Goal分配到最近的stuck_agent
                predator_num = []
                predator_pos = []
                for predator in self.predators:
                    if predator.stuck:
                        predator_num.append(predator.num)
                        predator_pos.append(predator.position)
                idx = self._find_the_nearest_goal(r, c, predator_pos)
                if idx != -1:
                    predator = self.predators[predator_num[idx]]
                    path = self.planner.searching(predator.position, (r, c))
                    if len(path) > 0:
                        predator.stuck = False
                        predator.chosen = False
                        predator.goal = (r, c)
                        predator.planned_path = path

    def step(self):

        stuck_cnt = 0
        # predator move
        for predator in self.predators:
            predator.maps.step_cnt = self.step_cnt
            predator.move()
            if predator.stuck:
                stuck_cnt += 1
        if stuck_cnt:
            self.label_tips.config(text="%d agent(s) stucked!" % stuck_cnt, bg='red')

        # # 设置一些禁区，避免重复访问
        # for predator in self.predators:
        #     predator.close()

        # self.maps.evaporate()

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
