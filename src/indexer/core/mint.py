import os
import sys
from typing import Union, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token, Balance
from src.indexer.utils.field import parse_amt
from src.indexer.utils.commom import parse_tick_and_tid, amt_add


def parse_base_params(event: Event) -> Tuple[Union[dict, None], str]:
    """
    Parse the base parameters from the event.

    Args:
        event (Event): The event object.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed base parameters and an error message (if any).
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
        Tuple[Union[dict, None], str]: A tuple containing the parsed parameters and an error message (if any).
    """

    if base_params["tick"] != token.tick:
        error = "tick is not matched"
        return None, error

    params = event.content.get("params", {})

    amt = parse_amt(params, token.dec, "amt", token.lim)
    if amt is None:
        error = "invalid amt"
        return None, error

    base_params["amt"] = amt

    return base_params, ""


def is_valid_event(event: Event, token: Token, params: dict) -> Tuple[bool, str]:
    """
    Check if the event is valid.

    Args:
        event (Event): The event object.
        token (Token): The token object.
        params (dict): The parsed parameters.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the event is valid and an error message (if any).
    """

    if token.mp is True and event.receiver != token.deployer:
        error = "token minting is protected and minter is not deployer"
        return False, error

    if token.max - token.minted < params["amt"]:
        error = "token minting is over max"
        return False, error

    return True, ""


def process_mint(
    event: Event, params: dict, token: Token, balance: Balance
) -> Tuple[Token, Balance]:
    """
    Process the mint event.

    Args:
        event (Event): The event object.
        params (dict): The parsed parameters.
        token (Token): The token object.
        balance (Balance): The balance object.

    Returns:
        Tuple[Token, Balance]: A tuple containing the updated token and balance objects.
    """

    # update token
    if token.minted == 0:
        token.first_number = event.inscription_number
        token.first_time = event.timestamp
        token.first_id = event.inscription_id

    if token.max - token.minted == params["amt"]:
        token.last_number = event.inscription_number
        token.last_time = event.timestamp
        token.last_id = event.inscription_id

    token.minted = amt_add(token.minted, params["amt"], token.dec)
    token.circulating = amt_add(token.circulating, params["amt"], token.dec)

    # update address
    if balance.balance == 0:
        token.holders += 1

    balance.balance = amt_add(balance.balance, params["amt"], token.dec)
    balance.available_balance = amt_add(
        balance.available_balance, params["amt"], token.dec
    )

    return token, balance
