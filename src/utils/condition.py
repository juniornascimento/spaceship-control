
from simpleeval import simple_eval

class Condition:

    def __init__(self, expression: str) -> None:
        self.__expr = expression

    def evaluate(self, **kwargs: 'Any') -> 'Any':

        try:
            return bool(simple_eval(self.__expr, names=kwargs))
        except Exception:
            return False
