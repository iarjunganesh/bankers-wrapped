"""
Base agent contract for Banker's Wrapped.

Each agent is a Semantic Kernel-compatible plugin: a typed input → typed output
transformation with a single async `run()` entry point. The `@kernel_function`
decorator marks methods for SK orchestration. Agents are stateless — all state
is passed explicitly as inputs and returned as outputs.
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

import structlog

log = structlog.get_logger()

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent(ABC):
    """Abstract base for all Banker's Wrapped agents."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.log = structlog.get_logger(agent=name)

    @abstractmethod
    async def run(self, input_data: Any) -> Any:  # noqa: ANN401
        """Execute the agent's core transformation."""
        ...

    async def __call__(self, input_data: Any) -> Any:  # noqa: ANN401
        self.log.info("agent.start")
        try:
            result = await self.run(input_data)
            self.log.info("agent.complete")
            return result
        except Exception as exc:
            self.log.error("agent.error", error=str(exc))
            raise
