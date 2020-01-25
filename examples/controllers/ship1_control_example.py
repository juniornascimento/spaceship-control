#!/usr/bin/env python3

from spctrl_base_controller import ship, send, debug

debug(ship.device)

colors = ('black', 'red', 'blue', 'green')
color_id = 0

print('\n   Spaceship Control')
print('\n\n This is just an example controller')

while True:
    try:
        if send('1:3: clicked') == '1':
            color_id += 1
            if color_id >= len(colors):
                color_id = 0

        debug(send('1:4: get'))

        debug('Speed:', send('0:3: read'))

        pos = ship.position
        angle = ship.angle
        intensity = -(pos[0] - 500) // 100
        send(f'0:0: set-property intensity {intensity}')
        debug(pos, intensity)
        ship.displayPrint(f'<font color={colors[color_id]}>{pos[0]:.1f}, '
                          f'{pos[1]:.1f} ({angle:.1f}º)</font>')

    except BrokenPipeError:
        break
    except Exception as err:
        debug(f'Error: {err}')

    ship.run(1)
