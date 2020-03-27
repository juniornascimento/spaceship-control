#!/usr/bin/env python3

import sys
from math import isclose

from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.joinpath('lib')))

from spctrl_base_controller import ship, send, debug

sys.__stderr__.flush()

debug(ship.device)

debug(sys.argv[1:])

REL_TOLERANCE = 0.2

def translate(msg):
    if len(msg) < 12:
        return ''

    first = msg[0]
    half_first = first/2

    if not isclose(msg[1], half_first, rel_tol=REL_TOLERANCE) or \
        not isclose(msg[2], first, rel_tol=REL_TOLERANCE) or \
        not isclose(msg[3], half_first, rel_tol=REL_TOLERANCE):

        return translate(msg[1:])

    result = 0
    for i in range(8):
        if isclose(msg[4 + i], first, rel_tol=REL_TOLERANCE):
            result += (1 << i)
        elif not isclose(msg[4 + i], half_first, rel_tol=REL_TOLERANCE):
            return translate(msg[1:])

    return chr(result) + translate(msg[12:])

while True:
    try:
        msg = send('0:0: get-received')
        if msg:
            values = tuple(float(i) for i in msg.split(','))
            debug('Received:', translate(values))

        ship.run(.25)
    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')
