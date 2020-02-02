
from collections import namedtuple

import toml

from pymunk import Body, Circle, Poly

from PyQt5.QtWidgets import QLabel, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..configfileinheritance import resolvePrefix

from ...utils.errorgenerator import ErrorGenerator

from ...interface.panelpushbutton import PanelPushButton
from ...interface.keyboardbutton import KeyboardButton

from ...devices.structure import Structure, StructuralPart
from ...devices.sensors import PositionSensor, AngleSensor, SpeedSensor
from ...devices.engine import LimitedLinearEngine
from ...devices.interfacedevice import (
    TextDisplayDevice, ButtonDevice, KeyboardReceiverDevice, ConsoleDevice
)

ShipConfig = namedtuple('ShipConfig', ('image'))

def __load_error(info: 'Dict[str, Any]') -> ErrorGenerator:

    return ErrorGenerator(error_max=info.get('error_max'),
                          offset_max=info.get('offset_max'),
                          error_max_minfac=info.get('error_max_minfac', 1))

def __load_error_dict(
    errors: 'Dict[str, Dict[str, Any]]') -> 'Dict[str, ErrorGenerator]':

    return {name: __load_error(info) for name, info in errors.items()}

def __engine_error_kwargs(
    errors: 'Dict[str, Dict[str, Any]]') -> 'Dict[str, ErrorGenerator]':

    if errors is None:
        return {}

    err_gens_dict = __load_error_dict(errors)

    return {
        'thrust_error_gen': err_gens_dict.get('Thrust'),
        'angle_error_gen': err_gens_dict.get('Angle'),
        'position_error_gen': err_gens_dict.get('Position')
    }

def __createCircleShape(info: 'Dict[str, Any]') -> 'Circle':

    shape = Circle(None, info['radius'],
                   (info.get('x', 0), info.get('y', 0)))

    shape.mass = info['mass']
    shape.elasticity = info.get('elasticity', 0.5)
    shape.friction = info.get('friction', 0.5)

    return shape

def __createPolyShape(info: 'Dict[str, Any]') -> 'Poly':

    points = tuple((point.get('x', 0), point.get('y', 0))
                   for point in info['Point'])
    shape = Poly(None, points)

    shape.mass = info['mass']
    shape.elasticity = info.get('elasticity', 0.5)
    shape.friction = info.get('friction', 0.5)

    return shape

__SHAPE_CREATE_FUNCTIONS = {

    'circle': __createCircleShape,
    'polygon': __createPolyShape
}

def __createShape(info: 'Dict[str, Any]') -> 'Shape':

    type_ = info.get('type')

    create_func = __SHAPE_CREATE_FUNCTIONS.get(type_)

    return create_func(info)

def __createLimitedLinearEngine(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[LimitedLinearEngine, Sequence[QWidget]]':

    return LimitedLinearEngine(part, info['min_intensity'],
                               info['max_intensity'], info['min_angle'],
                               info['max_angle'],
                               intensity_multiplier=info.get('intensity_mult',
                                                             1),
                               **__engine_error_kwargs(info.get('Error'))), ()

def __createPositionSensor(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[PositionSensor, Sequence[QWidget]]':

    return PositionSensor(part, info['reading_time'],
                          read_error_max=info.get('error_max', 0),
                          read_offset_max=info.get('offset_max', 0)), ()

def __createAngleSensor(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[AngleSensor, Sequence[QWidget]]':

    return AngleSensor(part, info['reading_time'],
                       read_error_max=info.get('error_max', 0),
                       read_offset_max=info.get('offset_max', 0)), ()

def __createSpeedSensor(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[AngleSensor, Sequence[QWidget]]':

    return SpeedSensor(part, info['reading_time'],
                       read_error_max=info.get('error_max', 0),
                       read_offset_max=info.get('offset_max', 0),
                       angle=info.get('angle', 0)), ()

def __createTextDisplay(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[TextDisplayDevice, Sequence[QWidget]]':

    label = QLabel('-')

    label.setStyleSheet('''

        background-color: white;
        border-color: black;
        border-width: 1px;
        border-style: solid;
        font-family: "Courier";

    ''')

    label.setGeometry(info.get('x', 0), info.get('y', 0),
                      info.get('width', 100), info.get('height', 30))

    return TextDisplayDevice(label), (label,)

def __createConsole(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[InterfaceDevice, Sequence[QWidget]]':

    text = QTextEdit()

    text.setReadOnly(True)

    text.setStyleSheet('''

        color: white;
        background-color: black;
        border-color: black;
        border-width: 1px;
        border-style: solid;
    ''')

    font = QFont('Monospace')
    font.setStyleHint(QFont.TypeWriter)
    text.setFont(font)

    text.setGeometry(info.get('x', 0), info.get('y', 0),
                     info.get('width', 100), 0)

    return (ConsoleDevice(text, info.get('columns', 20), info.get('rows', 5)),
            (text,))

def __createKeyboardReceiver(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[KeyboardButton, Sequence[QWidget]]':

    button = KeyboardButton()

    button.setGeometry(info.get('x', 0), info.get('y', 0), 20, 20)

    return KeyboardReceiverDevice(button), (button,)

def __createButton(info: 'Dict[str, Any]', part: StructuralPart) \
    -> 'Tuple[ButtonDevice, Sequence[QWidget]]':

    button = PanelPushButton()

    button.setFocusPolicy(Qt.NoFocus)

    button.setStyleSheet('background-color: red;')

    button.setGeometry(info.get('x', 0), info.get('y', 0), 50, 50)

    return ButtonDevice(button), (button,)

__DEVICE_CREATE_FUNCTIONS = {

    ('Actuator', 'engine', 'intensity_range'): __createLimitedLinearEngine,
    ('Sensor', 'position', None): __createPositionSensor,
    ('Sensor', 'angle', None): __createAngleSensor,
    ('Sensor', 'speed', None): __createSpeedSensor,
    ('InterfaceDevice', 'text-display', None): __createTextDisplay,
    ('InterfaceDevice', 'text-display', 'line'): __createTextDisplay,
    ('InterfaceDevice', 'text-display', 'console'): __createConsole,
    ('InterfaceDevice', 'button', None): __createButton,
    ('InterfaceDevice', 'keyboard', None): __createKeyboardReceiver
}

def __addDevice(
    info: 'Dict[str, Any]', parts: 'Dict[str, StructuralPart]',
    device_type: str) -> 'List[QWidget]':

    type_and_model = (device_type, info.get('type'), info.get('model'))
    create_func = __DEVICE_CREATE_FUNCTIONS.get(type_and_model)
    part = parts.get(info['part'])

    if create_func is None:
        type_and_model_str = f'{type_and_model[1]}/{type_and_model[2]}'
        raise ValueError(
            f'Invalid type/model for {device_type} \'{type_and_model_str}\'')

    device, widgets = create_func(info, part)
    part.addDevice(device, name=info.get('name'))

    return widgets

def loadShip(ship_info: str, name: str, space: 'pymunk.Space',
             prefixes: 'Sequence[str]' = ()) \
    -> 'Tuple[Structure, Sequence[QWidget]]':

    shapes = tuple(__createShape(shape_info)
                   for shape_info in ship_info['Shape'])

    mass = sum(shape.mass for shape in shapes)
    moment = sum(shape.moment for shape in shapes)

    body = Body(mass, moment)

    for shape in shapes:
        shape.body = body

    space.add(body, shapes)

    ship = Structure(name, space, body, device_type='ship')

    parts = {}
    for part_info in ship_info.get('Part', ()):
        part_name = part_info['name']
        part = StructuralPart(offset=(part_info['x'], part_info['y']))

        ship.addDevice(part, name=part_name)
        parts[part_name] = part

    for info in ship_info.get('Actuator', ()):
        __addDevice(info, parts, 'Actuator')

    for info in ship_info.get('Sensor', ()):
        __addDevice(info, parts, 'Sensor')

    widgets = []
    for info in ship_info.get('InterfaceDevice', ()):
        widgets.extend(
            __addDevice(info, parts, 'InterfaceDevice'))

    config_content = ship_info.get('Config')
    if config_content is None:
        config = ShipConfig(None)
    else:
        image_path = config_content.get('image')
        if image_path is not None:
            image_path, _ = resolvePrefix(image_path, prefixes)
        config = ShipConfig(image_path)

    return ship, config, widgets
