from logzero import logger
import requests
import asyncio

from typing import Any, Dict, List
from requests import Response
from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol


class Api:
    def __init__(self, args_manager: ArgsManagerProtocol) -> None:
        self.args_manager = args_manager

        self.algo_session_key = self.args_manager.algo_session_key
        self.algo_session_secret = self.args_manager.algo_session_secret
        self.api_url = self.args_manager.api_url

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        self.token = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        data: Dict[str, Any] | None = None,
        json: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        url = f"{self.api_url}{endpoint}"
        logger.info(f"[{method.upper()}] {url} payload={json or data}")

        # Disable SSL verification in development (for self-signed certificates like Laravel Herd)
        verify_ssl = self.args_manager.environment != "development"

        try:
            response: Response = await asyncio.to_thread(
                requests.request,
                method,
                url,
                data=data,
                json=json,
                headers=self.headers,
                verify=verify_ssl,
            )
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise Exception(e)

        try:
            result = response.json()
        except Exception:
            result = {}

        if not response.ok:
            logger.error(f"[{response.status_code}] {url} -> {result}")
            raise Exception(result)

        return result

    async def get_algo_session_info(self) -> Dict[str, Any]:
        try:
            result = await self._request(
                "post",
                "/api/algo-sessions/info",
                json={
                    "algo_session_key": self.algo_session_key,
                    "algo_session_secret": self.algo_session_secret,
                },
            )

            self.token = result["token"]
            self.headers["Authorization"] = f"Bearer {self.token}"

            return result
        except Exception as e:
            logger.error(f"get_algo_session_info failed: {e}")
            raise Exception(e)

    async def get_github_access_token(self, github_account_id: int) -> Dict[str, Any]:
        try:
            result = await self._request(
                "get",
                f"/api/github/accounts/{github_account_id}/access-token",
            )

            return result["access_token"]
        except Exception as e:
            logger.error(f"get_github_access_token failed: {e}")
            raise Exception(e)

    async def get_trading_days(self) -> List[Dict[str, Any]]:
        try:
            result = await self._request("get", "/api/trading-days/list")

            return result["trading_days"]
        except Exception as e:
            logger.error(f"get_trading_days failed: {e}")
            raise Exception(e)

    async def get_portfolio(self) -> Dict[str, Any]:
        try:
            result = await self._request(
                "get", f"/api/algo-sessions/{self.algo_session_key}/portfolio/list"
            )

            return result["portfolio"]
        except Exception as e:
            logger.error(f"get_portfolio failed: {e}")
            raise Exception(e)

    async def get_orders(self) -> Dict[str, Any]:
        try:
            result = await self._request(
                "get", f"/api/algo-sessions/{self.algo_session_key}/orders/list"
            )

            return result["orders"]
        except Exception as e:
            logger.error(f"get_orders failed: {e}")
            raise Exception(e)

    async def get_positions(self) -> Dict[str, Any]:
        try:
            result = await self._request(
                "get",
                f"/api/algo-sessions/{self.algo_session_key}/positions/list",
            )

            return result["positions"]
        except Exception as e:
            logger.error(f"get_positions failed: {e}")
            raise Exception(e)

    async def get_base_symbols(self) -> Dict[str, Any]:
        try:
            result = await self._request("get", "/api/base-symbols/list")

            return result["data"]
        except Exception as e:
            logger.error(f"get_base_symbols failed: {e}")
            raise Exception(e)

    async def get_broker_symbols(
        self, broker_title: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            result = await self._request(
                "get",
                f"/api/broker-symbols/{broker_title}/catalog",
                json=payload,
            )

            return result["broker_symbol"]
        except Exception as e:
            logger.error(f"get_broker_symbols failed: {e}")
            raise Exception(e)

    async def get_fno_expiry(self, payload: Dict[str, Any]) -> str | None:
        try:
            result = await self._request(
                "get",
                "/api/broker-symbols/fno/expiry",
                json=payload,
            )

            return result["expiry_date"]
        except Exception as e:
            logger.error(f"get_broker_symbols failed: {e}")
            raise Exception(e)

    async def get_signals(
        self, broker_title: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            result = await self._request(
                "post",
                f"/api/broker-symbols/{broker_title}/signals",
                json=payload,
            )

            return result
        except Exception as e:
            logger.error(f"get_signals failed: {e}")
            raise Exception(e)

    async def create_risk_reward(
        self, position_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            result = await self._request(
                "post",
                f"/api/algo-sessions/{self.algo_session_key}/risk-rewards/{position_id}/create",
                json=payload,
            )

            return result
        except Exception as e:
            logger.error(f"create_order failed: {e}")
            raise Exception(e)

    async def hit_risk_reward(
        self, position_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            result = await self._request(
                "post",
                f"/api/algo-sessions/{self.algo_session_key}/risk-rewards/{position_id}/hit",
                json=payload,
            )

            return result
        except Exception as e:
            logger.error(f"hit_risk_reward failed: {e}")
            raise Exception(e)

    async def trail_risk_reward(
        self, position_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            result = await self._request(
                "post",
                f"/api/algo-sessions/{self.algo_session_key}/risk-rewards/{position_id}/trail",
                json=payload,
            )

            return result
        except Exception as e:
            logger.error(f"trail_risk_reward failed: {e}")
            raise Exception(e)

    async def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self._request(
                "post",
                f"/api/algo-sessions/{self.algo_session_key}/orders/create",
                json=payload,
            )

            return result
        except Exception as e:
            logger.error(f"create_order failed: {e}")
            raise Exception(e)

    async def create_multiple_orders(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self._request(
                "post",
                f"/api/algo-sessions/{self.algo_session_key}/orders/create-multiple",
                json=payload,
            )

            return result
        except Exception as e:
            logger.error(f"create_multiple_orders failed: {e}")
            raise Exception(e)

    async def exit_all_positions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self._request(
                "post",
                f"/api/algo-sessions/{self.algo_session_key}/portfolio/exit-all-positions",
                json=payload,
            )

            return result
        except Exception as e:
            logger.error(f"create_multiple_orders failed: {e}")
            raise Exception(e)

    async def modify_order(
        self, order_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            result = await self._request(
                "put",
                f"/api/algo-sessions/{self.algo_session_key}/orders/{order_id}/modify",
                json=payload,
            )

            return result
        except Exception as e:
            logger.error(f"modify_order failed: {e}")
            raise Exception(e)
