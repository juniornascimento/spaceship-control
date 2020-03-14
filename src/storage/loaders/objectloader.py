
from collections import namedtuple

from pymunk import Body

from ..configfileinheritance import resolvePrefix

from .shapeloader import loadShapes

ImageInfo = namedtuple('ImageInfo', ('name', 'width', 'height'))
ObjectConfig = namedtuple('ObjectConfig', ('image',))

def loadObject(obj_info: str, space: 'pymunk.Space',
               prefixes: 'Sequence[str]' = ()) \
    -> 'Tuple[Structure, Sequence[QWidget]]':

    shapes = loadShapes(ship_info['Shape'])

    mass = sum(shape.mass for shape in shapes)
    moment = sum(shape.moment for shape in shapes)

    body = Body(mass, moment)

    for shape in shapes:
        shape.body = body

    space.add(body, shapes)

    config_content = ship_info.get('Config')
    if config_content is None:
        config = ObjectConfig(None)
    else:
        image_config = config_content.get('Image')

        image_info = None
        if image_config is not None:
            image_path = image_config.get('path')
            if image_path is not None:
                image_path, _ = resolvePrefix(image_path, prefixes)
                image_info = ImageInfo(image_path, image_config.get('width'),
                                       image_config.get('height'))

        config = ObjectConfig(image_info)

    ObjectInfo(body=body, shapes=shapes, image=)

    return body, shapes, config, widgets
