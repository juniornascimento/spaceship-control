
import random

class ErrorGenerator:

    def __init__(self,
                 error_max: 'Union[float, int]',
                 offset_max: 'Union[float, int]',
                 error_max_minfac: 'Union[float, int]' = 1):

        if error_max_minfac != 1:
            error_max *= error_max_minfac + \
                random.random()*(1 - error_max_minfac)

        self.__error_max = error_max
        self.__offset_max = offset_max
        self.__offset = (2*random.random() - 1)*offset_max

    @property
    def max_error(self) -> 'Union[float, int]':
        return self.__error_max

    @property
    def max_offset(self) -> 'Union[float, int]':
        return self.__offset_max

    def __call__(self, val: 'Union[float, int]'):
        val += self.__offset
        if self.__error_max == 0:
            return val

        return val + (2*random.random() - 1)*self.__error_max
