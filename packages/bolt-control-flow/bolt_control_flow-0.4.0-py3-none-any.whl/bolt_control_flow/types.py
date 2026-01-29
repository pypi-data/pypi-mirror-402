from dataclasses import dataclass, field
from enum import Enum, auto
from types import NotImplementedType
from typing import Any, Optional, TypeAlias

__all__ = [
    "CaseResult",
    "CaseMatchType",
    "CasePartialResult",
    "Case",
    "BranchType",
    "BranchInfo",
    "BinaryLogicalFallback",
    "WrappedCases",
]


class CaseMatchType(Enum):
    """The status of a match"""

    FAILED = auto()
    """The match failed at build time"""

    MATCHED = auto()
    """The match succeeded at build time"""

    MAYBE = auto()
    """Whether the match passed isn't known until runtime"""

    def __bool__(self) -> bool:
        return self != CaseMatchType.FAILED


@dataclass
class CaseResult:
    """Information about a match"""

    match_type: CaseMatchType
    """The match status"""

    bindings: dict[str, Any] = field(default_factory=dict)
    """Any bindings to be assigned in the condition caller's scope

    Must contain all the bindings that the case pattern is expecting, and any extra bindings will be ignored
    
    Note:
        If :py:attr:`match_type` is :py:const:`CaseMatchType.FAILED` these bindings will be ignored
    """

    @staticmethod
    def failed() -> "CaseResult":
        """:python:`yield` this value to indicate that the match failed at build time"""
        return CaseResult(CaseMatchType.FAILED)

    @staticmethod
    def matched(**bindings: Any) -> "CaseResult":
        """:python:`yield` this value to indicate that the match passed at build time and run the body of the condition

        Args:
            **bindings: The bindings to be assigned in the condition caller's scope
        """
        return CaseResult(CaseMatchType.MATCHED, bindings)

    @staticmethod
    def maybe(**bindings: Any) -> "CaseResult":
        """:python:`yield` this value to indicate that the match can't be determined until runtime

        It is expected for the runtime check to wrap the :python:`yield`,
        so that running the body of the condition will be wrapped in the check

        Args:
            **bindings: The bindings to be assigned in the condition caller's scope
        """
        return CaseResult(CaseMatchType.MAYBE, bindings)

    @dataclass
    class Codegen:
        """Helpers for generating code for accessing members of :py:class:`CaseResult`

        Danger:
            This is an internal helper, not meant for public usage
        """

        name: str
        """Name of the variable holding this :py:class:`CaseResult`"""

        @property
        def match_type(self) -> str:
            """Generate code for accessing the :py:attr:`~CaseResult.match_type`"""
            return f"{self.name}.match_type"

        def binding(self, binding: str) -> str:
            """Generate code for accessing the given binding in the :py:attr:`~CaseResult.bindings`"""
            return f'{self.name}.bindings["{binding}"]'


CasePartialResult: TypeAlias = CaseResult | NotImplementedType
"""The :python:`yield` type of a :python:`__case__` that doesn't implement all `Case` types

:type: CaseResult | NotImplementedType
"""


# TODO: more specific type for case object when representing match cases
Case: TypeAlias = bool | Any
"""The case being matched against

Possible values:

:python:`True`
    The :python:`if` case of an :python:`if ... else`

:python:`False`
    The :python:`else` case of an :python:`if ... else`

Anything else
    A pattern used in a :python:`case` within a :python:`match`

:type: bool | Any

Note:
    This type is currently a placeholder, it will be made more specific once pattern matching is implemented
"""


class BranchType(Enum):
    """The type of multibranch being processed"""

    IF_ELSE = auto()
    """An :python:`if ... else`"""

    MATCH = auto()
    """A :python:`match`"""

    @property
    def helper(self) -> str:
        """Get the name of the runtime helper for the :py:class:`~bolt_control_flow.helpers.MultibranchDriver` of this type

        Danger:
            This is an internal helper, not meant for public usage
        """
        return f"multibranch_{self.name}"


@dataclass(frozen=True)
class BranchInfo:
    """Information about the multibranch being processed"""

    branch_type: BranchType
    """The type of multibranch being processed"""

    parent_cases: Optional[Any]
    """The result of the parent :python:`__multibranch__`
    
    Will be :python:`None` if any of these are true:
        * there is no parent
        * there are more cases in the parent following the current case
        * this conditional isn't the only piece of the body of the current case

    Useful for merging separate nested multibranches into a single multibranch. e.g. :python:`elif` or :python:`case _:`
    """


@dataclass
class BinaryLogicalFallback:
    """Return this from a binary logical operator to request fallback/default behaviour

    During fallback, it will attempt to call :python:`__rlogical_{op}__` on the :py:attr:`right` value,
    and if that also requests fallback it will use the plain-bolt implementation of the logical operator
    """

    right: Any
    """The result of evaluating the lazy right value callback
    
    This is so that the value isn't calculated again during fallback
    """


class WrappedCases:
    """Marker class to indicate that it is safe for nested conditions to use return without making new functions

    i.e. there are no commands after the cases that must be run
    """
