import dataclasses
import json

from david8.core.arg_convertors import to_col_or_expr
from david8.core.fn_generator import FnCallableFactory, Function
from david8.protocols.dialect import DialectProtocol
from david8.protocols.sql import ExprProtocol, FunctionProtocol


@dataclasses.dataclass(slots=True)
class JsonValuesFn(Function):
    operator: str
    column: str | ExprProtocol
    values: tuple[str, ...]

    def _render_operator_expr(self, dialect: DialectProtocol) -> str:
        return f"{to_col_or_expr(self.column, dialect)}{self.operator}"


@dataclasses.dataclass(slots=True)
class ExtractField(JsonValuesFn):
    def _get_sql(self, dialect: DialectProtocol) -> str:
        op_sql = self._render_operator_expr(dialect)
        items = self.operator.join(f"'{v}'" for v in self.values)
        return f"{op_sql}{items}"


@dataclasses.dataclass(slots=True)
class DelKey(JsonValuesFn):
    def _get_sql(self, dialect: DialectProtocol) -> str:
        op_sql = self._render_operator_expr(dialect)
        return f"{op_sql}'{self.values[0]}'"


@dataclasses.dataclass(slots=True)
class JsonbSet(Function):
    column: str | ExprProtocol
    path: list[str]
    value: str | int | dict

    def _get_sql(self, dialect: DialectProtocol) -> str:
        sql = to_col_or_expr(self.column, dialect)
        paths = ''.join(('{', ','.join(self.path), '}'))
        if isinstance(self.value, dict):
            value = ''.join(("'", json.dumps(self.value), "'"))
        elif isinstance(self.value, int):
            value = f"'{self.value}'::jsonb"
        else:
            value = f'\'"{self.value}"\'::jsonb'

        return f"jsonb_set({sql}, '{paths}', {value})"


@dataclasses.dataclass(slots=True)
class ExtractFieldFactory(FnCallableFactory):
    def __call__(self, column: str | ExprProtocol, *paths: str) -> FunctionProtocol:
        return ExtractField(name=self.name, column=column, operator='->', values=paths)


@dataclasses.dataclass(slots=True)
class HasKeyFactory(FnCallableFactory):
    def __call__(self, column: str | ExprProtocol, key: str) -> FunctionProtocol:
        return ExtractField(name=self.name, column=column, operator='?', values=(key, ))


@dataclasses.dataclass(slots=True)
class DelKeyFactory(FnCallableFactory):
    def __call__(self, column: str | ExprProtocol, key: str) -> FunctionProtocol:
        return DelKey(name=self.name, column=column, operator='-', values=(key, ))


@dataclasses.dataclass(slots=True)
class JsonbSetFactory(FnCallableFactory):
    def __call__(self, column: str | ExprProtocol, path: list[str], value: str | int | dict) -> FunctionProtocol:
        return JsonbSet(name='jsonb_set', column=column, path=path, value=value)
