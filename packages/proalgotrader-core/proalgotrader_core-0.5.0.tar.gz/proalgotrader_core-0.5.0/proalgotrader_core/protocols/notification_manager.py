from __future__ import annotations

from typing import Protocol, Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol


class NotificationManagerProtocol(Protocol):
    """Protocol for NotificationManager functionality."""

    # Properties from concrete implementation
    algo_session: "AlgoSessionProtocol"
    algo_session_key: str
    reverb_info: Dict[str, Any]
    pusher_client: Any  # pusher.Pusher type

    # Methods from concrete implementation
    async def connect(self) -> None: ...

    async def send_message(self, data: Dict[str, Any]) -> None: ...
