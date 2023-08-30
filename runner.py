#!/usr/bin/python
# -*-coding:utf-8-*-

import os
import numpy as np
import tkinter as tk
import display
import time
import logging
from Components.Predator import Predator
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg")     # 防止绘图闪烁
default_tips = "The swarm is exploring..."


class Runner(object):

    def __init__(self, env, args=None):

        self.env = env
        self.args = args

        self.win = display.Maze(args)
        self.win.title('HSI')
        self.win.bind("g", self.cmd_start)

        self.win.bind("s", self.screenshot)

        # 绑定鼠标左键事件
        self.win.canvas.bind("<Button-1>", self.left_click)
        self.win.canvas.bind("<Button-3>", self.right_click)   # 本来绑定的是双击左键，但是会同时触发单击左键，所以先用右键代替

        # 绑定Start按钮事件
        self.b_start = tk.Button(self.win.indicate, text="START", command=self.cmd_start, font=("Times New Roman", 15, "bold"))
        self.b_start.place(x=5, y=5, anchor='nw')
        self.b_start.config(state="disabled")

        # 绑定Next按钮事件
        self.b_next = tk.Button(self.win.indicate, text="NEXT", command=self.cmd_next, font=("Times New Roman", 15, "bold"))
        self.b_next.place(x=5 + self.b_start.winfo_reqwidth() + 5, y=5, anchor='nw')
        self.b_next.config(state="disabled")

        self.scale_aco_c = tk.Scale(self.win.indicate, label="aco_c", from_=0., to=1., orient=tk.HORIZONTAL, length=200, resolution=0.05, tickinterval=0.2)
        self.scale_aco_c.set(Predator.aco_c)
        # self.scale_aco_c.place(x=5, y=60, anchor='nw')

        self.scale_aco_a = tk.Scale(self.win.indicate, label="aco_a", from_=1, to=20, orient=tk.HORIZONTAL, length=200, resolution=1, tickinterval=5)
        self.scale_aco_a.set(Predator.aco_alpha)
        # self.scale_aco_a.place(x=5, y=150, anchor='nw')

        self.scale_stuck_ratio = tk.Scale(self.win.indicate, label="ratio (%)", from_=0, to=100, orient=tk.HORIZONTAL, length=200, resolution=5, tickinterval=20)
        self.scale_stuck_ratio.set(Predator.stuck_ratio)
        # self.scale_stuck_ratio.place(x=5, y=240, anchor='nw')

        # 提示信息
        font_size = 15
        w_fa, h_fa = self.win.f_header.winfo_reqwidth(), self.win.f_header.winfo_reqheight()
        self.label_tips = tk.Label(self.win.f_header, text="Click [START] to start the coverage task.", bg="white",
                            font=("Times New Roman", font_size), wraplength=w_fa)
        self.label_tips.place(x=5, y=5, anchor="nw")

        # 绘图区
        self.fig, self.ax = plt.subplots(figsize=(4, 2.4), dpi=100)

        self.curve = FigureCanvasTkAgg(self.fig, master=self.win.legend)
        self.curve.draw()
        self.curve.get_tk_widget().place(x=0, y=0)

        self.receive_cmd = False        # 用这个变量来控制human只能在算法运行时进行操作

        super(Runner, self).__init__()

    def load_scene(self, ):
        if not self.env.load_scene():
            self.label_tips.config(text="Mission Completed, Thank You!", bg='green')
            self.label_tips.update()
            self.b_next.config(state='disabled')
            return False

        self.win.load_maps(self.env.maps)

        if len(self.env.scenes) == 0:
            self.b_next.config(state="disabled")

        self.receive_cmd = False

        self.ax.cla()
        self.ax.axhline(y=self.env.goal_coverage, color='g', linestyle='--', linewidth=1.)
        plt.xlim(xmin=0, xmax=self.env.max_steps)
        plt.ylim(ymin=0., ymax=1.)
        plt.xlabel('Steps')
        plt.ylabel('Coverage(%)')
        plt.grid()
        plt.tight_layout()
        # plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

        self.screenshot_dir = f"logs/{self.args.name}/screenshots_{self.env.scene[:-4]}"
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

        return True

    def run(self):
        # self.win.after(100, self.win.get_name)
        self.win.get_name()
        if self.load_scene():
            self.b_start.config(state="normal")
            if self.args.alg in ["aco", "random"] or self.args.use_heuristic:
                self.win.after(1000, self.cmd_start)
        else:
            if not (self.args.alg in ["aco", "random"]) and not self.args.use_heuristic:
                tk.messagebox.showinfo(title="SIM", message="Good Bye~")
            self.win.quit()
        self.win.mainloop()

    def run_until_complete(self):
        if self.args.alg == "hsi":
            self.receive_cmd = True

        time_stamp = time.time()

        # get scale value
        Predator.aco_c = self.scale_aco_c.get()
        Predator.aco_alpha = self.scale_aco_a.get()
        Predator.stuck_ratio = self.scale_stuck_ratio.get()

        self.env.step()

        if self.env.stuck_cnt > 0 or self.env.is_slow:
            tips = ""
            if self.env.stuck_cnt:
                tips += "%d agent(s) STUCK!" % self.env.stuck_cnt
            if self.env.is_slow:
                if tips: tips += "__"
                tips += "The progress is too SLOW!"
                if self.env.last_slow == self.env.step_cnt:
                    logging.info("Slow Beep!")
                    import winsound, threading
                    thread = threading.Thread(target=winsound.Beep, args=(1000, 400))
                    thread.start()

            self.label_tips.config(bg='red', text=tips)

            # 如果加入了启发式规则，且当前step出现了警告，则进行干预
            if self.args.use_heuristic:

                if self.env.stuck_cnt > 0 or self.env.last_slow == self.env.step_cnt:
                    # TODO: operation based on heuristic rule
                    if self.env.stuck_cnt > 0 and np.random.random() < 0.5: # and len(self.maps.frontiers) > 0:
                        px, py, fx, fy = self.env.generate_left_event()

                        self.win.canvas.event_generate("<Button-1>", x=px, y=py)
                        time.sleep(10)
                        self.win.canvas.event_generate("<Button-1>", x=fx, y=fy)

                    else:
                        fx, fy = self.env.generate_right_event()
                        self.win.canvas.event_generate("<Button-3>", x=fx, y=fy)

        else:
            self.label_tips.config(bg='white', text=default_tips)

        # draw coverage curve
        if self.env.step_cnt % 2 == 0:
            self.ax.plot(self.env.stat, 'b', lw=1)
            self.curve.draw()

        task_end = False
        if self.env.max_steps_exceeded() or self.env.completed():
            coverage  = self.env.maps.get_coverage()

            print(f"Scene \"{self.env.scene}\" end, Step# {self.env.step_cnt}, Coverage is {coverage:.4f}")
            logging.info(f"Scene \"{self.env.scene}\" end, Step# {self.env.step_cnt}, Coverage is {coverage:.4f}")

            if self.env.completed():
                self.label_tips.config(text="Success! Click [NEXT] to A New Task!", bg='green')
            else:
                self.label_tips.config(text="Fail! Click [NEXT] to A New Task!", bg='red')
            self.label_tips.update()

            self.receive_cmd = False
            task_end = True

        self.update_canvas()

        if task_end:
            if self.load_scene():
                self.b_next.config(state="normal")
                if self.args.alg in ["aco", "random"] or self.args.use_heuristic:
                    self.win.after(50, self.cmd_next)
            else:
                if not (self.args.alg in ["aco", "random"]) and not self.args.use_heuristic:
                    tk.messagebox.showinfo(title="SIM", message="Good Bye~")
                self.win.quit()
        else:
            # seconds, 每个场景控制在180s以内
            if self.args.nosync:
                rest_time = 1
            else:
                step_time = 180./self.env.max_steps
                rest_time = int(max(0.001, step_time - (time.time() - time_stamp)) * 1000)
            self.win.after(rest_time, self.run_until_complete)

    def cmd_start(self):
        self.label_tips.config(bg='white', text=default_tips)
        self.b_start.config(state="disabled")
        self.update_canvas()
        self.run_until_complete()

    def cmd_next(self):
        self.b_next.config(state="disabled")
        self.label_tips.config(bg='white', text=default_tips)
        self.update_canvas()
        self.run_until_complete()

    def left_click(self, event):
        if not self.receive_cmd:
            return
        if self.args.mode == 'multiple':
            return

        self.env.left_click(event.x, event.y)

    def right_click(self, event):
        if not self.receive_cmd:
            return
        if self.args.mode == 'single':
            return

        self.env.right_click(event.x, event.y)

    def update_canvas(self):
        if self.args.gui:
            self.win.draw_reset(self.env.predators, self.env.key_region)
            img_file = self.screenshot_dir + f"/{self.env.step_cnt:04d}.png"
            with open(img_file, "wb") as fp:
                self.win.image.save(fp)
            self.screenshot(img_name=self.screenshot_dir + f"/{self.env.step_cnt:04d}.png")

    def screenshot(self, key=None, img_name="screenshot.png"):
        from PIL import ImageGrab
        x = self.win.winfo_toplevel().winfo_rootx()  # + canvas.winfo_x()
        y = self.win.winfo_toplevel().winfo_rooty()  # + canvas.winfo_y()
        x1 = x + self.win.winfo_toplevel().winfo_width()
        y1 = y + self.win.winfo_toplevel().winfo_height()
        image = ImageGrab.grab((x, y, x1, y1))
        # 保存屏幕截图
        image.save(img_name)
