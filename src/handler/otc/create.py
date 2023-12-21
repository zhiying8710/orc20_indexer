import os
import sys
import asyncio
from environs import Env


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, EventType
from src.indexer.otc import create as create_indexer
from src.data.processer.interface import Interface as DataProcesser
from src.handler.utils.utils import handle_inscribe, error_event

env = Env()
env.read_env()
otc_start_block_height = env.int("OTC_START_BLOCK_HEIGHT")


async def handle_create(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the creation of an OTC event.

    Args:
        event (Event): The OTC event to be handled.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated OTC event.
    """
    if event.block_height < otc_start_block_height:
        return error_event(event, f"otc function is not available yet")

    (base_params, error) = create_indexer.parse_base_params(event)
    if base_params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    event.function_id = event.inscription_number

    if event.event_type == EventType.INSCRIBE:
        return await handle_inscribe(event, data_processer)

    tasks = [
        data_processer.get_pending_inscription(event.sender),
        data_processer.get_token(base_params["tid1"]),
        data_processer.get_token(base_params["tid2"]),
        data_processer.get_balance(event.sender, base_params["tid1"]),
    ]
    (pending_ins, token1, token2, token1_balance) = await asyncio.gather(*tasks)

    if pending_ins is None or event.inscription_id not in pending_ins.inscriptions:
        return error_event(event, "invalid inscription")

    if token1 is None or token2 is None:
        return error_event(
            event, f"Failed to get tokens: {base_params['tid1']}, {base_params['tid2']}"
        )

    if token1_balance is None:
        return error_event(event, f"Failed to get balance: {event.sender}")

    (params, error) = create_indexer.parse_params(event, token1, token2, base_params)
    if params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    (valid, error) = create_indexer.is_valid_event(params, token1_balance)
    if valid is False:
        return error_event(event, error)

    (token1, token1_balance, otc) = create_indexer.process_create(
        event, params, token1, token1_balance
    )

    pending_ins.inscriptions.remove(event.inscription_id)

    tasks = [
        data_processer.save_otc(otc),
        data_processer.save_token(token1),
        data_processer.save_balance(token1_balance),
        data_processer.save_pending_inscription(pending_ins),
    ]
    await asyncio.gather(*tasks)

    return event
