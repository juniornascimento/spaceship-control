
from math import pi
from collections import namedtuple

from ..configfileinheritance import resolvePrefix
from ...objectives.objective import ObjectiveGroup
from ...objectives.gotoobjective import GoToObjective

ShipInfo = namedtuple('ShipInfo', (
    'name', 'model', 'controller', 'position', 'angle'))

ScenarioInfo = namedtuple('ScenarioInfo', (
    'name', 'ships', 'objectives', 'visible_user_interface'))

def __createGoToObjective(objective_content) -> 'GoToObjective':

    position = (objective_content['x'], objective_content['y'])
    distance = objective_content['distance']

    kwargs = {key: value for key, value in objective_content.items()
              if key in ('name', 'description')}

    return GoToObjective(position, distance, **kwargs)

def __createObjectiveGroup(objective_content) -> 'ObjectiveGroup':

    kwargs = {key: value for key, value in objective_content.items()
              if key in ('name', 'description')}

    return ObjectiveGroup(loadObjectives(objective_content['Objective']),
                          **kwargs)

__OBJECTIVE_CREATE_FUNCTIONS = {

    'goto': __createGoToObjective,
    'list': __createObjectiveGroup
}

def __readShipInfo(ship_content, prefixes) -> 'ShipInfo':

    model = ship_content.get('model')
    if model is not None:
        model, _ = resolvePrefix(model, prefixes)

        if model is None:
            raise ValueError(f'Ship model not found')

    controller = ship_content.get('controller')

    if controller is not None:
        controller, _ = resolvePrefix(controller, prefixes)

    ship_info_kwargs = {

        'name': ship_content.get('name', '<<nameless>>'),
        'controller': controller,
        'model': model,
        'position': (ship_content.get('x', 0), ship_content.get('y', 0)),
        'angle': pi*ship_content.get('angle', 0)/180
    }

    return ShipInfo(**ship_info_kwargs)

def loadObjectives(objectives):
    return tuple(__OBJECTIVE_CREATE_FUNCTIONS[objective['type']](objective)
                 for objective in objectives)

def loadScenario(scenario_info: 'Dict[str, Any]',
                 prefixes=()) -> 'ScenarioInfo':

    scenario_content = scenario_info.get('Scenario', {})

    s_name = scenario_content.get('name', '<<nameless>>')
    ships = tuple(__readShipInfo(ship, prefixes)
                  for ship in scenario_info.get('Ship', ()))

    objectives = loadObjectives(scenario_info.get('Objective', ()))

    hidden_user_interface = scenario_content.get('hide_user_interface', False)

    return ScenarioInfo(name=s_name, ships=ships, objectives=objectives,
                        visible_user_interface=not(hidden_user_interface))
