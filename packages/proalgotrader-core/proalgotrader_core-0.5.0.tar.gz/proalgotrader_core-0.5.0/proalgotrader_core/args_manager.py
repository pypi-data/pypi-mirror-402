import argparse
import os

from logzero import logger


def parse_arguments() -> argparse.Namespace:
    try:
        parser = argparse.ArgumentParser(
            description="ProAlgoTrader - Algorithmic Trading Framework",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --mode=paper                                               Run in paper trading mode
  %(prog)s --mode=live                                                Run in live trading mode
  %(prog)s --mode=paper --environment=development                     Run in paper mode with development environment (no SSL verification)
  %(prog)s --mode=live --environment=production                       Run in live mode with production environment (SSL verification enabled)
            """,
        )

        parser.add_argument(
            "--mode",
            default="paper",
            choices=["paper", "live"],
            help="Trading mode: 'paper' for paper trading or 'live' for live trading (default: paper)",
        )

        parser.add_argument(
            "--environment",
            default=os.getenv("ENVIRONMENT", "development"),
        )

        parser.add_argument(
            "--api_url",
            default=os.getenv("API_URL", "https://proalgotrader.com"),
        )

        return parser.parse_args()
    except Exception as e:
        logger.debug(e)
        raise Exception(e)


class ArgsManager:
    def __init__(self) -> None:
        self.arguments = parse_arguments()

        self.mode = self.arguments.mode
        self.algo_session_key = os.getenv("ALGO_SESSION_KEY")
        self.algo_session_secret = os.getenv("ALGO_SESSION_SECRET")

        self.api_url = self.arguments.api_url

        self.environment = self.arguments.environment

    def validate_arguments(self) -> None:
        if not self.arguments.environment:
            raise Exception("Environment is required")

        if not self.algo_session_key:
            raise Exception("Algo Session Key is required")

        if not self.algo_session_secret:
            raise Exception("Algo Session Secret is required")

        if self.arguments.environment not in ["development", "production"]:
            raise Exception(
                f"Invalid Environment '{self.arguments.environment}', Choose between 'development' or 'production'"
            )
