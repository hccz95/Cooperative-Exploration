import sys
import time
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer
from qt_display import MapVisualization


class Runner(object):
    def __init__(self, env, args=None):

        self.env = env
        self.args = args

        self.app = QApplication([])
        self.win = MapVisualization(args)

        # 绑定鼠标事件
        self.win.start.mousePressEvent = self.press_start
        self.win.next.mousePressEvent = self.press_next
        self.win.map.mousePressEvent = self.intervention

        # 方向键
        self.win.btn_left.mousePressEvent = self.cmd_left
        self.win.btn_right.mousePressEvent = self.cmd_right
        self.win.btn_up.mousePressEvent = self.cmd_up
        self.win.btn_down.mousePressEvent = self.cmd_down

        self.win.btn_save.mousePressEvent = self.cmd_save
        self.win.btn_clear.mousePressEvent = self.cmd_clear

        self.receive_cmd = False        # 用这个变量来控制human只能在算法运行时进行操作

        self.timer = self.win.timer
        self.timer.timeout.connect(self.step)

    def load_scene(self, scene=None):
        if not self.env.load_scene(scene):
            # self.label_tips.config(text="Mission Completed, Thank You!", bg='green')
            # self.label_tips.update()

            # TODO: 实际上，这里只需要禁用next按钮，不需要修改提示文字，因为这里只负责load_scene，更整体的逻辑可以放在外面去控制
            # self.win.no_scene_call()

            return False

        self.win.load_scene(self.env.maps, self.env.predators)

        # self.screenshot_dir = f"logs/{self.args.name}/screenshots_{self.env.scene[:-4]}"
        # if not os.path.exists(self.screenshot_dir):
        #     os.makedirs(self.screenshot_dir)

        return True

    def run(self):

        if self.load_scene():
            self.win.set_start(True)
            if self.args.alg in ["aco", "random"] or self.args.use_heuristic:
                QTimer.singleShot(1000, self.press_start)
        else:
            # if human: print("empty scene!")
            exit(0)

        self.win.show()
        sys.exit(self.app.exec_())

    def press_start(self, event=None):
        self.win.set_start(False)
        self.win.get_name()

        # 打开文件对话框
        options = QFileDialog.Options()
        scene_file, ok = QFileDialog.getOpenFileName(self.win, '选择文件', '', 'All Files (*)', options=options)

        if scene_file:
            self.load_scene(scene_file)
        else:
            scene_file = self.env.scene

        import os
        time_stamp = time.time()
        self.save_dir = f"logs/{self.args.name}/{os.path.basename(scene_file)[:-4]}_{int(time_stamp)}"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        self.update_render()

    def press_next(self, event=None):
        self.win.set_next(False)
        self.receive_cmd = True
        self.timer.start(0)

    def step(self):

        # 暂停计时器
        self.timer.stop()

        start_time = time.time()

        self.env.step()
        self.update_render()

        end_time = time.time()

        if self.env.max_steps_exceeded() or self.env.completed():
            self.timer.stop()
            self.receive_cmd = False
            if self.load_scene():
                self.win.set_next(True)
                if self.args.alg in ["aco", "random"] or self.args.use_heuristic:
                    QTimer.singleShot(50, self.press_next)
            else:
                if not (self.args.alg in ["aco", "random"]) and not self.args.use_heuristic:
                    QMessageBox.information(self.win, "SIM", "Mission Completed!\n\nGood Bye~", QMessageBox.Yes, QMessageBox.Yes)
                self.app.quit()
        else:
            if self.args.nosync:
                rest_time = 0
            else:
                step_time = 0.15
                rest_time = int(max(0.001, step_time - (time.time() - start_time)) * 1000)
                if rest_time <= 1:
                    print('out of time when rendering!')
            self.timer.start(rest_time)

    def intervention(self, event):
        if not self.receive_cmd:
            return

        if event.button() == Qt.LeftButton:
            if self.args.mode == "multiple":
                return
            print('intervention: left click')
            self.env.left_click(event.x(), event.y())
        elif event.button() == Qt.RightButton:
            if self.args.mode == 'single':
                return
            print('intervention: right click')
            self.env.right_click(event.x(), event.y())

    # 每个step之后调用一次，load_scene之后马上调用一次(step=0)
    def update_render(self):
        if self.args.gui:
            self.win.update_map(self.env.predators, self.env.key_region)
            # self.draw_curve()
            # screenshot

            # 显示动作序列
            self.win.actions_text.setPlainText(" ".join(self.env.predators[0].history['act']))

            self.win.update()

    def cmd_up(self, event=None):
        print("UPUPUP", self.env.predators[0].orientation)

        for predator in self.env.predators:
            predator.move_toward('N')
        self.update_render()

    def cmd_down(self, event=None):
        for predator in self.env.predators:
            predator.move_toward('S')
        self.update_render()

    def cmd_left(self, event=None):
        for predator in self.env.predators:
            predator.move_toward('W')
        self.update_render()

    def cmd_right(self, event=None):
        for predator in self.env.predators:
            predator.move_toward('E')
        self.update_render()

    def cmd_save(self, event=None):
        import json
        data = dict()
        #data['map'] = self.maps.grids.tolist()

        data['inst'] = self.win.instruction_text.toPlainText()
        for num, predator in enumerate(self.env.predators):
            data[str(num)] = {"pos": list(predator.history["pos"]), "act": list(predator.history["act"])}
        with open(f"{self.save_dir}" + "/sample.json", 'w', encoding="utf8") as f_in:
            json.dump(data, f_in, indent=4, ensure_ascii=False)

        self.screenshot(img_name=self.save_dir + "/screenshot.png")

    def cmd_clear(self, event=None):
        # TODO: clear的逻辑尚未实现
        pass

    def screenshot(self, key=None, img_name="screenshot.png"):
        # TODO: 用pyqt的方法截图
        # from PIL import ImageGrab
        # x = self.win.winfo_toplevel().winfo_rootx() * 1.25  # + canvas.winfo_x()
        # y = self.win.winfo_toplevel().winfo_rooty() * 1.25  # + canvas.winfo_y()
        # x1 = x + self.win.winfo_toplevel().winfo_width() * 1.25
        # y1 = y + self.win.winfo_toplevel().winfo_height() * 1.25
        # image = ImageGrab.grab((x, y, x1, y1))
        # # 保存屏幕截图
        # image.save(img_name)
        pass


if __name__ == "__main__":
    print(sys.argv)

    app = QApplication(sys.argv)
    MainWindow = MapVisualization()

    # ui.setupUi(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())
