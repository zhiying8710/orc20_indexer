import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, EventType, Pending_Inscriptions
from src.indexer.core import transfer as transfer_indexer
from src.data.processer.interface import Interface as DataProcesser
from src.handler.utils.utils import new_balance, error_event


async def handle_transfer(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the transfer event.

    Args:
        event (Event): The transfer event.
        data_processer (DataProcesser): The data processer.

    Returns:
        Event: The updated transfer event.
    """
    (base_params, error) = transfer_indexer.parse_base_params(event)
    if base_params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    event.function_id = base_params["tid"]

    token = await data_processer.get_token(base_params["tid"])
    if token is None:
        return error_event(event, f"Failed to get token: {base_params['tid']}")

    (params, error) = transfer_indexer.parse_params(event, token, base_params)
    if params is None:
        return error_event(event, f"Failed to parse inscription params: {error}")

    if event.event_type == EventType.INSCRIBE:
        tasks = [
            data_processer.get_pending_inscription(event.receiver),
            data_processer.get_balance(event.receiver, base_params["tid"]),
        ]
        (pending_ins, balance) = await asyncio.gather(*tasks)

        if pending_ins is None:
            pending_ins = Pending_Inscriptions(event.receiver, [])
        if balance is None:
            return error_event(
                event,
                f"Failed to get user balance, user: {event.receiver}, tid: {base_params['tid']}",
            )

        (valid, error) = transfer_indexer.is_valid_event(balance, params)
        if valid is False:
            return error_event(event, error)

        sender_balance = transfer_indexer.process_inscribe(params, token, balance)

        pending_ins.inscriptions.append(event.inscription_id)

        tasks = [
            data_processer.save_balance(sender_balance),
            data_processer.save_pending_inscription(pending_ins),
        ]
        await asyncio.gather(*tasks)

        return event

    else:
        if event.receiver == "":
            event.receiver = event.sender

        tasks = [
            data_processer.get_pending_inscription(event.sender),
            data_processer.get_balance(event.sender, base_params["tid"]),
            data_processer.get_balance(event.receiver, base_params["tid"]),
        ]

        (
            sender_pending_ins,
            sender_balance,
            receiver_balance,
        ) = await asyncio.gather(*tasks)

        if (
            sender_pending_ins is None
            or event.inscription_id not in sender_pending_ins.inscriptions
        ):
            return error_event(event, "invalid inscription")

        if sender_balance is None:
            return error_event(
                event,
                f"Failed to get user balance, user: {event.sender}, tid: {base_params['tid']}",
            )

        if receiver_balance is None:
            receiver_balance = new_balance(event.receiver, token)

        (
            sender_balance,
            receiver_balance,
            is_transfer_to_self,
        ) = transfer_indexer.process_transfer(
            token, params, sender_balance, receiver_balance
        )

        sender_pending_ins.inscriptions.remove(event.inscription_id)

        tasks = [
            data_processer.save_token(token),
            data_processer.save_balance(sender_balance),
            data_processer.save_pending_inscription(sender_pending_ins),
        ]
        if is_transfer_to_self is False:
            tasks.append(data_processer.save_balance(receiver_balance))

        await asyncio.gather(*tasks)

        return event
