# this file is based on Yong Zhao's code

import tkinter as tk
from PIL import Image, ImageTk

H_max = 800
W_max = 1200
size = 1
step_size = 1
gap = 5
H_1 = 40 + gap * 2
H_2 = 50


class Maze(tk.Tk, object):
    def __init__(self, ):
        super(Maze, self).__init__()

        self.configure(bg="#CDC0B0")                # 整体的背景色CDC0B0
        self.resizable(width=False, height=False)   # 窗口是否可以设置大小

        self.geometry('{0}x{1}'.format(W_max, H_max))

        # 画布模块
        canvas_h, canvas_w = H_max - gap * 2, H_max - gap * 2
        self.canvas = tk.Canvas(self, height=canvas_h, width=canvas_w, bg='white')
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

    def load_maps(self, maps):
        self.maps = maps

        self.region_height, self.region_width = maps.region_height, maps.region_width
        self.UNIT = min((H_max - gap * 2) / self.region_height, (H_max - gap * 2) / self.region_width)

    def draw_reset(self, predators=[], key_region=[]):
        self.canvas.delete("all")

        self.map_area = self.canvas.create_rectangle(2, 2, self.region_width * self.UNIT, self.region_height * self.UNIT, outline='black')
        for r in range(self.region_height):
            for c in range(self.region_width):
                x, y = c * self.UNIT, r * self.UNIT
                if not self.maps.cell_visible[r][c]:
                    self.canvas.create_rectangle(x, y, x+self.UNIT, y+self.UNIT, fill='#bfbfbf', width=1, outline='#7f7f7f')
                elif self.maps.cell_obstacle[r][c]:
                    self.canvas.create_rectangle(x, y, x + self.UNIT, y + self.UNIT, fill='black', width=1, outline='#000000')
                elif self.maps.is_closed(r, c):
                    self.canvas.create_rectangle(x, y, x + self.UNIT, y + self.UNIT, fill='#3f3f3f', width=1, outline='#7f7f7f')
                else:
                    pheromone = self.maps.cell_chemical[r][c]
                    from utils.color import get_color_by_pheromone
                    color = get_color_by_pheromone(pheromone)
                    self.canvas.create_rectangle(x, y, x + self.UNIT, y + self.UNIT, fill=color, width=1, outline='#7f7f7f')

        # draw predators
        for predator in predators:
            r, c = predator.position
            x, y = c * self.UNIT, r * self.UNIT

            delta = int(self.UNIT * 0.15)
            if predator.stuck:
                self.canvas.create_oval(x - delta * 2, y - delta * 2, x + self.UNIT + delta * 2, y + self.UNIT + delta * 2, width=1.5)
                self.canvas.create_oval(x + delta, y + delta, x + self.UNIT - delta, y + self.UNIT - delta, fill='blue' if predator.chosen else 'red', width=0, outline='blue' if predator.chosen else 'red')
            elif len(predator.planned_path) > 0:
                self.canvas.create_oval(x + delta, y + delta, x + self.UNIT - delta, y + self.UNIT - delta, fill='green', width=0, outline='green')
            else:
                self.canvas.create_oval(x + delta, y + delta, x + self.UNIT - delta, y + self.UNIT - delta, fill='red', width=0, outline='red')

        for i, (x, y, t) in enumerate(key_region):
            rad = int((self.region_width+self.region_height) * 0.125) * self.UNIT
            if t % 2 == 0:
                self.canvas.create_oval(x - rad, y - rad, x + rad, y + rad, outline='#7f7f7f', dash=(4, 11), width=2)
            else:
                self.canvas.create_oval(x - rad, y - rad, x + rad, y + rad, outline='#3f3f3f', dash=(6, 17), width=2)

            rad = 1 * self.UNIT
            self.canvas.create_oval(x - rad, y - rad, x + rad, y + rad, fill='#2f2f2f', width=0)
            key_region[i][2] -= 1

        while len(key_region) > 0 and key_region[0][2] == 0:
            del key_region[0]


if __name__ == "__main__":
    ma = Maze()

    ma.mainloop()
