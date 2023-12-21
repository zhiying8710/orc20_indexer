import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, EventType
from src.indexer.core import upgrade as upgrade_indexer
from src.data.processer.interface import Interface as DataProcesser
from src.handler.utils.utils import handle_inscribe, error_event


async def handle_upgrade(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the upgrade event.

    Args:
        event (Event): The event to be handled.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    (base_params, error) = upgrade_indexer.parse_base_params(event)
    if base_params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    event.function_id = base_params["tid"]

    if event.event_type == EventType.INSCRIBE:
        return await handle_inscribe(event, data_processer)

    tasks = [
        data_processer.get_token(base_params["tid"]),
        data_processer.get_pending_inscription(event.sender),
    ]
    (token, pending_ins) = await asyncio.gather(*tasks)

    if pending_ins is None or event.inscription_id not in pending_ins.inscriptions:
        return error_event(event, "invalid inscription")

    if token is None:
        return error_event(event, f"Failed to get token: {base_params['tid']}")

    (params, error) = upgrade_indexer.parse_params(event, token, base_params)
    if params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    (valid, error) = upgrade_indexer.is_valid_event(event, token)
    if valid is False:
        return error_event(event, error)

    token = upgrade_indexer.process_upgrade(event, params, token)

    pending_ins.inscriptions.remove(event.inscription_id)

    tasks = [
        data_processer.save_token(token),
        data_processer.save_pending_inscription(pending_ins),
    ]
    await asyncio.gather(*tasks)

    return event
