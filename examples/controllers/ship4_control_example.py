#!/usr/bin/env python3

import sys
from lib.spctrl_base_controller import ship, send, debug

engine_on = True
engine_not_reverse = 5

while True:

    val = 4

    try:

        engine_on = not engine_on
        if engine_not_reverse:
            engine_not_reverse -= 1
        else:
            val = -val
            engine_not_reverse = 5

        debug(ship.position)
        send(f'0:0: set-property intensity {val if engine_on else 0}')

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(1)
