import pusher

from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed

from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol


class NotificationManager:
    def __init__(self, algo_session: AlgoSessionProtocol) -> None:
        self.algo_session = algo_session
        self.pusher_client = None
        self.is_connected = False

    async def connect(self):
        self.algo_session_key = self.algo_session.key
        self.reverb_info = self.algo_session.reverb_info

        await self.get_client()

    async def get_client(self):
        """Get existing client or create new one if not connected (Singleton pattern)"""
        if self.is_connected and self.pusher_client is not None:
            return self.pusher_client

        try:
            self.pusher_client = pusher.Pusher(
                app_id=self.reverb_info["app_id"],
                key=self.reverb_info["app_key"],
                secret=self.reverb_info["app_secret"],
                host=self.reverb_info["host"],
                port=self.reverb_info["port"],
                ssl=self.reverb_info["secure"],
            )

            self.is_connected = True

            return self.pusher_client
        except Exception as e:
            self.is_connected = False

            raise Exception(f"Failed to create Pusher client: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def send_message(self, data: Dict[str, Any]) -> None:
        """Send message with retry logic"""
        try:
            client = await self.get_client()
            channel_name = f"algo-session-{self.algo_session_key}"
            client.trigger(channels=[channel_name], event_name="ltp.update", data=data)
        except Exception as e:
            # Connection lost - mark as disconnected so get_client() will reconnect next time
            self.is_connected = False
            raise e  # Re-raise to trigger retry
