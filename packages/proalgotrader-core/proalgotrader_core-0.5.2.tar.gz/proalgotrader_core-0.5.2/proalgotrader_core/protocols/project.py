from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Any, Dict

if TYPE_CHECKING:
    from proalgotrader_core.protocols.broker_info import BrokerInfoProtocol
    from proalgotrader_core.protocols.api import ApiProtocol


class ProjectProtocol(Protocol):
    """Protocol for Project functionality."""

    # Properties from concrete implementation
    id: int
    name: str
    status: str
    broker_info: "BrokerInfoProtocol"
    github_repository: (
        Any  # GithubRepository - keeping as Any since it's not a core protocol
    )

    # Methods from concrete implementation
    def __init__(self, project_info: Dict[str, Any]) -> None: ...

    async def clone_repository(self, api: "ApiProtocol") -> None: ...
