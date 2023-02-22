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
        self.predators = [Predator(position=(base_r, base_c), num=idx, region_size=self.region_size, sight=2, maps=maps)
                          for idx in range(num_predator)]

        prey_r, prey_c = self.maps.random_free_position()
        self.preys = [Prey(position=(prey_r, prey_c), region_size=self.region_size, num=0)]

        ############################

        self.win = display.Maze(self.maps)
        self.win.title('HSI')
        self.win.bind("g", self.cmd_start)

        # 绑定鼠标左键事件
        self.win.canvas.bind("<Button-1>", None)

        # 绑定Start按钮事件
        self.b_start = tk.Button(self.win.f_header, text="START", command=self.cmd_start, font=("Times New Roman", 15, "bold"))
        self.b_start.place(x=5, y=10, anchor='nw')

        self.scale_aco_c = tk.Scale(self.win.f_header, label="aco_c", from_=0., to=1., orient=tk.HORIZONTAL, length=300, resolution=0.05, tickinterval=0.2)
        self.scale_aco_c.set(0.05)
        self.scale_aco_c.place(x=100, y=10, anchor='nw')

        self.scale_aco_a = tk.Scale(self.win.f_header, label="aco_a", from_=1, to=20, orient=tk.HORIZONTAL, length=300, resolution=1, tickinterval=5)
        self.scale_aco_a.set(2)
        self.scale_aco_a.place(x=450, y=10, anchor='nw')

        self.step_cnt = 0

        super(SimEnv, self).__init__()

    def run(self):
        self.win.draw_reset(self.predators)
        self.win.canvas.update()

        self.win.mainloop()

    def cmd_start(self, key=None):
        print('Cmd: Start')
        while True:
            self.step_cnt += 1

            # get scale value
            Predator.aco_c = self.scale_aco_c.get()
            Predator.aco_alpha = self.scale_aco_a.get()

            self.step()
            self.win.draw_reset(self.predators)
            self.win.canvas.update()

            # count coverage rate

            if self.step_cnt % 100 == 0:
                cnt_visited = self.maps.cell_visited.sum()
                cnt_total = (self.maps.cell_obstacle == 0).sum()
                print(self.step_cnt, cnt_visited / cnt_total)

            if key:
                break

    def step(self):

        # predator move
        for predator in self.predators:
            predator.maps.step_cnt = self.step_cnt
            predator.move()

        for predator in self.predators:
            predator.close()
