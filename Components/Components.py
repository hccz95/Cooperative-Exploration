#!/usr/bin/python
# -*-coding:utf-8-*-
# this file is based on https://github.com/RuoxiQin/Unmanned-Aerial-Vehicle-Tracking.git


class Component(object):
    '''This is the component in the game.'''
    _name = 'Component'

    def __init__(self, position, num, region_size):
        self.position = position
        self.num = num
        self._region_size = region_size
        super(Component, self).__init__()

    def __str__(self):
        return str(self._name) + str(self.num) + ' position' + str(self.position)


class MoveComponent(Component):
    '''This is the moveable component.'''
    _name = 'MoveComponent'

    def __init__(self, position, num, region_size, maps=None):
        super(MoveComponent, self).__init__(position, num, region_size)
        self.maps = maps

    def move(self, cmd):
        '''Input L,R,U,D  or S to move the component or stop. Rise exception if moving out of region.'''
        pos = self.next_position(cmd)
        if pos is None:
            return 'Invalid Move'
        elif self.maps.passable(pos[0], pos[1]):
            self.position = pos
            return 'Successful move'

    def next_position(self, cmd):
        position = None
        cmd = cmd.upper()
        if cmd == 'L':
            if self.position[1] - 1 >= 0:
                position = (self.position[0], self.position[1] - 1)
        elif cmd == 'R':
            if self.position[1] + 1 < self._region_size[1]:
                position = (self.position[0], self.position[1] + 1)
        elif cmd == 'U':
            if self.position[0] - 1 >= 0:
                position = (self.position[0] - 1, self.position[1])
        elif cmd == 'D':
            if self.position[0] + 1 < self._region_size[0]:
                position = (self.position[0] + 1, self.position[1])
        elif cmd == 'S':
            position = (self.position[0], self.position[1])
        return position

    def moveable_directions(self):
        r, c = self.position
        directions = []
        neighbors = []
        if self.maps.passable(r, c-1):
            directions.append('L')
            neighbors.append((r, c-1))
        if self.maps.passable(r, c+1):
            directions.append('R')
            neighbors.append((r, c+1))
        if self.maps.passable(r-1, c):
            directions.append('U')
            neighbors.append((r-1, c))
        if self.maps.passable(r+1, c):
            directions.append('D')
            neighbors.append((r+1, c))
        if len(directions) == 0:
            directions.append('S')
            neighbors.append((r, c))
        return directions, neighbors
