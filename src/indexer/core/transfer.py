import os
import sys
from typing import Union, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token, Balance
from src.indexer.utils.field import parse_amt
from src.indexer.utils.commom import parse_tick_and_tid, amt_add, amt_sub


def parse_base_params(event: Event) -> Tuple[Union[dict, None], str]:
    """
    Parse the base parameters from the event.

    Args:
        event (Event): The event object.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed base parameters and an error message if any.

    """

    params = event.content.get("params", {})

    for key in params.keys():
        if key not in ["tick", "tid", "amt"]:
            error = "unknown key in params"
            return None, error

    return parse_tick_and_tid(event)


def parse_params(
    event: Event, token: Token, base_params: dict
) -> Tuple[Union[dict, None], str]:
    """
    Parse the parameters from the event.

    Args:
        event (Event): The event object.
        token (Token): The token object.
        base_params (dict): The base parameters.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed parameters and an error message if any.

    """

    if base_params["tick"] != token.tick:
        error = "tick is not matched"
        return None, error

    params = event.content.get("params", {})

    amt = parse_amt(params, token.dec, "amt", token.max)
    if amt is None:
        error = "invalid amt"
        return None, error

    base_params["amt"] = amt

    return base_params, ""


def is_valid_event(balance: Balance, params: dict) -> Tuple[bool, str]:
    """
    Check if the event is valid.

    Args:
        balance (Balance): The balance object.
        params (dict): The parameters.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the event is valid and an error message if any.

    """

    if balance.available_balance < params["amt"]:
        error = "inscribe transfer amount is greater than available balance"
        return False, error

    return True, ""


def process_inscribe(
    params: dict,
    token: Token,
    balance: Balance,
) -> Balance:
    """
    Process the inscribe transfer.

    Args:
        params (dict): The parameters.
        token (Token): The token object.
        balance (Balance): The balance object.

    Returns:
        Balance: The updated balance object.

    """

    balance.available_balance = amt_sub(
        balance.available_balance, params["amt"], token.dec
    )
    balance.transferable_balance = amt_add(
        balance.transferable_balance, params["amt"], token.dec
    )

    return balance


def process_transfer(
    token: Token,
    params: dict,
    sender_balance: Balance,
    receiver_balance: Balance,
) -> Tuple[Balance, Balance, bool]:
    """
    Process the transfer.

    Args:
        token (Token): The token object.
        params (dict): The parameters.
        sender_balance (Balance): The sender's balance object.
        receiver_balance (Balance): The receiver's balance object.

    Returns:
        Tuple[Balance, Balance, bool]: A tuple containing the updated sender's balance, receiver's balance, and a boolean indicating if the sender and receiver are the same.

    """

    if sender_balance.address == receiver_balance.address:
        sender_balance.available_balance = amt_add(
            sender_balance.available_balance, params["amt"], token.dec
        )
        sender_balance.transferable_balance = amt_sub(
            sender_balance.transferable_balance, params["amt"], token.dec
        )
        receiver_balance = sender_balance
        return sender_balance, receiver_balance, True

    # update sender

    sender_balance.transferable_balance = amt_sub(
        sender_balance.transferable_balance, params["amt"], token.dec
    )
    sender_balance.balance = amt_sub(sender_balance.balance, params["amt"], token.dec)
    if sender_balance.balance == 0:
        token.holders -= 1

    # update receiver
    if receiver_balance.balance == 0:
        token.holders += 1
    receiver_balance.available_balance = amt_add(
        receiver_balance.available_balance, params["amt"], token.dec
    )
    receiver_balance.balance = amt_add(
        receiver_balance.balance, params["amt"], token.dec
    )

    return sender_balance, receiver_balance, False
