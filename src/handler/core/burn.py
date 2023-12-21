import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, EventType
from src.indexer.core import burn as burn_indexer
from src.data.processer.interface import Interface as DataProcesser
from src.handler.utils.utils import handle_inscribe, error_event


async def handle_burn(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handles the burn event.

    Args:
        event (Event): The burn event to handle.
        data_processer (DataProcesser): The data processer instance.

    Returns:
        Event: The updated event after handling the burn event.
    """
    (base_params, error) = burn_indexer.parse_base_params(event)
    if base_params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    event.function_id = base_params["tid"]

    if event.event_type == EventType.INSCRIBE:
        return await handle_inscribe(event, data_processer)

    tasks = [
        data_processer.get_token(base_params["tid"]),
        data_processer.get_balance(event.sender, base_params["tid"]),
        data_processer.get_pending_inscription(event.sender),
    ]

    (token, balance, pending_ins) = await asyncio.gather(*tasks)

    if pending_ins is None or event.inscription_id not in pending_ins.inscriptions:
        return error_event(event, "invalid inscription")

    if token is None:
        return error_event(event, f"Failed to get token: {base_params['tid']}")
    if balance is None:
        return error_event(event, f"Failed to get balance: {event.sender}")

    (params, error) = burn_indexer.parse_params(event, token, base_params)
    if params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    (valid, error) = burn_indexer.is_valid_event(balance, params)
    if valid is False:
        return error_event(event, error)

    (token, balance) = burn_indexer.process_burn(params, token, balance)

    pending_ins.inscriptions.remove(event.inscription_id)

    tasks = [
        data_processer.save_token(token),
        data_processer.save_balance(balance),
        data_processer.save_pending_inscription(pending_ins),
    ]
    await asyncio.gather(*tasks)

    return event
