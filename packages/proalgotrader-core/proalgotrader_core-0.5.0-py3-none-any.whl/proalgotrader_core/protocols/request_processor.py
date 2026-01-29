from __future__ import annotations

from typing import Any, Protocol
from contextlib import asynccontextmanager


class RequestProcessorProtocol(Protocol):
    """Protocol for RequestProcessor functionality."""

    def is_processing(self) -> bool: ...

    @asynccontextmanager
    async def processing(self) -> Any: ...

    async def finish(self) -> None: ...
