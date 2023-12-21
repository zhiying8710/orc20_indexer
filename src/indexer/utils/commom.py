import os
import sys
import math
from typing import Union, Tuple
from decimal import Decimal, getcontext, ROUND_DOWN

max_precision = 38
getcontext().prec = max_precision

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event
from src.indexer.utils.field import parse_tick, parse_tid


def parse_tick_and_tid(event: Event) -> Tuple[Union[dict, None], str]:
    """
    Parse the tick and tid from the event content.

    Args:
        event (Event): The event object.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed tick and tid as a dictionary,
        and an error message if there was an error during parsing.

    """
    params = event.content.get("params", {})

    tick = parse_tick(params)
    if tick is None:
        error = "invalid tick"
        return None, error

    tid = parse_tid(params)
    if tid is None:
        error = "invalid tid"
        return None, error

    return {"tick": tick, "tid": tid}, ""


def parse_double_tick_and_tid(event: Event) -> Tuple[Union[dict, None], str]:
    """
    Parse the double tick and tid from the event content.

    Args:
        event (Event): The event object.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed double tick and tid as a dictionary,
        and an error message if there was an error during parsing.

    """
    params = event.content.get("params", {})

    tick1 = parse_tick(params, "tick1")
    if tick1 is None:
        error = "invalid tick1"
        return None, error

    tid1 = parse_tid(params, "tid1")
    if tid1 is None:
        error = "invalid tid1"
        return None, error

    tick2 = parse_tick(params, "tick2")
    if tick2 is None:
        error = "invalid tick2"
        return None, error

    tid2 = parse_tid(params, "tid2")
    if tid2 is None:
        error = "invalid tid2"
        return None, error

    base_params = {
        "tick1": tick1,
        "tid1": tid1,
        "tick2": tick2,
        "tid2": tid2,
    }

    return base_params, ""


def parse_tick_and_tid_and_function_id(
    event: Event, function_id_key: str
) -> Tuple[Union[dict, None], str]:
    """
    Parse the tick, tid, and function id from the event content.

    Args:
        event (Event): The event object.
        function_id_key (str): The key for the function id in the event content.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed tick, tid, and function id as a dictionary,
        and an error message if there was an error during parsing.

    """
    params = event.content.get("params", {})

    tick = parse_tick(params)
    if tick is None:
        error = "invalid tick"
        return None, error

    tid = parse_tid(params)
    if tid is None:
        error = "invalid tid"
        return None, error

    function_id = parse_tid(params, function_id_key)
    if function_id is None:
        error = f"invalid {function_id_key}"
        return None, error

    return {"tick": tick, "tid": tid, function_id_key: function_id}, ""


def amt_mul(amt1: Decimal, amt2: Decimal, dec: int) -> Decimal:
    """
    Multiply two decimal numbers and round down to the specified decimal places.

    Args:
        amt1 (Decimal): The first decimal number.
        amt2 (Decimal): The second decimal number.
        dec (int): The number of decimal places to round down to.

    Returns:
        Decimal: The result of the multiplication rounded down to the specified decimal places.

    """
    result = amt1 * amt2
    result = result.quantize(Decimal("0." + "0" * dec), rounding=ROUND_DOWN)
    return result


def amt_div(amt1: Decimal, amt2: Decimal, dec: int) -> Decimal:
    """
    Divide two decimal numbers and round down to the specified decimal places.

    Args:
        amt1 (Decimal): The first decimal number.
        amt2 (Decimal): The second decimal number.
        dec (int): The number of decimal places to round down to.

    Returns:
        Decimal: The result of the division rounded down to the specified decimal places.

    """
    result = amt1 / amt2
    result = result.quantize(Decimal("0." + "0" * dec), rounding=ROUND_DOWN)
    return result


def amt_add(amt1: Decimal, amt2: Decimal, dec: int) -> Decimal:
    """
    Add two decimal numbers and round down to the specified decimal places.

    Args:
        amt1 (Decimal): The first decimal number.
        amt2 (Decimal): The second decimal number.
        dec (int): The number of decimal places to round down to.

    Returns:
        Decimal: The result of the addition rounded down to the specified decimal places.

    """
    result = amt1 + amt2
    result = result.quantize(Decimal("0." + "0" * dec), rounding=ROUND_DOWN)
    return result


def amt_sub(amt1: Decimal, amt2: Decimal, dec: int) -> Decimal:
    """
    Subtract two decimal numbers and round down to the specified decimal places.

    Args:
        amt1 (Decimal): The first decimal number.
        amt2 (Decimal): The second decimal number.
        dec (int): The number of decimal places to round down to.

    Returns:
        Decimal: The result of the subtraction rounded down to the specified decimal places.

    """
    result = amt1 - amt2
    result = result.quantize(Decimal("0." + "0" * dec), rounding=ROUND_DOWN)
    return result


def amt_zero() -> Decimal:
    return Decimal("0")
