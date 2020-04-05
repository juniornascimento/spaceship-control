
from .expressionevaluator import ExpressionEvaluator

class Condition:

    def __init__(self, expression: str) -> None:
        self.__expr = expression
        self.__evaluator = ExpressionEvaluator()

    def evaluate(self, **kwargs: 'Any') -> 'Any':

        try:
            return bool(self.__evaluator.eval(self.__expr, names=kwargs))
        except Exception:
            return False
