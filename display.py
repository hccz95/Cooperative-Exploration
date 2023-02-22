# this file is based on Yong Zhao's code

import tkinter as tk
from PIL import Image, ImageTk

H_max = 1000
W_max = 1600
size = 1
step_size = 1
gap = 10
header_height = 150
legend_width = 240


class Maze(tk.Tk, object):
    def __init__(self, maps):
        super(Maze, self).__init__()

        self.maps = maps

        self.configure(bg="#CDC0B0")                # 整体的背景色
        self.resizable(width=False, height=False)   # 窗口是否可以设置大小

        self.region_height, self.region_width = maps.region_height, maps.region_width
        self.UNIT = min((H_max - header_height) // self.region_height, (W_max - legend_width) // self.region_width)

        # header模块
        self.f_header = tk.Frame(self, height=header_height, width=self.region_width * self.UNIT, highlightthickness=0, bg="#FFFFFF")
        self.f_header.place(x=gap, y=self.region_height * self.UNIT + gap * 2, anchor="nw")

        self.geometry('{0}x{1}'.format(self.region_width * self.UNIT + legend_width + gap * 3,
                                       self.region_height * self.UNIT + header_height + gap * 3))

        # 画布模块
        self.canvas = tk.Canvas(self, height=self.region_height * self.UNIT, width=self.region_width * self.UNIT, bg='white')
        self.canvas.place(x=gap, y=gap, anchor='nw')

        # 图例模块
        img_open = Image.new('RGB', (256, 256), (255, 255, 255))
        self.img_png = ImageTk.PhotoImage(img_open)
        self.legend = tk.Label(self, image=self.img_png, height=self.region_height * self.UNIT + header_height + gap,
                                                         width=legend_width, bg='white')
        self.legend.place(x=gap * 2 + self.region_width * self.UNIT, y=gap, anchor='nw')

    def draw_reset(self, predators=[], preys=[]):
        self.canvas.delete("all")

        self.map_area = self.canvas.create_rectangle(2, 2, self.region_width * self.UNIT, self.region_height * self.UNIT, outline='black')
        for r in range(self.region_height):
            for c in range(self.region_width):
                x, y = c * self.UNIT, r * self.UNIT
                if not self.maps.cell_visable[r][c]:
                    self.canvas.create_rectangle(x, y, x+self.UNIT, y+self.UNIT, fill='#bfbfbf', width=0)
                elif self.maps.cell_obstacle[r][c]:
                    self.canvas.create_rectangle(x, y, x + self.UNIT, y + self.UNIT, fill='black', width=0)
                elif self.maps.is_closed(r, c):
                    self.canvas.create_rectangle(x, y, x + self.UNIT, y + self.UNIT, fill='#3f3f3f', width=0)
                else:
                    pheromone = self.maps.cell_chemical[r][c]
                    from utils.color import get_color_by_pheromone
                    color = get_color_by_pheromone(pheromone)
                    self.canvas.create_rectangle(x, y, x + self.UNIT, y + self.UNIT, fill=color, width=0)

        # draw predators
        for predator in predators:
            r, c = predator.position
            x, y = c * self.UNIT, r * self.UNIT
            self.canvas.create_oval(x, y, x + self.UNIT, y + self.UNIT, fill='red', width=0)

        for prey in preys:
            if prey.found:
                r, c = prey.position
                x, y = c * self.UNIT, r * self.UNIT
                self.canvas.create_oval(x, y, x + self.UNIT, y + self.UNIT, fill='green', width=0)

        self.canvas.update()


if __name__ == "__main__":
    ma = Maze()

    ma.mainloop()
