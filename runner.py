#!/usr/bin/python
# -*-coding:utf-8-*-

import tkinter as tk
import display
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
        self.predators = [Predator(position=(base_r, base_c), num=idx, region_size=self.region_size, sight=3, maps=maps)
                          for idx in range(num_predator)]

        prey_r, prey_c = self.maps.random_free_position()
        self.preys = [Prey(position=(prey_r, prey_c), region_size=self.region_size, num=0)]

        super(SimEnv, self).__init__()

    def run(self):
        self.win = display.Maze()
        self.win.title('HSI')

        # 绑定鼠标左键事件
        self.win.canvas.bind("<Button-1>", None)

        # 绑定Start按钮事件
        self.b_start = tk.Button(self.win.f_header, text="START", command=self.cmd_start, font=("Times New Roman", 15, "bold"))
        self.b_start.place(x=5, y=10, anchor='nw')

        self.win.mainloop()

    def cmd_start(self):
        print('Cmd: Start')

        step_cnt = 0
        while True:
            step_cnt += 1

            self.step()

            # count coverage rate
            cnt_visited = self.maps.cell_visited.sum()
            cnt_total = self.maps.cell_visited.size

            if step_cnt % 100 == 0:
                print(step_cnt, cnt_visited / cnt_total)

    def step(self):

        # predator move
        for predator in self.predators:
            predator.move()
