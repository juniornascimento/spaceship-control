#!/usr/bin/env python3

import sys
from lib.spctrl_base_controller import ship, send, debug

debug(ship.device)

debug(sys.argv[1:])

while True:
    try:
        debug(send('0:0: get-received'))
        ship.run(.25)
    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')
