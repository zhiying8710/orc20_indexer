import os
import sys
from typing import Union, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token, Balance, OTC
from src.indexer.utils.field import parse_amt, parse_er, parse_dl, parse_mba
from src.indexer.utils.commom import parse_double_tick_and_tid, amt_mul, amt_sub


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
        if key not in [
            "tick1",
            "tid1",
            "tick2",
            "tid2",
            "supply",
            "er",
            "dl",
            "mba",
            "oid",
        ]:
            error = "unknown key in params"
            return None, error

    return parse_double_tick_and_tid(event)


def parse_params(
    event: Event, token1: Token, token2: Token, base_params: dict
) -> Tuple[Union[dict, None], str]:
    """
    Parse the additional parameters from the event.

    Args:
        event (Event): The event object.
        token1 (Token): The first token object.
        token2 (Token): The second token object.
        base_params (dict): The base parameters.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed parameters and an error message if any.

    """
    if base_params["tick1"] != token1.tick:
        error = "tick1 is not matched"
        return None, error

    if base_params["tick2"] != token2.tick:
        error = "tick2 is not matched"
        return None, error

    params = event.content.get("params", {})

    supply = parse_amt(params, token1.dec, "supply", token1.max)
    if supply is None:
        error = "invalid supply"
        return None, error
    base_params["supply"] = supply

    er = parse_er(params, token2.dec)
    if er is None:
        error = "invalid er"
        return None, error
    base_params["er"] = er

    dl = parse_dl(params, event.timestamp)
    if dl is None:
        error = "invalid dl"
        return None, error
    base_params["dl"] = dl

    mba = parse_mba(params, token2.dec, token2.max)
    if mba is None:
        error = "invalid mba"
        return None, error
    base_params["mba"] = mba

    if (
        amt_mul(base_params["supply"], base_params["er"], token2.dec)
        < base_params["mba"]
    ):
        error = "invalid config: supply * er < mba"
        return None, error

    return base_params, ""


def is_valid_event(params: dict, token1_balance: Balance) -> Tuple[bool, str]:
    """
    Check if the event is valid.

    Args:
        params (dict): The parameters.
        token1_balance (Balance): The balance of token1.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the event is valid and an error message if any.

    """
    if token1_balance.available_balance < params["supply"]:
        error = "insufficient available balance to create otc"
        return False, error

    return True, ""


def process_create(
    event: Event,
    params: dict,
    token1: Token,
    token1_balance: Balance,
) -> Tuple[Token, Balance, OTC]:
    """
    Process the create event.

    Args:
        event (Event): The event object.
        params (dict): The parameters.
        token1 (Token): The first token object.
        token1_balance (Balance): The balance of token1.

    Returns:
        Tuple[Token, Balance, OTC]: A tuple containing the updated token1 object, the updated token1 balance object, and the created OTC object.

    """
    token1_balance.available_balance = amt_sub(
        token1_balance.available_balance, params["supply"], token1.dec
    )
    token1_balance.balance = amt_sub(
        token1_balance.balance, params["supply"], token1.dec
    )

    if token1_balance.balance == 0:
        token1.holders -= 1

    otc = OTC(
        event.inscription_number,
        params["tick1"],
        params["tid1"],
        params["supply"],
        params["tick2"],
        params["tid2"],
        params["er"],
        params["mba"],
        params["dl"],
        event.sender,
        event.timestamp,
        event.inscription_id,
    )

    return token1, token1_balance, otc
