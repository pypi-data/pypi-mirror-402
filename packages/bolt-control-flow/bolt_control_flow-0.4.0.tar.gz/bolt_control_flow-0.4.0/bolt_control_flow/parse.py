"""Parsing and codegen logic

Danger:
    This is an internal module, not meant for public usage
"""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Optional, cast

from beet.core.utils import extra_field
from bolt import Accumulator, visit_body, visit_single
from bolt.ast import AstExpressionBinary
from mecha import AstCommand, AstNode, AstRoot, Dispatcher, rule

from bolt_control_flow.helpers import CaseDriver, MultibranchDriver
from bolt_control_flow.types import BranchType, CaseResult


@dataclass(eq=False)
class Codegen(Dispatcher[Any]):
    cases_vars: list[str] = extra_field(default_factory=list, init=False)
    is_conditional_only_in_last_case: bool = extra_field(default=False, init=False)

    @rule(AstExpressionBinary, operator="and")
    @rule(AstExpressionBinary, operator="or")
    def binary_logical(
        self, node: AstExpressionBinary, acc: Accumulator
    ) -> Generator[AstNode, Optional[list[str]], Optional[list[str]]]:
        left = yield from visit_single(node.left, required=True)
        lazy_right = acc.make_variable()
        with acc.function(lazy_right):
            right = yield from visit_single(node.right, required=True)
            acc.statement("return", right)

        value = acc.helper(
            f"operator_{node.operator}", "_bolt_runtime", left, lazy_right
        )
        acc.statement(left, "=", value)
        return [left]

    @contextmanager
    def _case_block(
        self,
        acc: Accumulator,
        *bindings: str,
        case: str,
        body_is_conditional_only_in_last_case: bool,
    ) -> Iterator[None]:
        was_nested = self.is_conditional_only_in_last_case
        self.is_conditional_only_in_last_case = body_is_conditional_only_in_last_case
        try:
            condition = "_bolt_condition"
            case_result = CaseResult.Codegen(condition)
            acc.statement(
                "with", f"{self.cases_vars[-1]}.__case__({case})", "as", f"{condition}"
            )
            with acc.block():
                acc.statement("if", f"{case_result.match_type}")
                with acc.block():
                    for binding in bindings:
                        acc.statement(f"{binding} = {case_result.binding(binding)}")

                    yield
        finally:
            self.is_conditional_only_in_last_case = was_nested

    @rule(AstCommand, identifier="if:condition:body")
    def if_statement(
        self, node: AstCommand, acc: Accumulator
    ) -> Generator[AstNode, Optional[list[str]], Optional[list[str]]]:
        condition = yield from visit_single(node.arguments[0], required=True)

        else_index = acc.current_sibling_index + 1
        if (
            else_index < len(acc.current_siblings)
            and isinstance(else_node := acc.current_siblings[else_index], AstCommand)
            and else_node.identifier == "else:body"
        ):
            parent_cases = (
                CaseDriver.codegen_access_underlying(self.cases_vars.pop())
                if self.is_conditional_only_in_last_case
                else str(None)
            )

            multibranch = MultibranchDriver.codegen_call(
                acc, parent_cases, BranchType.IF_ELSE, condition
            )

            cases = acc.make_variable()
            self.cases_vars.append(cases)
            acc.statement("with", f"{multibranch}", "as", f"{cases}")
            with acc.block():
                with self._case_block(
                    acc, case="True", body_is_conditional_only_in_last_case=False
                ):
                    yield from visit_body(cast(AstRoot, node.arguments[1]), acc)
        else:
            with acc.if_statement(condition, None):
                yield from visit_body(cast(AstRoot, node.arguments[1]), acc)

        return []

    @rule(AstCommand, identifier="else:body")
    def else_statement(
        self, node: AstCommand, acc: Accumulator
    ) -> Generator[AstNode, Optional[list[str]], Optional[list[str]]]:
        body = cast(AstRoot, node.arguments[0])

        should_nest: bool
        match body.commands:
            case (
                # else containing only a nested if...else
                [
                    AstCommand(identifier="if:condition:body"),
                    AstCommand(identifier="else:body"),
                ]
                # TODO: Single match statement
            ):
                should_nest = True
            case _:
                should_nest = False

        # continue the if's `with {multibranch} as {cases}:`
        with acc.block():
            with self._case_block(
                acc, case="False", body_is_conditional_only_in_last_case=should_nest
            ):
                if not should_nest:
                    self.cases_vars.pop()

                yield from visit_body(body, acc)

        return []
