
import ast

from simpleeval import SimpleEval

class ExpressionEvaluator(SimpleEval):

    @staticmethod
    def parse(expr):
        return ast.parse(expr.strip())

    def eval(self, expr, parsed_expr=False):

        if parsed_expr is False:
            expr = self.parse(expr).body

        expressions = expr.body

        for i in range(len(expressions) - 1):
            self.names['_'] = self._eval(expressions[i].value)

        return self._eval(expressions[-1].value)
