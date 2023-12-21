import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token, Balance, Pending_Inscriptions
from src.data.processer.interface import Interface as DataProcesser


def new_balance(address: str, token: Token) -> Balance:
    """
    Create a new Balance object.

    Args:
        address (str): The address associated with the balance.
        token (Token): The token object.

    Returns:
        Balance: The newly created Balance object.
    """
    id = f"{address}-{token.id}"
    return Balance(id, token.tick, token.id, token.inscription_id, address)


async def handle_inscribe(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the inscription event.

    Args:
        event (Event): The inscription event.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated inscription event.
    """
    pending_ins = await data_processer.get_pending_inscription(event.receiver)

    if pending_ins is None:
        pending_ins = Pending_Inscriptions(event.receiver, [])

    if event.inscription_id in pending_ins.inscriptions:
        return event

    pending_ins.inscriptions.append(event.inscription_id)

    await data_processer.save_pending_inscription(pending_ins)

    return event


def error_event(event: Event, error: str) -> Event:
    """
    Create an error event.

    Args:
        event (Event): The original event.
        error (str): The error message.

    Returns:
        Event: The updated event with error information.
    """
    event.valid = False
    event.error = error
    return event
