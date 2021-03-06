
from abc import abstractmethod

import time
import math

from pymunk import Vec2d

from .device import DeviceGroup, DefaultDevice

from ..utils.errorgenerator import ErrorGenerator

class Structure(DeviceGroup):

    def __init__(self, name: str, space: 'pymunk.Space', body: 'pymunk.Body',
                 **kwargs: 'Any') -> None:

        if 'device_type' not in kwargs:
            kwargs['device_type'] = 'structure'

        super().__init__(**kwargs)

        self.__body = body
        self.__space = space
        self.__name = name

    @property
    def name(self) -> str:
        return self.__name

    def addDevice(self, device: 'Device', **kwargs: 'Any') -> None: # pylint: disable=arguments-differ
        super().addDevice(device, **kwargs)

        if isinstance(device, StructuralPart):
            device.structure = self

    def isDestroyed(self) -> bool:
        return self.__body.space is None

    @property
    def body(self) -> 'pymunk.Body':
        return self.__body

    @property
    def space(self) -> 'pymunk.Space':
        return self.__space

class StructuralPart(DeviceGroup):

    def __init__(self,
                 structure: Structure = None,
                 offset: 'Tuple[Union[int, float], Union[int, float]]' = (0, 0),
                 **kwargs: 'Any') -> None:

        if 'device_type' not in kwargs:
            kwargs['device_type'] = 'structural-part'

        super().__init__(**kwargs)

        self.__offset = offset
        self.__structure = structure

    def applyForce(self, val, x, y, angle) -> None:

        if self.__structure is None:
            return

        body = self.__structure.body
        body_angle = body.angle

        body.apply_impulse_at_local_point((math.cos(angle)*val,
                                           math.sin(angle)*val), self.__offset)

    @property
    def position(self) -> 'Tuple[float, float]':
        if self.__structure is None:
            return self.__offset
        pos = self.__structure.body.position
        return pos.x + self.__offset[0], pos.y + self.__offset[1]

    @property
    def angle(self) -> float:
        if self.__structure is None:
            return 0
        return self.__structure.body.angle

    @property
    def velocity(self) -> 'Tuple[float, float]':
        if self.__structure is None:
            return self.__offset
        return tuple(self.__structure.body.velocity)

    @property
    def structure(self) -> Structure:
        return self.__structure

    @structure.setter
    def structure(self, structure: Structure) -> None:
        self.__structure = structure

    @property
    def offset(self) -> 'Tuple[Union[int, float], Union[int, float]]':
        return self.__offset

class Sensor(DefaultDevice):

    def __init__(self, st_part: StructuralPart,
                 read_time: 'Union[float, int]',
                 read_error_max: 'Union[float, int]' = 0,
                 read_offset_max: 'Union[float, int]' = 0,
                 **kwargs: 'Any') -> None:
        super().__init__(**kwargs)

        self.__st_part = st_part
        self.__last_read_time = 0
        self.__last_value = None
        self.__read_time = read_time
        self.__error_gen = ErrorGenerator(read_error_max, read_offset_max)

    @property
    def structural_part(self) -> Structure:
        return self.__st_part

    @property
    def reading_time(self) -> 'Union[float, int]':
        return self.__read_time

    @property
    def max_read_error(self) -> 'Union[float, int]':
        return self.__error_gen.max_error + self.__error_gen.max_offset

    @property
    def max_read_offset(self) -> 'Union[float, int]':
        return self.__error_gen.max_offset

    def act(self) -> None:
        pass

    def command(self, command: 'List[str]', *args) -> 'Any':
        return super().command(command, Sensor.__COMMANDS, *args)

    def __read(self) -> float:
        now = time.time()

        if now - self.__last_read_time > self.__read_time:
            self.__last_value = self.__error_gen(self.read())
            self.__last_read_time = now

        return self.__last_value

    @abstractmethod
    def read(self) -> 'Union[int, float]':
        pass

    __COMMANDS = {

        'read': __read,
        'reading-time': reading_time.fget,
        'max-error': max_read_error.fget,
        'max-offset': max_read_offset.fget
    }

class MultiSensor(DeviceGroup):

    def __init__(self, sensors: 'Dict[str, Type[Sensor]]',
                 st_part: 'StructuralPart',
                 read_time: 'Union[float, int]',
                 read_error_max: 'Union[float, int]' = 0,
                 read_offset_max: 'Union[float, int]' = 0,
                 **kwargs: 'Any'):
        super().__init__(**kwargs)

        self.__sensors = []
        for sensor_name, sensor_type in sensors.items():
            self.__sensors.append(sensor_type(st_part, read_time,
                                              read_error_max=read_error_max,
                                              read_offset_max=read_offset_max))
            self.addDevice(self.__sensors[-1], name=sensor_name)

    def command(self, command: 'List[str]', *args) -> 'Any':
        if self.__sensors and command and \
            command[0] in MultiSensor.__REDIRECT_COMMANDS:

            return self.__sensors[0].command(command)

        return super().command(command, *args)

    __REDIRECT_COMMANDS = {'reading-time', 'max-error', 'max-offset'}

class Actuator(DefaultDevice):

    def __init__(self, part: StructuralPart, **kwargs: 'Any') -> None:
        super().__init__(**kwargs)

        self.__part = part

    def applyForce(self, val, x, y, angle) -> None:
        self.__part.applyForce(val, x, y, angle)

    @property
    def structural_part(self) -> StructuralPart:
        return self.__part

    def act(self) -> None:
        self.actuate()

    @abstractmethod
    def actuate(self) -> None:
        pass
