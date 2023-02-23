"""
A_star 2D
@author: huiming zhou
This file is based on https://github.com/zhm-real/PathPlanning/blob/master/Search_based_Planning/Search_2D/Astar.py
"""

from collections import deque
import math
import heapq

motions = [(-1, 0), (0, 1), (1, 0), (0, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)]


class AStar:
    """AStar set the cost + heuristics as the priority
    """
    def __init__(self, maps, heuristic_type="manhattan"):
        self.maps = maps
        self.s_start = None
        self.s_goal = None
        self.heuristic_type = heuristic_type

        if self.heuristic_type == "manhattan":
            self.u_set = motions[:4]  # feasible input set
        else:
            self.u_set = motions

        self.OPEN = []  # priority queue / OPEN set
        self.CLOSED = []  # CLOSED set / VISITED order
        self.PARENT = dict()  # recorded parent
        self.g = dict()  # cost to come

    def searching(self, s_start, s_goal):
        """
        A_star Searching.
        :return: path, visited order
        """
        self.s_start = s_start
        self.s_goal = s_goal

        self.OPEN = []  # priority queue / OPEN set
        self.CLOSED = []  # CLOSED set / VISITED order
        self.PARENT = dict()  # recorded parent
        self.g = dict()  # cost to come

        self.PARENT[self.s_start] = self.s_start
        self.g[self.s_start] = 0
        self.g[self.s_goal] = math.inf
        heapq.heappush(self.OPEN,
                       (self.f_value(self.s_start), self.s_start))
        found = False
        while self.OPEN:
            _, s = heapq.heappop(self.OPEN)
            self.CLOSED.append(s)

            if s == self.s_goal:  # stop condition
                found = True
                break

            for s_n in self.get_neighbor(s):
                new_cost = self.g[s] + self.cost(s, s_n)

                if s_n not in self.g:
                    self.g[s_n] = math.inf

                if new_cost < self.g[s_n]:  # conditions for updating Cost
                    self.g[s_n] = new_cost
                    self.PARENT[s_n] = s
                    heapq.heappush(self.OPEN, (self.f_value(s_n), s_n))
        if found:
            return self.extract_path(self.PARENT)
        else:
            return []

    def get_neighbor(self, s):
        """
        find neighbors of state s that not in obstacles.
        :param s: state
        :return: neighbors
        """

        return [(s[0] + u[0], s[1] + u[1]) for u in self.u_set]

    def cost(self, s_start, s_goal):
        """
        Calculate Cost for this motion
        :param s_start: starting node
        :param s_goal: end node
        :return:  Cost for this motion
        :note: Cost function could be more complicate!
        """

        if self.is_collision(s_start, s_goal):
            return math.inf

        return math.hypot(s_goal[0] - s_start[0], s_goal[1] - s_start[1])

    def is_collision(self, s_start, s_end):
        """
        check if the line segment (s_start, s_end) is collision.
        :param s_start: start node
        :param s_end: end node
        :return: True: is collision / False: not collision
        """

        if self.maps.obstacle(s_start[0], s_start[1]) or self.maps.obstacle(s_end[0], s_end[1]):
            return True
        if not self.maps.cell_visable[s_start[0]][s_start[1]] or not self.maps.cell_visable[s_end[0]][s_end[1]]:
            return True

        if s_start[0] != s_end[0] and s_start[1] != s_end[1]:
            if s_end[0] - s_start[0] == s_start[1] - s_end[1]:
                s1 = (min(s_start[0], s_end[0]), min(s_start[1], s_end[1]))
                s2 = (max(s_start[0], s_end[0]), max(s_start[1], s_end[1]))
            else:
                s1 = (min(s_start[0], s_end[0]), max(s_start[1], s_end[1]))
                s2 = (max(s_start[0], s_end[0]), min(s_start[1], s_end[1]))

            # if s1 in self.obs or s2 in self.obs:
            if self.maps.obstacle(s1[0], s1[1]) or self.maps.obstacle(s2[0], s2[1]):
                return True

        return False

    def f_value(self, s):
        """
        f = g + h. (g: Cost to come, h: heuristic value)
        :param s: current state
        :return: f
        """

        return self.g[s] + self.heuristic(s)

    def extract_path(self, PARENT):
        """
        Extract the path based on the PARENT set.
        :return: The planning path
        """

        path = [self.s_goal]
        s = self.s_goal

        while True:
            s = PARENT[s]
            if s == self.s_start:
                break

            path.append(s)
        path.reverse()
        return deque(path)

    def heuristic(self, s):
        """
        Calculate heuristic.
        :param s: current node (state)
        :return: heuristic function value
        """

        heuristic_type = self.heuristic_type  # heuristic type
        goal = self.s_goal  # goal node

        if heuristic_type == "manhattan":
            return abs(goal[0] - s[0]) + abs(goal[1] - s[1])
        else:
            return math.hypot(goal[0] - s[0], goal[1] - s[1])


def main():
    from Components.Map import Map
    from utils import load_grids
    map_file = 'maps/mts2.map'
    grids = load_grids(map_file)
    maps = Map(grids)

    s_start = (2, 15)
    s_goal = (7, 15)

    astar = AStar(maps, s_start, s_goal, "manhattan")
    # plot = plotting.Plotting(s_start, s_goal)

    path = astar.searching()
    # plot.animation(path, visited, "A*")  # animation

    # path, visited = astar.searching_repeated_astar(2.5)               # initial weight e = 2.5
    # plot.animation_ara_star(path, visited, "Repeated A*")

    grids = astar.maps.grids
    for r in range(grids.shape[0]):
        for c in range(grids.shape[1]):
            print(grids[r][c], end='')
        print('')

    print(path)

    for r, c in path:
        grids[r][c] = 'O'

    for r in range(grids.shape[0]):
        for c in range(grids.shape[1]):
            print(grids[r][c], end='')
        print('')



if __name__ == '__main__':
    main()
