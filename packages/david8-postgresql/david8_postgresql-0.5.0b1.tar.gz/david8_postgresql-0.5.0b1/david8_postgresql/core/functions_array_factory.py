import dataclasses

from david8.core.fn_generator import FnCallableFactory, SeparatedArgsFn
from david8.expressions import val
from david8.protocols.sql import ExprProtocol, FunctionProtocol


@dataclasses.dataclass(slots=True)
class StrSeparatedArgsFactory(FnCallableFactory):
    def __call__(self, *args: str | ExprProtocol) -> FunctionProtocol:
        return SeparatedArgsFn(self.name, fn_items=args, separator=', ')


@dataclasses.dataclass(slots=True)
class Col2AnyArgsFactory(FnCallableFactory):
    """
    array_remove(column, 2) | array_remove(column, "name")
    """
    def __call__(self, column: str | ExprProtocol, arg: str | float | int | ExprProtocol) -> FunctionProtocol:
        param = val(arg) if isinstance(arg, str) else arg
        return SeparatedArgsFn(self.name, fn_items=(column, param), separator=', ', numbers_as_str=False)


@dataclasses.dataclass(slots=True)
class Col3AnyArgsFactory(FnCallableFactory):
    """
     array_replace(column, 1, 2) | array_replace(column, "old", "new")
    """
    def __call__(
        self,
        column: str | ExprProtocol,
        arg: str | float | int | ExprProtocol,
        arg2: str | float | int | ExprProtocol
    ) -> FunctionProtocol:
        param = val(arg) if isinstance(arg, str) else arg
        param2 = val(arg2) if isinstance(arg2, str) else arg2
        return SeparatedArgsFn(self.name, fn_items=(column, param, param2), separator=', ', numbers_as_str=False)
