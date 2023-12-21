import os
import sys
from typing import Union, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token
from src.indexer.utils.field import parse_max, parse_lim, parse_ug, parse_mp
from src.indexer.utils.commom import parse_tick_and_tid


def parse_base_params(event: Event) -> Tuple[Union[dict, None], str]:
    """
    Parse the base parameters from the event content.

    Args:
        event (Event): The event containing the parameters.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed parameters and an error message if any.

    Raises:
        None

    """
    params = event.content.get("params", {})

    for key in params.keys():
        if key not in ["tick", "tid", "max", "lim", "ug", "mp"]:
            error = "unknown key in params"
            return None, error

    if (
        "max" not in params
        and "lim" not in params
        and "ug" not in params
        and "mp" not in params
    ):
        error = (
            "max & lim & ug & mp cannot be none in upgrade operation at the same time"
        )
        return None, error

    return parse_tick_and_tid(event)


def parse_params(
    event: Event, token: Token, base_params: dict
) -> Tuple[Union[dict, None], str]:
    """
    Parse the parameters from the event content and update the base parameters.

    Args:
        event (Event): The event containing the parameters.
        token (Token): The token object.
        base_params (dict): The base parameters.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed parameters and an error message if any.

    Raises:
        None

    """
    if base_params["tick"] != token.tick:
        error = "tick is not matched"
        return None, error

    params = event.content.get("params", {})

    base_params["max"] = parse_max(params, token.dec)
    max = base_params["max"] if base_params["max"] is not None else token.max
    base_params["lim"] = parse_lim(params, token.dec, max, False)
    base_params["ug"] = parse_ug(params, False)
    base_params["mp"] = parse_mp(params, False)

    if base_params["max"] is not None and base_params["max"] <= token.max:
        error = "max is not enabled to increase"
        return None, error

    return base_params, ""


def is_valid_event(event: Event, token: Token) -> Tuple[bool, str]:
    """
    Check if the event is valid for token upgrade.

    Args:
        event (Event): The event to be checked.
        token (Token): The token object.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the event is valid and an error message if any.

    Raises:
        None

    """
    if event.sender != token.deployer:
        error = "sender is not deployer"
        return False, error

    if token.ug is False:
        error = "token is not upgradable"
        return False, error

    return True, ""


def process_upgrade(event: Event, params: dict, token: Token) -> Token:
    """
    Process the token upgrade based on the parameters.

    Args:
        event (Event): The event triggering the upgrade.
        params (dict): The parameters for the upgrade.
        token (Token): The token object.

    Returns:
        Token: The updated token object.

    Raises:
        None

    """
    if params["max"] is not None:
        token.max = params["max"]

    if params["lim"] is not None:
        token.lim = params["lim"]

    if params["mp"] is not None:
        token.mp = params["mp"]

    if params["ug"] is not None:
        token.ug = params["ug"]

    token.last_upgrade_time = event.timestamp
    token.upgrade_records.append(event.inscription_id)

    return token
