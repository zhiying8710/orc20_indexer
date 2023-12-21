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
        error = "burn amount is greater than available balance"
        return False, error

    return True, ""


def process_burn(
    params: dict,
    token: Token,
    balance: Balance,
) -> Tuple[Token, Balance]:
    """
    Process the burn event.

    Args:
        params (dict): The parameters.
        token (Token): The token object.
        balance (Balance): The balance object.

    Returns:
        Tuple[Token, Balance]: A tuple containing the updated token and balance objects.

    """
    balance.balance = amt_sub(balance.balance, params["amt"], token.dec)
    balance.available_balance = amt_sub(
        balance.available_balance, params["amt"], token.dec
    )

    if balance.balance == 0:
        token.holders -= 1

    token.burned = amt_add(token.burned, params["amt"], token.dec)
    token.circulating = amt_sub(token.circulating, params["amt"], token.dec)

    return token, balance
