#!/usr/bin/env python3

import sys
from lib.spctrl_base_controller import ship, send, debug

debug(ship.device)

debug(sys.argv[1:])

while True:
    try:
        send('0:0: send-signal')
        ship.run(.25)
    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')
