import asyncio
from pathlib import Path
from typing import Type

from dotenv import load_dotenv
from logzero import logger

from proalgotrader_core.application import Application
from proalgotrader_core.algorithm_factory import AlgorithmFactory
from proalgotrader_core.args_manager import parse_arguments
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


# Setup the loop at module level
try:
    event_loop = asyncio.get_running_loop()
except RuntimeError:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)


def _load_env_file(mode: str) -> None:
    """
    Load the appropriate .env file based on the trading mode.

    Args:
        mode: Trading mode ('paper' or 'live')

    Raises:
        Exception: If the required .env file does not exist
    """
    project_root = Path().cwd()
    env_file = project_root / f".env.{mode}"

    if not env_file.exists():
        raise Exception(
            f"Environment file '.env.{mode}' not found at {env_file}. "
            f"Please create this file with the required configuration."
        )

    logger.info(f"Loading environment from: {env_file}")
    load_dotenv(env_file, verbose=True, override=True)


async def start_with_factory(strategy_class: Type[AlgorithmProtocol]) -> None:
    """
    Start function that uses the factory pattern to create
    Algorithm with pre-initialized AlgoSession
    """
    # Parse arguments early to get the mode and handle --help properly
    # This will exit if --help is provided, before we try to load the env file
    args = parse_arguments()
    mode = args.mode

    _load_env_file(mode)

    algorithm_factory = AlgorithmFactory(
        event_loop=event_loop,
        strategy_class=strategy_class,
    )

    # Use factory to create algorithm with session
    algorithm = await algorithm_factory.create_algorithm_with_session()

    # Create application with the pre-initialized algorithm
    application = Application(algorithm=algorithm)

    try:
        await application.start()
    except Exception as e:
        logger.exception(e)


def run_strategy(strategy_class: Type[AlgorithmProtocol]) -> None:
    """
    Start function that uses the factory pattern for better initialization
    """
    try:
        event_loop.run_until_complete(start_with_factory(strategy_class=strategy_class))
    except Exception as e:
        logger.exception(e)
    finally:
        event_loop.close()
