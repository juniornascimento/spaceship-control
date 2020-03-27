#!/usr/bin/env python3

import sys
import random

from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.joinpath('lib')))

from spctrl_base_controller import ship, send, debug

debug(ship.device)

debug(sys.argv[1:])

HIGH_INTENSITY = 20000000

def send_bit(bit):
    send(f'0:0: set-intensity {HIGH_INTENSITY if bit else HIGH_INTENSITY//2}')
    send('0:0: send-signal')

def send_char(char):
    value = ord(char)
    send_bit(1)
    send_bit(0)
    send_bit(1)
    send_bit(0)
    for i in range(8):
        send_bit((value & (1 << i)) >> i)

while True:
    try:
        char = chr(random.randint(ord('A'), ord('Z')))
        debug(f'Sending: {char}')
        send_char(char)
        ship.run(.25)
    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')
