#!/usr/bin/python
# -*-coding:utf-8-*-

import tkinter as tk
import display


class SimEnv(object):
    def __init__(self,
                 maps,
                 num_predator=10
                 ):

        self.region_size = maps.region_size
        self.region_height, self.region_width = self.region_size
        self.num_predator = num_predator

        self.maps = maps

        super(SimEnv, self).__init__()

    def run(self):
        self.win = display.Maze()
        self.win.title('HSI')

        # 绑定鼠标左键事件
        self.win.canvas.bind("<Button-1>", None)

        # 绑定Start按钮事件
        self.b_start = tk.Button(self.win.f_header, text="START", command=None, font=("Times New Roman", 15, "bold"))
        self.b_start.place(x=5, y=10, anchor='nw')

        self.win.mainloop()
