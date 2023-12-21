import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, EventType
from src.indexer.core import mint as mint_indexer
from src.data.processer.interface import Interface as DataProcesser
from src.handler.utils.utils import new_balance, error_event


async def handle_mint(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the mint event.

    Args:
        event (Event): The mint event to be handled.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event after handling the mint event.
    """
    if event.event_type != EventType.INSCRIBE:
        return error_event(event, "mint event don't care about transfer")

    (base_params, error) = mint_indexer.parse_base_params(event)
    if base_params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    event.function_id = base_params["tid"]

    tasks = [
        data_processer.get_token(base_params["tid"]),
        data_processer.get_balance(event.receiver, base_params["tid"]),
    ]
    (token, balance) = await asyncio.gather(*tasks)
    if token is None:
        return error_event(event, f"Failed to get token: {base_params['tid']}")
    if balance is None:
        balance = new_balance(event.receiver, token)

    (params, error) = mint_indexer.parse_params(event, token, base_params)
    if params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    (valid, error) = mint_indexer.is_valid_event(event, token, params)
    if valid is False:
        return error_event(event, error)

    (token, balance) = mint_indexer.process_mint(event, params, token, balance)

    tasks = [data_processer.save_token(token), data_processer.save_balance(balance)]
    await asyncio.gather(*tasks)

    return event
