
from math import pi
from collections import namedtuple
import toml

ShipInfo = namedtuple('ShipInfo', (
    'name', 'model', 'controller', 'position', 'angle'))

ScenarioInfo = namedtuple('ScenarioInfo', ('name', 'ships'))

def __readShipInfo(ship_content) -> 'ShipInfo':

    ship_info_kwargs = {

        'name': ship_content.get('name', '<<nameless>>'),
        'controller': ship_content['controller'],
        'model': ship_content['model'],
        'position': (ship_content.get('x', 0), ship_content.get('y', 0)),
        'angle': pi*ship_content.get('angle', 0)/180
    }

    return ShipInfo(**ship_info_kwargs)

def loadScenario(filename: str) -> 'ScenarioInfo':

    content = toml.load(filename)

    scenario_content = content.get('Scenario', {})

    s_name = scenario_content.get('name', '<<nameless>>')
    ships = tuple(__readShipInfo(ship) for ship in content.get('Ship', ()))

    return ScenarioInfo(name=s_name, ships=ships)
