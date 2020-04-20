
import ast

from simpleeval import SimpleEval, FeatureNotAvailable

class ExpressionEvaluator(SimpleEval):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.nodes[ast.Assign] = self._eval_assign
        self.nodes[ast.AugAssign] = self._eval_augassign
        self.nodes[ast.Expr] = lambda expr: self._eval(expr.value)

    @staticmethod
    def parse(expr):
        return ast.parse(expr.strip())

    def eval(self, expr, parsed_expr=False):

        if parsed_expr is False:
            expr = self.parse(expr).body
            self.expr = expr
        else:
            self.expr = '<<Parsed expression>>'

        expressions = expr.body

        for i in range(len(expressions) - 1):
            self.names['_'] = self._eval(expressions[i])

        return self._eval(expressions[-1])

    def _eval_assign(self, node):

        value = self._eval(node.value)
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                raise FeatureNotAvailable(
                    'Setting an attribute is forbidden')
            self.names[target.id] = value

        return value

    def _eval_augassign(self, node):

        value = self._eval(node.value)
        target = node.target

        if isinstance(target, ast.Attribute):
            raise FeatureNotAvailable(
                'Setting an attribute is forbidden')

        self.names[target.id] = self.operators[type(node.op)](
            self._eval(target), value)

        return value
