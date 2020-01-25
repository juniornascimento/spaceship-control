
import itertools
from math import pi
from collections import namedtuple
import toml

ShipInfo = namedtuple('ShipInfo', (
    'name', 'model', 'controller', 'position', 'angle'))

ScenarioInfo = namedtuple('ScenarioInfo', ('name', 'ships'))

def __subPrefix(name, prefixes, error_msg):

    for dot_count, char in enumerate(name):
        if char != '.':
            break
    else:
        raise ValueError(error_msg)

    if dot_count == 0:
        return name

    parent_returns = dot_count - 1

    if parent_returns > len(prefixes):
        raise ValueError(error_msg)

    return '/'.join(itertools.chain(prefixes[: len(prefixes) - parent_returns],
                                    (name[dot_count:],)))

def __readShipInfo(ship_content, prefixes) -> 'ShipInfo':

    model = ship_content['model']
    model = __subPrefix(model, prefixes, f'Invalid model \'{model}\'')

    controller = ship_content['controller']
    controller = __subPrefix(controller, prefixes,
                             f'Invalid controller \'{controller}\'')

    if model is None:
        raise ValueError(f'Invalid ship model ')

    ship_info_kwargs = {

        'name': ship_content.get('name', '<<nameless>>'),
        'controller': controller,
        'model': model,
        'position': (ship_content.get('x', 0), ship_content.get('y', 0)),
        'angle': pi*ship_content.get('angle', 0)/180
    }

    return ShipInfo(**ship_info_kwargs)

def loadScenario(filename: str, prefixes=()) -> 'ScenarioInfo':

    content = toml.load(filename)

    scenario_content = content.get('Scenario', {})

    s_name = scenario_content.get('name', '<<nameless>>')
    ships = tuple(__readShipInfo(ship, prefixes)
                  for ship in content.get('Ship', ()))

    return ScenarioInfo(name=s_name, ships=ships)
