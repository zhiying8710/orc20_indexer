import os
import sys
from typing import Union, Tuple
from decimal import Decimal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token, Balance, OTC, OTC_Record
from src.indexer.utils.field import parse_amt
from src.indexer.utils.commom import (
    parse_tick_and_tid_and_function_id,
    amt_mul,
    amt_div,
    amt_sub,
    amt_add,
)


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
            "oid",
            "tick",
            "tid",
            "amt",
        ]:
            error = "unknown key in params"
            return None, error

    return parse_tick_and_tid_and_function_id(event, "oid")


def parse_params(
    event: Event, token2: Token, base_params: dict
) -> Tuple[Union[dict, None], str]:
    """
    Parse the additional parameters from the event.

    Args:
        event (Event): The event object.
        token2 (Token): The second token object.
        base_params (dict): The base parameters.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed parameters and an error message if any.

    """
    if base_params["tick"] != token2.tick:
        error = "tick is not matched"
        return None, error

    params = event.content.get("params", {})

    amt = parse_amt(params, token2.dec, "amt", token2.max)
    if amt is None:
        error = "invalid amt"
        return None, error

    base_params["amt"] = amt

    return base_params, ""


def is_valid_event(
    event: Event, params: dict, token2: Token, token2_balance: Balance, otc: OTC
) -> Tuple[bool, str]:
    """
    Check if the event is valid for buying.

    Args:
        event (Event): The event object.
        params (dict): The parsed parameters.
        token2 (Token): The second token object.
        token2_balance (Balance): The balance of the second token.
        otc (OTC): The OTC object.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the event is valid and an error message if any.

    """
    if otc.valid is False:
        error = "otc is not valid"
        return False, error

    if otc.dl < event.timestamp:
        error = "otc is expired"
        return False, error

    max_otc_receive = amt_mul(otc.supply, otc.er, token2.dec)
    if otc.received == max_otc_receive:
        error = "otc is sold out"
        return False, error

    if params["amt"] < otc.mba:
        error = "buy amount is less than minimum buy amount"
        return False, error

    available_amt = amt_sub(max_otc_receive, otc.received, token2.dec)
    if available_amt < params["amt"]:
        error = "buy amount is greater than available otc"
        return False, error

    if token2_balance.available_balance < params["amt"]:
        error = "buy amount is greater than available balance"
        return False, error

    return True, ""


def process_buy(
    event: Event,
    params: dict,
    token1: Token,
    token2: Token,
    token2_balance: Balance,
    otc: OTC,
) -> Tuple[Token, Balance, OTC, OTC_Record]:
    """
    Process the buy event.

    Args:
        event (Event): The event object.
        params (dict): The parsed parameters.
        token1 (Token): The first token object.
        token2 (Token): The second token object.
        token2_balance (Balance): The balance of the second token.
        otc (OTC): The OTC object.

    Returns:
        Tuple[Token, Balance, OTC, OTC_Record]: A tuple containing the updated token, balance, OTC, and OTC record.

    """
    token2_balance.available_balance = amt_sub(
        token2_balance.available_balance, params["amt"], token2.dec
    )
    token2_balance.balance = amt_sub(token2_balance.balance, params["amt"], token2.dec)

    if token2_balance.balance == 0:
        token2.holders -= 1

    otc.received = amt_add(otc.received, params["amt"], token2.dec)
    user_received = amt_div(params["amt"], otc.er, token1.dec)
    otc_record = create_otc_record(event, otc, params["amt"], user_received)

    return token2, token2_balance, otc, otc_record


def create_otc_record(
    event: Event, otc: OTC, amount_out: Decimal, amount_in: Decimal
) -> OTC_Record:
    """
    Create an OTC record.

    Args:
        event (Event): The event object.
        otc (OTC): The OTC object.
        amount_out (Decimal): The amount of the second token sold.
        amount_in (Decimal): The amount of the first token received.

    Returns:
        OTC_Record: The created OTC record.

    """
    return OTC_Record(
        event.id, otc.id, event.inscription_id, event.sender, amount_out, amount_in
    )
