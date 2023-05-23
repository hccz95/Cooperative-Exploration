#!/usr/bin/python
# -*-coding:utf-8-*-

import os, random
import tkinter as tk
import display
import numpy as np
import time
import logging
from utils import distance_euclid
from utils.AStar import AStar
from Components.Map import Map
from Components.Predator import Predator
from collections import deque
from utils import load_scene
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg")     # 防止绘图闪烁
default_tips = "The swarm is exploring..."
goal_coverage = 0.99


class SimEnv(object):
    key_region = []

    def __init__(self, scenes=None, args=None):

        self.scenes = deque(scenes)
        self.args = args
        Predator.args = args

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

        super(SimEnv, self).__init__()

    def load_scene(self, ):
        if len(self.scenes) == 0:
            self.label_tips.config(text="Mission Completed, Thank You!", bg='green')
            self.label_tips.update()
            self.b_next.config(state='disabled')
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
        self.predators = [Predator(position=(base_r, base_c), num=idx, region_size=self.region_size, sight=2, maps=self.maps)
                          for idx in range(num_predator)]
        self.maps.prune_frontier()

        self.win.load_maps(self.maps)
        self.maps.UNIT = self.win.UNIT

        if len(self.scenes) == 0:
            self.b_next.config(state="disabled")

        self.step_cnt = 0
        self.planner = AStar(self.maps, "manhattan")
        self.chosen_predator = None
        self.stat = []
        self.key_region = []
        self.last_slow = None
        self.receive_cmd = False

        self.ax.cla()
        self.ax.axhline(y=goal_coverage, color='g', linestyle='--', linewidth=1.)
        plt.xlim(xmin=0, xmax=max_steps)
        plt.ylim(ymin=0., ymax=1.)
        plt.xlabel('Steps')
        plt.ylabel('Coverage(%)')
        plt.grid()
        plt.tight_layout()
        # plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

        self.screenshot_dir = f"logs/{self.args.name}/screenshots_{self.scene[:-4]}"
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

        self.update_canvas()
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

        self.step_cnt += 1
        logging.info(f"Step# {self.step_cnt} start.")

        # get scale value
        Predator.aco_c = self.scale_aco_c.get()
        Predator.aco_alpha = self.scale_aco_a.get()
        Predator.stuck_ratio = self.scale_stuck_ratio.get()

        self.step()

        coverage = self.stat[-1]
        if self.step_cnt % 100 == 0:
            print('Step#', self.step_cnt, ' Coverage:', coverage)

        # draw coverage curve
        if self.step_cnt % 2 == 0:
            self.ax.plot(self.stat, 'b', lw=1)
            self.curve.draw()

        # self.update_canvas()

        logging.info(f"Coverage: {round(coverage*100, 1)} %")
        logging.info(f"Step# {self.step_cnt} end.")

        task_end = False
        if coverage > goal_coverage or self.step_cnt >= self.max_steps:
            print(f"Scene \"{self.scene}\" end, Step# {self.step_cnt}, Coverage is {coverage:.4f}")
            logging.info(f"Scene \"{self.scene}\" end, Step# {self.step_cnt}, Coverage is {coverage:.4f}")

            if coverage > goal_coverage:
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
                step_time = 180./self.max_steps
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

        logging.info("Left Click mark")

        x, y = event.x, event.y

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
                    self.label_tips.config(bg='red', text="You chose an INVALID Goal!")
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

    def right_click(self, event):
        if not self.receive_cmd:
            return
        if self.args.mode == 'single':
            return

        x, y = event.x, event.y
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
            if distance_to_mouse / self.win.UNIT < 0.25 * self.region_height:
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

    def step(self):

        stuck_cnt = 0
        # predator move
        stuck_agent_ids = []
        for predator in self.predators:
            predator.maps.step_cnt = self.step_cnt
            predator.move()
            if predator.stuck:
                stuck_cnt += 1
                stuck_agent_ids.append(predator.num)

        self.maps.prune_frontier()

        # count coverage rate
        coverage = self.maps.get_coverage()
        self.stat.append(coverage)

        if self.args.alg == "hsi" or self.args.use_heuristic:
            # 计算覆盖率的微分，如果太慢则报警
            T = 50
            min_dt = 0.1        # 这里设置阈值为0.3 (平均一个agent每步能探索的新网格数，[0, 2*sight+1])
            is_slow = False
            if self.step_cnt >= T and (self.stat[-1] - self.stat[-T]) * len(self.maps.free_grids) / T / self.num_predator < min_dt:
                # print("Slow", (self.stat[-1] - self.stat[-T]) * cnt_total / T / self.num_predator)
                is_slow = True

            if stuck_cnt or is_slow:
                tips = ""
                if stuck_cnt:
                    tips += "%d agent(s) STUCK!" % stuck_cnt
                if is_slow:
                    if tips: tips += "__"
                    tips += "The progress is too SLOW!"
                    if self.last_slow is None or self.step_cnt - self.last_slow >= T:
                        logging.info("Slow Beep!")
                        import winsound, threading
                        thread = threading.Thread(target=winsound.Beep, args=(1000, 400))
                        thread.start()

                        self.last_slow = self.step_cnt
                self.label_tips.config(bg='red', text=tips)

                # 如果加入了启发式规则，且当前step出现了警告，则进行干预
                if self.args.use_heuristic:
                    if stuck_cnt > 0 or self.last_slow == self.step_cnt:
                        # TODO: operation based on heuristic rule
                        if stuck_cnt > 0 and np.random.random() < 0.5: # and len(self.maps.frontiers) > 0:
                            agent_id = np.random.choice(stuck_agent_ids)
                            predator = self.predators[agent_id]
                            frontier = random.choice(self.maps.frontiers)

                            px, py = self.maps.rc2xy(predator.position)
                            self.win.canvas.event_generate("<Button-1>", x=px, y=py)
                            fx, fy = self.maps.rc2xy(frontier)
                            self.win.canvas.event_generate("<Button-1>", x=fx, y=fy)

                        else:
                            best_frontier = random.choice(self.maps.frontiers)
                            best_p_cnt = 0
                            for frontier in self.maps.frontiers:
                                p_cnt = 0
                                for predator in self.predators:
                                    if distance_euclid(predator.position, frontier) < 0.25 * self.region_height / self.win.UNIT:
                                        p_cnt += 1
                                if p_cnt > best_p_cnt:
                                    best_frontier = frontier
                                    best_p_cnt = p_cnt
                            fx, fy = self.maps.rc2xy(best_frontier)
                            self.win.canvas.event_generate("<Button-3>", x=fx, y=fy)

            else:
                self.label_tips.config(bg='white', text=default_tips)

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

    def update_canvas(self):
        if self.args.gui:
            self.win.draw_reset(self.predators, self.key_region)
            img_file = self.screenshot_dir + f"/{self.step_cnt:04d}.png"
            with open(img_file, "wb") as fp:
                self.win.image.save(fp)
            self.screenshot(img_name=self.screenshot_dir + f"/{self.step_cnt:04d}.png")

    def screenshot(self, key=None, img_name="screenshot.png"):
        from PIL import ImageGrab
        x = self.win.winfo_toplevel().winfo_rootx()  # + canvas.winfo_x()
        y = self.win.winfo_toplevel().winfo_rooty()  # + canvas.winfo_y()
        x1 = x + self.win.winfo_toplevel().winfo_width()
        y1 = y + self.win.winfo_toplevel().winfo_height()
        image = ImageGrab.grab((x, y, x1, y1))
        # 保存屏幕截图
        image.save(img_name)
