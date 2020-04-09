#!/usr/bin/env python3

import sys
from lib.spctrl_base_controller import ship, send, debug

engine_on = True

while True:

    try:

        engine_on = not engine_on

        debug(ship.position)
        send(f'0:0: set-property intensity {4 if engine_on else 0}')

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(1)
