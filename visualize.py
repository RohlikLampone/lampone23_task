import time

from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class Visualization:
    def __init__(self):
        self.iteration = 0
        self.posit = (0, 0)
        self.stposor = [(0, 0), 0]
        self.orient = 0
        self.orients = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        self.robot = Image.open("assets/robot.png")
        self.arrow = Image.open("assets/arrow.png")
        self.blue_square = Image.open("assets/blue_square.png")
        self.green_square = Image.open("assets/green_square.png")
        self.red_square = Image.open("assets/red_square.png")
        self.red_star = Image.open("assets/red_star.png")

    def render_pole(self, pole, cellsize):

        rows = len(pole)
        cols = len(pole[0])

        final = Image.new("RGB", (cols * cellsize, rows * cellsize), (255, 255, 255))

        # Draw some lines
        draw = ImageDraw.Draw(final)
        x_start, y_start = 0, 0
        x_end, y_end = final.width, final.height

        # Draw columns:
        for x in range(0, x_end + 1, cellsize):
            line = ((x - 1, y_start), (x - 1, y_end))
            draw.line(line, fill=(127, 127, 127), width=10)

        # Draw rows:
        for y in range(0, y_end + 1, cellsize):
            line = ((x_start, y - 1), (x_end, y - 1))
            draw.line(line, fill=(127, 127, 127), width=10)

        del draw

        for j, row in enumerate(pole):
            for i, cell in enumerate(row):
                x, y = i * cellsize + 5, j * cellsize + 5
                if all(cell == ["blue", "square"]):
                    final.paste(self.blue_square, (x, y), self.blue_square)
                elif all(cell == ["green", "square"]):
                    final.paste(self.green_square, (x, y), self.green_square)
                elif all(cell == ["red", "square"]):
                    final.paste(self.red_square, (x, y), self.red_square)
                elif all(cell == ["red", "star"]):
                    final.paste(self.red_star, (x, y), self.red_star)

        return final

    def visualize(self, pole, path, render_list):
        arr_ori = 0
        arr_oris = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        arr_pos = (0, 0)

        cellsize = 100

        final = self.render_pole(pole, cellsize)

        [j], [i], [_] = np.where(pole == "robot")

        x, y = i * cellsize + 5, j * cellsize + 5

        orient = int(pole[j][i][1])
        rob_tmp = self.robot.rotate(-90 * orient, Image.NEAREST, expand=True)
        final.paste(rob_tmp, (x, y), rob_tmp)

        arr_pos = (i, j)
        arr_tmp = self.arrow.rotate(-90 * orient, Image.NEAREST, expand=True)
        arr_ori = orient

        for char in path:
            if char == "L":
                arr_tmp = arr_tmp.rotate(90, Image.NEAREST, expand=True)
                arr_ori -= 1
            elif char == "R":
                arr_tmp = arr_tmp.rotate(-90, Image.NEAREST, expand=True)
                arr_ori += 1
            elif char == "F":
                final.paste(arr_tmp, (arr_pos[0] * cellsize + 5, arr_pos[1] * cellsize + 5), arr_tmp)
                arr_pos = (arr_pos[0] + arr_oris[arr_ori][0], arr_pos[1] + arr_oris[arr_ori][1])
            arr_ori %= 4

        render_list.append([final, "lolik", False])

    def animation(self, pole, path):

        cellsize = 100

        final = self.render_pole(pole, cellsize)
        fig, ax = plt.subplots()
        ax.set_xlim(0, len(pole[0]))
        ax.set_ylim(len(pole), 0)
        ax.imshow(final, extent=[0, len(pole[0]), len(pole), 0])

        [y], [x], [_] = np.where(pole == "robot")

        self.orient = int(pole[y][x][1])
        sprite = plt.imshow(self.robot, extent=[x+0.05, x+0.95, y+0.95, y+0.05])
        sprite.set_data(np.rot90(self.robot, k=self.orient, axes=(1, 0)))
        print(self.orient)
        self.posit = (x, y)
        self.stposor = self.posit, self.orient
        self.iteration = len(path)

        def update(frame):
            if self.iteration >= len(path):
                self.iteration = 0
                self.posit, self.orient = self.stposor
                x, y = self.posit
                sprite.set_extent([x + 0.05, x + 0.95, y + 0.95, y + 0.05])
                sprite.set_data(np.rot90(self.robot, k=self.orient, axes=(1, 0)))
                return

            char = path[self.iteration]
            if char == "L":
                self.orient -= 1
                sprite.set_data(np.rot90(self.robot, k=self.orient, axes=(1, 0)))

            elif char == "R":
                self.orient += 1
                sprite.set_data(np.rot90(self.robot, k=self.orient, axes=(1, 0)))

            elif char == "F":
                self.posit = (self.posit[0] + self.orients[self.orient][0], self.posit[1] + self.orients[self.orient][1])
                x, y = self.posit
                sprite.set_extent([x+0.05, x+0.95, y+0.95, y+0.05])
            self.orient %= 4
            self.iteration += 1

        ani = FuncAnimation(fig, update, frames=len(path), interval=500)
        ani.save("ANIMACEVOLE.gif", "imagemagick", fps=2)

        plt.axis('off')
        plt.show()
