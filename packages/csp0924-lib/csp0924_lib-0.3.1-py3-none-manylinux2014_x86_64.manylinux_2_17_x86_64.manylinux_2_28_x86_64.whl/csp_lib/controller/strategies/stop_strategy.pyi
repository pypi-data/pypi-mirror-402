import _abc
import csp_lib.controller.core.strategy
from csp_lib.controller.core.command import Command as Command
from csp_lib.controller.core.context import StrategyContext as StrategyContext
from csp_lib.controller.core.execution import ExecutionConfig as ExecutionConfig, ExecutionMode as ExecutionMode
from csp_lib.controller.core.strategy import Strategy as Strategy
from typing import ClassVar

class StopStrategy(csp_lib.controller.core.strategy.Strategy):
    __abstractmethods__: ClassVar[frozenset] = ...
    _abc_impl: ClassVar[_abc._abc_data] = ...
    def execute(self, context: StrategyContext) -> Command: ...
    @property
    def execution_config(self): ...
