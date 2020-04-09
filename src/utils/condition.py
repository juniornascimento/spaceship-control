
from .expressionevaluator import ExpressionEvaluator

class Condition:

    def __init__(self, expression: str) -> None:
        self.__expr = ExpressionEvaluator.parse(expression)
        self.__evaluator = ExpressionEvaluator()

    def evaluate(self, **kwargs: 'Any') -> 'Any':

        self.__evaluator.names = kwargs

        try:
            return bool(self.__evaluator.eval(self.__expr, parsed_expr=True))
        except Exception:
            return False
