from __future__ import annotations

from typing import Protocol, Any


class ArgsManagerProtocol(Protocol):
    """Protocol for ArgsManager functionality."""

    # Properties from concrete implementation
    arguments: Any  # argparse.Namespace
    algo_session_key: str
    algo_session_secret: str
    api_url: str
    environment: str

    # Public methods from concrete implementation
    def validate_arguments(self) -> None: ...
