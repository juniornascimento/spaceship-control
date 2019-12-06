
import toml

from pymunk import Body, Circle

from structure import Structure, StructuralPart
from positionsensor import PositionSensor
from engine import LimitedLinearEngine

def __createCircleShape(info: 'Dict[str, Any]') -> 'Circle':

    shape = Circle(None, info.get('radius', 0),
                   (info.get('x', 0), info.get('y', 0)))

    shape.mass = info['mass']
    shape.elasticity = info.get('elasticity', 0.5)
    shape.friction = info.get('friction', 0.5)

    return shape

__SHAPE_CREATE_FUNCTIONS = {

    'circle': __createCircleShape
}

def __createShape(info: 'Dict[str, Any]') -> 'Shape':

    type_ = info.get('type')

    create_func = __SHAPE_CREATE_FUNCTIONS.get(type_)

    return create_func(info)

def __createLimitedLinearEngine(
    info: 'Dict[str, Any]', part: StructuralPart) -> LimitedLinearEngine:

    return LimitedLinearEngine(part, info['min_intensity'],
                               info['max_intensity'], info['min_angle'],
                               info['max_angle'],
                               intensity_multiplier=info.get('intensity_mult',
                                                             1))

def __createPositionSensor(
    info: 'Dict[str, Any]', part: StructuralPart) -> PositionSensor:

    return PositionSensor(part, info['reading_time'],
                          read_error_max=info.get('error_max', 0),
                          read_offset_max=info.get('offset_max', 0))

__DEVICE_CREATE_FUNCTIONS = {

    ('Actuator', 'engine', 'intensity_range'): __createLimitedLinearEngine,
    ('Sensor', 'position', None): __createPositionSensor
}

def __addDevice(
    info: 'Dict[str, Any]',
    parts: 'Dict[str, StructuralPart]',
    device_type: str) -> 'Tuple[str, Device]':

    type_and_model = (device_type, info.get('type'), info.get('model'))
    create_func = __DEVICE_CREATE_FUNCTIONS.get(type_and_model)
    part = parts.get(info['part'])

    if create_func is None:
        type_and_model_str = f'{type_and_model[1]}/{type_and_model[2]}'
        raise ValueError(
            f'Invalid type/model for {device_type} \'{type_and_model_str}\'')

    part.addDevice(create_func(info, parts.get(info['part'])),
                   name=info.get('name'))

def loadShip(filename: str, space: 'pymunk.Space') -> Structure:

    file_content = toml.load(filename)

    shapes = tuple(__createShape(shape_info)
                   for shape_info in file_content['Shape'])

    mass = sum(shape.mass for shape in shapes)
    moment = sum(shape.moment for shape in shapes)

    body = Body(mass, moment)

    for shape in shapes:
        shape.body = body

    space.add(body, shapes)

    ship = Structure(space, body, device_type='ship')

    parts = {}
    for part_info in file_content.get('Part', ()):
        name = part_info['name']
        part = StructuralPart(offset=(part_info['x'], part_info['y']))

        ship.addDevice(part, name=name)
        parts[name] = part

    for info in file_content.get('Actuator', ()):
        __addDevice(info, parts, 'Actuator')

    for info in file_content.get('Sensor', ()):
        __addDevice(info, parts, 'Sensor')

    return ship
