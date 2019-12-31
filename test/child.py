
import time
import sys

import collections

__device_comm_write = sys.__stdout__
__device_comm_read = sys.__stdin__

sys.stdout = sys.stderr
sys.stdin = None

class Device:

    def __init__(self, device_path=''):

        self.__device_path = device_path

        if self.sendMessage('get-info is-device-group') == 'yes':

            children_count = int(self.sendMessage('device-count'))

            if device_path == '':
                dev_path_prefix = ':'
            else:
                dev_path_prefix = device_path

            self.__children = tuple(Device(device_path=f'{device_path}{i}:')
                                    for i in range(children_count))
        else:
            self.__children = None

        self.__device_type = self.sendMessage('device-type')
        self.__device_desc = self.sendMessage('device-desc')
        self.__device_name = self.sendMessage(
            'get-info device-name-in-group')
        if self.__device_name == '<<null>>':
            self.__device_name = self.__device_type

    @property
    def children(self):
        return self.__children

    @property
    def type_(self):
        return self.__device_type

    @property
    def name(self):
        return self.__device_name

    @property
    def description(self):
        return self.__device_desc

    def __get_repr(self, depth=0):

        spaces = '  '*depth
        prefix = spaces + self.__device_name

        if self.__children is None:
            return prefix

        children_repr = (child.__get_repr(depth+1) for child in self.__children)
        return prefix + ': {\n' + ',\n'.join(children_repr) + f'\n{spaces}}}'

    def __repr__(self):
        return self.__get_repr()

    def sendMessage(self, message):
        return send(self.__device_path + message)

SensorInfo = collections.namedtuple('SensorInfo', ('reading_time',
                                                    'max_error',
                                                    'max_offset',
                                                    'estimated_offset'))

class Ship:

    def __init__(self):
        self.__device = Device()
        self.__position_devices = []
        self.__find_position_devices(self.__device)

    @property
    def position(self):
        if not self.__position_devices:
            return None

        device = self.__position_devices[0][0]

        return (float(device.sendMessage('x:read')),
                float(device.sendMessage('y:read')))

    @property
    def device(self):
        return self.__device

    def __find_position_devices(self, device):

        if device.type_ == 'position-sensor':
            reading_time = float(device.sendMessage('reading-time'))
            max_offset = float(device.sendMessage('max-offset'))
            max_error = float(device.sendMessage('max-error')) - max_offset
            info = SensorInfo(reading_time=reading_time,
                              max_error=max_error,
                              max_offset=max_offset,
                              estimated_offset=0)
            self.__position_devices.append((device, info))
            return

        children = device.children
        if children is None:
            return

        for child in device.children:
            self.__find_position_devices(child)

def send(message):

    __device_comm_write.write(message)
    __device_comm_write.write('\n')
    __device_comm_write.flush()

    return __device_comm_read.readline()[:-1]

ship = Ship()

print(ship.device)

try:
    send(f'1:2: set-text "apenas testando."')
    while True:
        pos = ship.position
        intensity = -(pos[0] - 500) // 100
        send(f'0:0: set-property intensity {intensity}')
        print(pos, intensity)
        time.sleep(1)
except BrokenPipeError:
    pass
