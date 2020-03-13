
from pymunk import Circle, Poly

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

def loadShapes(info_list: 'Sequence[Dict[str, Any]]') -> 'Tuple[Shape, ...]':
    return tuple(__createShape(shape_info)
                 for shape_info in info_list)
