from __future__ import annotations

from typing import Protocol, Dict, Any


class BrokerInfoProtocol(Protocol):
    """Protocol for BrokerInfo functionality."""

    # Properties from concrete implementation
    id: int
    broker_uid: str
    broker_title: str
    broker_name: str
    broker_config: Dict[str, Any]
