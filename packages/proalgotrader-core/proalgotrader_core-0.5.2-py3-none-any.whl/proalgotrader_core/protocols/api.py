from __future__ import annotations

from typing import Protocol, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol


class ApiProtocol(Protocol):
    """Protocol for Api functionality."""

    # Properties from concrete implementation
    args_manager: "ArgsManagerProtocol"
    algo_session_key: str
    algo_session_secret: str
    api_url: str
    headers: Dict[str, str]
    token: str | None

    # Constructor
    def __init__(self, args_manager: "ArgsManagerProtocol") -> None: ...

    # Public methods from concrete implementation
    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        data: Dict[str, Any] | None = None,
        json: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]: ...

    async def get_algo_session_info(self) -> Dict[str, Any]: ...

    async def get_github_access_token(self, github_account_id: int) -> str: ...

    async def get_trading_days(self) -> List[Dict[str, Any]]: ...

    async def get_portfolio(self) -> Dict[str, Any]: ...

    async def get_orders(self) -> Dict[str, Any]: ...

    async def get_positions(self) -> Dict[str, Any]: ...

    async def get_base_symbols(self) -> Dict[str, Any]: ...

    async def get_broker_symbols(
        self, broker_title: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    async def get_fno_expiry(self, payload: Dict[str, Any]) -> str | None: ...

    async def get_signals(
        self, broker_title: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    async def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...

    async def create_multiple_orders(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    async def exit_all_positions(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...

    async def modify_order(
        self, order_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    async def create_risk_reward(
        self, position_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    async def hit_risk_reward(
        self, position_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    async def trail_risk_reward(
        self, position_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]: ...
