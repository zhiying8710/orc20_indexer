import os
import sys
import asyncio
from environs import Env

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, EventType
from src.indexer.otc import execute as execute_indexer
from src.data.processer.interface import Interface as DataProcesser
from src.handler.utils.utils import handle_inscribe, error_event, new_balance

env = Env()
env.read_env()
otc_start_block_height = env.int("OTC_START_BLOCK_HEIGHT")


async def handle_execute(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the execution of OTC events.

    Args:
        event (Event): The OTC event to be executed.
        data_processer (DataProcesser): The data processer interface.

    Returns:
        Event: The updated event after execution.
    """
    if event.block_height < otc_start_block_height:
        return error_event(event, f"otc function is not available yet")

    if event.event_type != EventType.INSCRIBE:
        return error_event(event, "otc-execute event don't care about transfer")

    (base_params, error) = execute_indexer.parse_params(event)
    if base_params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    event.function_id = base_params["oid"]

    tasks = [
        data_processer.get_otc(base_params["oid"]),
        data_processer.get_otc_records(base_params["oid"]),
    ]

    (otc, records) = await asyncio.gather(*tasks)

    if otc is None:
        return error_event(event, f"Failed to get otc: {base_params['oid']}")
    if None in records:
        return error_event(event, "Failed to get all otc records")

    tasks = [data_processer.get_token(otc.tid1), data_processer.get_token(otc.tid2)]
    (token1, token2) = await asyncio.gather(*tasks)
    if token1 is None:
        return error_event(event, f"Failed to get token: {otc.tid1}")
    if token2 is None:
        return error_event(event, f"Failed to get token: {otc.tid2}")

    (valid, error) = execute_indexer.is_valid_event(event, otc, token2)
    if valid is False:
        return error_event(event, error)

    user_and_token_infos = [(otc.owner, otc.tid1), (otc.owner, otc.tid2)]
    user_and_token_infos.extend([(record.address, otc.tid1) for record in records])
    user_and_token_infos.extend([(record.address, otc.tid2) for record in records])

    tasks = [data_processer.get_balance(*item) for item in user_and_token_infos]
    balances = await asyncio.gather(*tasks)

    seller_token1_balance = balances[0]
    if seller_token1_balance is None:
        return error_event(
            event,
            f"Failed to get user balance, user: {otc.owner}, tid: {otc.tid1}",
        )

    seller_token2_balance = balances[1]
    if seller_token2_balance is None:
        seller_token2_balance = new_balance(otc.owner, token2)

    buyer_token1_balances = []
    buyer_token2_balances = []
    if len(records) > 0:
        buyer_token1_balances = balances[2 : len(records) + 2]
        for index in range(len(buyer_token1_balances)):
            if buyer_token1_balances[index] is None:
                buyer_token1_balances[index] = new_balance(
                    records[index].address, token1
                )
        buyer_token2_balances = balances[len(records) + 2 : len(records) * 2 + 2]
        for index in range(len(buyer_token2_balances)):
            if buyer_token2_balances[index] is None:
                return error_event(
                    event,
                    f"Failed to get user balance, user: {records[index].address}, tid: {otc.tid2}",
                )

    (token1, token2, otc, balances) = execute_indexer.process_execute(
        event,
        otc,
        token1,
        token2,
        records,
        seller_token1_balance,
        seller_token2_balance,
        buyer_token1_balances,
        buyer_token2_balances,
    )

    tasks = [
        data_processer.save_token(token1),
        data_processer.save_token(token2),
        data_processer.save_otc(otc),
        data_processer.batch_save_balances(balances),
    ]
    await asyncio.gather(*tasks)

    return event
