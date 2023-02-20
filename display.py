# this file is based on Yong Zhao's code

import tkinter as tk
from PIL import Image, ImageTk

UNIT = 25
X_min, X_max = 0, 30
Y_min, Y_max = 0, 30
size = 1
step_size = 1


class Maze(tk.Tk, object):
    def __init__(self):
        super(Maze, self).__init__()

        self.configure(bg="#CDC0B0")                # 整体的背景色
        self.resizable(width=False, height=False)   # 窗口是否可以设置大小

        # header模块
        self.f_header = tk.Frame(self, height=6 * UNIT, width=X_max * UNIT, highlightthickness=0, bg="#CDC0B0")
        self.f_header.place(x=10, y=(Y_max+0.5)*UNIT, anchor='nw')

        self.geometry('{0}x{1}'.format((X_max+11) * UNIT, (Y_max+7) * UNIT))

        # 画布模块
        self.canvas = tk.Canvas(self, height=Y_max * UNIT, width=X_max * UNIT, bg='white')
        self.canvas.place(x=10, y=10, anchor='nw')

        # 图例模块
        img_open = Image.new('RGB', (256, 256), (255, 255, 255))
        self.img_png = ImageTk.PhotoImage(img_open)
        self.legend = tk.Label(self, image=self.img_png, height=Y_max * UNIT + 150, width=240, bg='white')
        self.legend.place(x=20 + X_max * UNIT, y=10, anchor='nw')


if __name__ == "__main__":
    ma = Maze()

    ma.mainloop()
