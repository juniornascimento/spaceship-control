
from collections import namedtuple

from pymunk import Body

from ..configfileinheritance import resolvePrefix

from .shapeloader import loadShapes
from .imageloader import loadImages

ObjectInfo = namedtuple('ObjectInfo', ('body', 'images'))

def loadObject(obj_info: str, space: 'pymunk.Space',
               prefixes: 'Sequence[str]' = ()) \
    -> 'Tuple[Structure, Sequence[QWidget]]':

    config_content = obj_info.get('Config', {})

    if config_content is None:
        is_static = False
    else:
        is_static = config_content.get('static', False)

    shapes = loadShapes(obj_info['Shape'])

    if is_static is True:

        body = Body(body_type=Body.STATIC)

        for shape in shapes:
            shape.body = body

        space.add(shapes)

    else:
        mass = sum(shape.mass for shape in shapes)
        moment = sum(shape.moment for shape in shapes)

        body = Body(mass, moment)

        for shape in shapes:
            shape.body = body

        space.add(body, shapes)

    return ObjectInfo(body, loadImages(obj_info.get('Image', ()),
                                       prefixes=prefixes))
