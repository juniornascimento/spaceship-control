
from abc import abstractmethod

from structure import Actuator
from utils import Interval, IntervalSet

class Engine(Actuator):

    def __init__(self, part: 'StructuralPart',
                 start_intensity: 'Union[float, int]' = 0,
                 start_angle: 'Union[float, int]' = 0,
                 thrust_error_gen: 'ErrorGenerator' = None,
                 angle_error_gen: 'ErrorGenerator' = None,
                 valid_intensities: 'utils.IntervalSet' = None,
                 valid_angles: 'utils.IntervalSet' = None):
        super().__init__(part, properties={'intensity': Engine.intensity,
                                           'angle': Engine.angle})

        self.__intensity = start_intensity
        self.__thrust = self.mapIntensityToThrust(self.__intensity)
        self.__angle = start_angle
        self.__thrust_error = thrust_error_gen
        self.__angle_error = angle_error_gen
        self.__valid_intensities = valid_intensities
        self.__valid_angles = valid_angles

    @property
    def intensity(self):
        return self.__intensity

    @intensity.setter
    def intensity(self, val):

        if isinstance(val, str):
            val = float(val)

        if self.__valid_intensities is None or \
            self.__valid_intensities.isInside(val):

            self.__intensity = val
            self.__thrust = self.mapIntensityToThrust(self.__intensity)

    @property
    def angle(self):
        return self.__angle

    @angle.setter
    def angle(self, val):

        if isinstance(val, str):
            val = float(val)

        if self.__valid_angles is None or \
            self.__valid_angles.isInside(val):

            self.__angle = val

    @abstractmethod
    def mapIntensityToThrust(self, intensity) -> 'Union[float, int]':
        pass

    def actuate(self) -> None:

        if self.__thrust_error is None:
            thrust = self.__thrust
        else:
            thrust = self.__thrust_error(self.__thrust)

        if self.__angle_error is None:
            angle = self.__angle
        else:
            angle = self.__angle_error(self.__angle_error)

        self.applyForce(thrust, 0, 0, angle)

class LinearEngine(Engine):

    def __init__(self, part: 'StructuralPart',
                 intensity_multiplier: 'Union[float, int]' = 1,
                 intensity_offset: 'Union[float, int]' = 0,
                 **kwargs: 'Any') -> None:

        self.__int_mult = intensity_multiplier
        self.__int_off = intensity_offset

        super().__init__(part, **kwargs)

    def mapIntensityToThrust(self, intensity) -> 'Union[float, int]':
        return self.__int_off + intensity*self.__int_mult

class LimitedLinearEngine(LinearEngine):

    def __init__(self, part: 'StructuralPart',
                 min_intensity: 'Union[float, int]',
                 max_intensity: 'Union[float, int]',
                 min_angle: 'Union[float, int]',
                 max_angle: 'Union[float, int]',
                 **kwargs: 'Any') -> None:

        valid_intensities = IntervalSet((Interval(min_intensity,
                                                  max_intensity),))
        valid_angles = IntervalSet((Interval(min_angle,
                                             max_angle),))

        super().__init__(part, valid_intensities=valid_intensities,
                         valid_angles=valid_angles, **kwargs)
