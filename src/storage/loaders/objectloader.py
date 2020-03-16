
from collections import namedtuple

from pymunk import Body

from ..configfileinheritance import resolvePrefix

from .shapeloader import loadShapes

ImageInfo = namedtuple('ImageInfo', ('name', 'width', 'height'))
ObjectConfig = namedtuple('ObjectConfig', ('image',))

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

    return body, config
