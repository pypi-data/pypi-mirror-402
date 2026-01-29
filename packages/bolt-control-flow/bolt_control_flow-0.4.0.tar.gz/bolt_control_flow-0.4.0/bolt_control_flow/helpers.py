"""Runtime implementation helpers

Danger:
    This is an internal module, not meant for public usage
"""

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from functools import partial
from types import TracebackType
from typing import Any, Literal, Optional, TypeAlias, TypeGuard

from bolt import Accumulator, Runtime

from bolt_control_flow.types import (
    BinaryLogicalFallback,
    BranchInfo,
    BranchType,
    Case,
    CaseMatchType,
    CasePartialResult,
    CaseResult,
)


def get_runtime_helpers() -> dict[str, Any]:
    return {
        "operator_and": partial(binary_logical, "and"),
        "operator_or": partial(binary_logical, "or"),
        **{t.helper: partial(MultibranchDriver, t) for t in BranchType},
    }


def call_branch(condition: Any, runtime: Runtime) -> AbstractContextManager[Any]:
    return runtime.helpers["branch"](condition)


def call_not(condition: Any, runtime: Runtime) -> Any:
    return runtime.helpers["operator_not"](condition)


def binary_logical(
    op: Literal["and", "or"], runtime: Runtime, left: Any, right: Callable[[], Any]
) -> Any:
    ltype = type(left)
    if func := getattr(ltype, f"__logical_{op}__", None):
        match func(left, right):
            case BinaryLogicalFallback(fallback_right_value):
                # Matching standard Python behaviour for "reflected (swapped)" operators
                # For operands of the same type, it is assumed that if the non-reflected method fails then the overall operation is not supported, which is why the reflected method is not called.
                rtype = type(fallback_right_value)
                if ltype != rtype:
                    if func := getattr(rtype, f"__rlogical_{op}__", None):
                        match func(fallback_right_value, left):
                            case BinaryLogicalFallback():
                                # Avoid calling the original right function again
                                # Reuse existing value instead
                                right = lambda: fallback_right_value  # noqa: E731  (use def instead of lambda)
                            case res:
                                return res
            case res:
                return res

    # Can only safely use __rlogical_{op}__ if left has __logical_{op}__
    # Otherwise short circuiting rules would be broken for standard Python values

    # Reimplementation of the code that plain-bolt generates for an `and` or `or` expression
    #
    # See: bolt.codegen.Codegen.binary_logical
    # TODO: Determine if there's a good way to wrap this such that __multibranch__ can still be utilised
    condition = call_not(left, runtime) if op == "or" else left
    dup = runtime.helpers["get_dup"](left)
    if dup is not None:
        left = dup()

    with call_branch(condition, runtime) as _bolt_condition:
        if _bolt_condition:
            right_value = right()

            if dup is not None:
                _bolt_rebind = runtime.helpers["get_rebind"](left)
                left = right_value
                if _bolt_rebind is not None:
                    left = _bolt_rebind(left)
            else:
                left = right_value

    return left


CaseCallable: TypeAlias = Callable[
    [Any, Case], AbstractContextManager[CasePartialResult]
]

_LAZY_NOT_SENTINEL = object()


class CaseDriver:
    obj: Any
    runtime: Runtime
    case_func: Optional[CaseCallable]
    not_obj: Any = _LAZY_NOT_SENTINEL
    case_definitely_matched: bool = False

    def __init__(self, obj: Any, runtime: Runtime) -> None:
        self.obj = obj
        self.runtime = runtime
        self.case_func = getattr(type(obj), "__case__", None)

    @staticmethod
    def codegen_access_underlying(target: str) -> str:
        """Generate an access to the underlying case object

        This is a helper to keep the hardcoded name of the attribute close to the definition of the attribute

        :param target: Code str for accessing a CaseDriver
        :type target: str
        :return: Code str for accessing the underlying case object
        :rtype: str
        """
        return target + ".obj"

    def _fallback_case(self, case: bool | Any) -> Iterator[CaseResult]:
        match case:
            case bool(is_if):
                assert (self.not_obj is _LAZY_NOT_SENTINEL) == is_if

                if is_if:
                    # Lazily calculated when detecting an if...else so that the not isn't called for pattern matching
                    self.not_obj = call_not(self.obj, self.runtime)
                    obj = self.obj
                else:
                    obj = self.not_obj

                with call_branch(obj, self.runtime) as _bolt_condition:
                    if _bolt_condition:
                        # the original __branch__ pattern treated True as if it were maybe
                        yield CaseResult.maybe()
                    else:
                        yield CaseResult.failed()
            case _:
                # TODO: use pattern's default implementation
                raise NotImplementedError("Fallback pattern matching")

    def _should_use_case(
        self, case_func: Optional[CaseCallable]
    ) -> TypeGuard[CaseCallable]:
        if case_func is None:
            # The type doesn't implement __case__
            return False

        if self.not_obj is not _LAZY_NOT_SENTINEL:
            # __case__ returned NotImplemented for `if` (True) in the previous call
            return False

        return True

    @contextmanager
    def __case__(self, case: bool | Any) -> Iterator[CaseResult]:
        if self.case_definitely_matched:
            # Don't attempt to match after a previous match passed at build time
            yield CaseResult.failed()
            return

        if not self._should_use_case(self.case_func):
            yield from self._fallback_case(case)
            return

        with self.case_func(self.obj, case) as res:
            if isinstance(res, CaseResult):
                if res.match_type == CaseMatchType.MATCHED:
                    self.case_definitely_matched = True

                yield res
                return

        if case is False:
            raise ValueError(
                f"Type {type(self.obj)} implemented __case__ for `if` (True) but not `else` (False)"
            )

        yield from self._fallback_case(case)


class MultibranchDriver:
    obj: Any
    context_manager: Optional[AbstractContextManager[Any]] = None
    runtime: Runtime

    def __init__(
        self,
        branch_type: BranchType,
        obj: Any,
        runtime: Runtime,
        parent_cases: Optional[Any],
    ) -> None:
        self.obj = obj
        self.runtime = runtime

        tobj = type(obj)
        if func := getattr(tobj, "__multibranch__", None):
            self.context_manager = func(obj, BranchInfo(branch_type, parent_cases))

    @staticmethod
    def codegen_call(
        acc: Accumulator, parent_cases: str, branch_type: BranchType, condition: str
    ) -> str:
        return acc.helper(branch_type.helper, condition, "_bolt_runtime", parent_cases)

    def __enter__(self) -> Any:
        if self.context_manager is None:
            obj = self.obj
        else:
            obj = self.context_manager.__enter__()
            if obj is NotImplemented:
                obj = self.obj

        return CaseDriver(obj, self.runtime)

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if self.context_manager is not None:
            return self.context_manager.__exit__(exc_type, exc, traceback)

        return None
