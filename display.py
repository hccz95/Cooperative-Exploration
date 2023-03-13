# this file is based on Yong Zhao's code
import os
import tkinter as tk
from tkinter.simpledialog import askstring
import logging
from PIL import Image, ImageTk, ImageDraw

H_max = 800
W_max = 1200
size = 1
step_size = 1
gap = 5
H_1 = 40 + gap * 2
H_2 = 50


class Maze(tk.Tk, object):
    def __init__(self, args=None):
        super(Maze, self).__init__()

        self.args = args

        self.configure(bg="#CDC0B0")                # 整体的背景色CDC0B0
        self.resizable(width=False, height=False)   # 窗口是否可以设置大小

        self.geometry('{0}x{1}'.format(W_max, H_max))

        # 画布模块
        canvas_h, canvas_w = H_max - gap * 2, H_max - gap * 2
        self.canvas = tk.Canvas(self, height=canvas_h, width=canvas_w, bg='#CDC0B0')
        self.canvas.place(x=gap, y=H_max//2, anchor='w')

        # 按钮容器
        W_2 = W_max - canvas_w - gap * 3
        X_2 = gap * 2 + canvas_w
        self.indicate = tk.Frame(self, height=H_1, width=W_2, bg='#CDC0B0')
        self.indicate.place(x=X_2, y=gap, anchor='nw')

        # header模块
        self.f_header = tk.Frame(self, height=H_2, width=W_2, highlightthickness=0, bg="#FFFFFF")
        self.f_header.place(x=X_2, y=gap + H_1 + gap, anchor="nw")

        # 图例模块
        img_open = Image.open('Legend.png')
        self.img_png = ImageTk.PhotoImage(img_open)
        self.legend = tk.Label(self, image=self.img_png, height=H_max - H_1 - H_2 - gap * 4,
                                                         width=W_2, bg='#CDC0B0', anchor='s')
        self.legend.place(x=X_2, y=gap + H_1 + gap + H_2 + gap, anchor='nw')

        self.image = Image.new("RGB", (canvas_w, canvas_h), (205, 192, 176))    # #CDC0B0
        self.draw = ImageDraw.Draw(self.image)

    def get_name(self):
        # 用对话框收集用户姓名
        if self.args.alg == "hsi":
            name = askstring(title="UserName", prompt="Please input your name!", initialvalue=None, parent=self)
            if name is None or name == "":
                name = "Anonymous"
        else:
            name = self.args.alg
        self.args.name = name

        if not os.path.exists(f'logs/{self.args.name}'):
            os.makedirs(f'logs/{self.args.name}')
        logging.basicConfig(filename=f'logs/{self.args.name}/{self.args.name}.log', level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s'
                            )
        logging.info(f"New Experiment, Username is [{self.args.name}], Mode is [{self.args.mode}]")


    def load_maps(self, maps):
        self.maps = maps

        self.region_height, self.region_width = maps.region_height, maps.region_width
        self.UNIT = min((H_max - gap * 2) / self.region_height, (H_max - gap * 2) / self.region_width)

    def draw_reset(self, predators=[], key_region=[]):
        for r in range(self.region_height):
            for c in range(self.region_width):
                x, y = c * self.UNIT, r * self.UNIT
                if not self.maps.cell_visible[r][c]:
                    self.draw.rectangle((x, y, x+self.UNIT, y+self.UNIT), fill='#bfbfbf', width=1, outline='#7f7f7f')
                elif self.maps.cell_obstacle[r][c]:
                    self.draw.rectangle((x, y, x + self.UNIT, y + self.UNIT), fill='black', width=1, outline='#000000')
                elif self.maps.is_closed(r, c):
                    self.draw.rectangle((x, y, x + self.UNIT, y + self.UNIT), fill='#3f3f3f', width=1, outline='#7f7f7f')
                else:
                    pheromone = self.maps.cell_chemical[r][c]
                    from utils.color import get_color_by_pheromone
                    color = get_color_by_pheromone(pheromone)
                    self.draw.rectangle((x, y, x + self.UNIT, y + self.UNIT), fill=color, width=1, outline='#7f7f7f')
        # 给地图画一个边框
        self.draw.rectangle((2, 2, self.region_width * self.UNIT - 1, self.region_height * self.UNIT - 1), outline='black')

        # draw predators
        for predator in predators:
            r, c = predator.position
            x, y = c * self.UNIT, r * self.UNIT

            delta = int(self.UNIT * 0.15)
            if predator.stuck:
                self.draw.ellipse((x - delta * 2, y - delta * 2, x + self.UNIT + delta * 2, y + self.UNIT + delta * 2), width=2, outline='black')
                self.draw.ellipse((x + delta, y + delta, x + self.UNIT - delta, y + self.UNIT - delta), fill='blue' if predator.chosen else 'red', width=0, outline='blue' if predator.chosen else 'red')
            elif len(predator.planned_path) > 0:
                self.draw.ellipse((x + delta, y + delta, x + self.UNIT - delta, y + self.UNIT - delta), fill='green', width=0, outline='green')
            else:
                self.draw.ellipse((x + delta, y + delta, x + self.UNIT - delta, y + self.UNIT - delta), fill='red', width=0, outline='red')

        for i, (x, y, t) in enumerate(key_region):
            rad = int((self.region_width+self.region_height) * 0.125) * self.UNIT
            if t % 2 == 0:
                self.draw.ellipse((x - rad, y - rad, x + rad, y + rad), outline='#7f7f7f', width=2)
            else:
                self.draw.ellipse((x - rad, y - rad, x + rad, y + rad), outline='#3f3f3f', width=2)

            rad = 0.4 * self.UNIT
            self.draw.ellipse((x - rad, y - rad, x + rad, y + rad), fill=(47, 47, 47), width=0)
            key_region[i][2] -= 1

        while len(key_region) > 0 and key_region[0][2] == 0:
            del key_region[0]

        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")


if __name__ == "__main__":
    ma = Maze()

    ma.mainloop()
