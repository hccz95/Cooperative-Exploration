import numpy as np
from Components.Components import MoveComponent


class Predator(MoveComponent):
    '''This is the class of intruder.'''
    _name = 'Predator'

    # def __init__(self, position, num, region_size, sight, maps=None, grids=None):
    #     super(Predator, self).__init__(position, num, region_size, maps, grids)

    def __init__(self, position, num, region_size, sight=1, maps=None):
        super(Predator, self).__init__(position, num, region_size, maps)
        self.__region_size = region_size
        self.__sight = sight
        self.maps = maps

        self.visit()

    def visit(self):
        r, c = self.position
        self.maps.cell_visited[r][c] = 1

    def move(self):
        probs = []
        cmd_list, neighbor_list = self.moveable_directions()
        for cmd, nb in zip(cmd_list, neighbor_list):
            r, c = nb
            probs.append(1.0)
        probs = np.array(probs) / sum(probs)
        cmd = np.random.choice(cmd_list, p=probs)

        super(Predator, self).move(cmd)
        self.maps.cell_visited[self.position[0]][self.position[1]] = 1
