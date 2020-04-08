
import ast

from simpleeval import SimpleEval

class ExpressionEvaluator(SimpleEval):

    def eval(self, expr):
        self.expr = expr

        expressions = ast.parse(expr.strip()).body

        for i in range(len(expressions) - 1):
            self.names['_'] = self._eval(expressions[i].value)

        return self._eval(expressions[-1].value)
