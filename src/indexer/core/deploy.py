import os
import sys
from typing import Union, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token
from src.indexer.utils.field import (
    parse_tick,
    parse_dec,
    parse_max,
    parse_lim,
    parse_ug,
    parse_mp,
)


def parse_params(event: Event) -> Tuple[Union[dict, None], str]:
    """
    Parse the parameters from the event content.

    Args:
        event (Event): The event containing the parameters.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed parameters and an error message if any.

    """
    params = event.content.get("params", {})

    for key in params.keys():
        if key not in ["tick", "max", "lim", "dec", "ug", "mp", "tid"]:
            error = "unknown key in params"
            return None, error

    tick = parse_tick(params)
    if tick is None:
        error = "invalid tick"
        return None, error

    dec = parse_dec(params)
    if dec is None:
        error = "invalid dec"
        return None, error

    max = parse_max(params, dec)
    if max is None:
        error = "invalid max"
        return None, error

    lim = parse_lim(params, dec, max)
    if lim is None:
        error = "invalid lim"
        return None, error

    ug = parse_ug(params)
    if ug is None:
        error = "invalid ug"
        return None, error

    mp = parse_mp(params)
    if mp is None:
        error = "invalid mp"
        return None, error

    return {"tick": tick, "dec": dec, "max": max, "lim": lim, "ug": ug, "mp": mp}, ""


def process_deploy(event: Event, params: dict) -> Token:
    """
    Process the deployment of a token.

    Args:
        event (Event): The event triggering the deployment.
        params (dict): The parsed parameters for the deployment.

    Returns:
        Token: The deployed token.

    """
    token = Token(
        event.inscription_number,
        params["tick"],
        params["max"],
        params["lim"],
        params["dec"],
        params["ug"],
        params["mp"],
        event.receiver,
        event.timestamp,
        event.inscription_id,
    )

    return token
