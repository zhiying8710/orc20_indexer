import os
import sys
import asyncio
from environs import Env

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, EventType
from src.indexer.otc import buy as buy_indexer
from src.data.processer.interface import Interface as DataProcesser
from src.handler.utils.utils import handle_inscribe, error_event

env = Env()
env.read_env()
otc_start_block_height = env.int("OTC_START_BLOCK_HEIGHT")


async def handle_buy(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handles the buy event.

    Args:
        event (Event): The buy event.
        data_processer (DataProcesser): The data processer.

    Returns:
        Event: The updated event.
    """
    if event.block_height < otc_start_block_height:
        return error_event(event, f"otc function is not available yet")

    (base_params, error) = buy_indexer.parse_base_params(event)
    if base_params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    event.function_id = base_params["oid"]

    if event.event_type == EventType.INSCRIBE:
        return await handle_inscribe(event, data_processer)

    tasks = [
        data_processer.get_pending_inscription(event.sender),
        data_processer.get_token(base_params["tid"]),
        data_processer.get_otc(base_params["oid"]),
        data_processer.get_balance(event.sender, base_params["tid"]),
    ]

    (pending_ins, token2, otc, balance2) = await asyncio.gather(*tasks)

    if pending_ins is None or event.inscription_id not in pending_ins.inscriptions:
        return error_event(event, "invalid inscription")

    if token2 is None:
        return error_event(event, f"Failed to get token: {base_params['tid']}")

    if otc is None:
        return error_event(event, f"Failed to get otc: {base_params['oid']}")

    if balance2 is None:
        return error_event(event, f"Failed to get balance: {event.sender}")

    (params, error) = buy_indexer.parse_params(event, token2, base_params)
    if params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    (valid, error) = buy_indexer.is_valid_event(event, params, token2, balance2, otc)
    if valid is False:
        return error_event(event, error)

    token1 = await data_processer.get_token(otc.tid1)
    if token1 is None:
        return error_event(event, f"Failed to get token: {otc.tid1}")

    (token2, balance2, otc, otc_record) = buy_indexer.process_buy(
        event, params, token1, token2, balance2, otc
    )

    pending_ins.inscriptions.remove(event.inscription_id)

    tasks = [
        data_processer.save_otc(otc),
        data_processer.save_otc_record(otc_record),
        data_processer.save_token(token2),
        data_processer.save_balance(balance2),
        data_processer.save_pending_inscription(pending_ins),
    ]
    await asyncio.gather(*tasks)

    return event
