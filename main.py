
import sys
import os
import random
import time
from threading import Thread, Lock
from subprocess import Popen, PIPE

import pygame
from pygame.locals import QUIT
from pygame.color import THECOLORS

import pymunk
import pymunk.pygame_util

from device import DeviceGroup, DefaultDevice
from structure import Structure, StructuralPart
from positionsensor import PositionSensor
from engine import LimitedLinearEngine

def start_controller(program, device, lock):

    process = Popen(program, stdin=PIPE,
                    stdout=PIPE)

    try:
        while process.poll() is None:
            question = process.stdout.readline().decode()

            if question and question[-1] == '\n':
                question = question[:-1]

            with lock:
                answer = device.communicate(question)

            process.stdin.write(answer.encode())
            process.stdin.write(b'\n')
            process.stdin.flush()

    except BrokenPipeError:
        pass

def main():

    lock = Lock()

    pygame.init()
    pygame.display.set_caption('Test')

    screen = pygame.display.set_mode((800, 600))
    draw_options = pymunk.pygame_util.DrawOptions(screen)


    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0, 0)

    mass = 10
    radius = 50
    inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
    body = pymunk.Body(mass, inertia)
    body.position = 300, 400
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.elasticity = 0.95
    shape.friction = 0.9
    space.add(body, shape)

    ship = Structure(space, body, device_type='ship')

    part = StructuralPart()
    part2 = StructuralPart(offset=(0, 25))

    ship.addDevice(part, name='part')
    ship.addDevice(part2, name='part2')

    part.addDevice(PositionSensor(part, 1, read_error_max=100,
                                  read_offset_max=40))

    part.addDevice(LimitedLinearEngine(part, -4, 4, 0, 0), name='engine')
    part2.addDevice(LimitedLinearEngine(part2, -4, 4, 0, 0,
                                        intensity_multiplier=4), name='engine2')
    part2.addDevice(LimitedLinearEngine(part2, -4, 4, 0, 0), name='engine3')

    t = Thread(target=start_controller,
            args=(['/usr/bin/python3', 'test/child.py'], ship, lock))
    t.start()

    ships = [ship]
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                os._exit(0)

        with lock:
            for ship in ships:
                ship.act()
            space.step(0.02)

        screen.fill(THECOLORS['white'])
        space.debug_draw(draw_options)
        pygame.display.flip()

        clock.tick(50)

if __name__ == '__main__':
    main()
