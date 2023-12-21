from typing import Union
from decimal import Decimal, getcontext


def parse_tick(data: dict, key: str = "tick") -> Union[str, None]:
    """
    Parse the tick value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        key (str, optional): The key to retrieve the tick value. Defaults to "tick".

    Returns:
        Union[str, None]: The parsed tick value or None if it cannot be parsed.
    """
    if key not in data:
        return None

    tick = data[key]
    if not isinstance(tick, str):
        return None

    tick = tick.lower()

    try:
        b_tick = tick.encode("utf-8")
    except UnicodeEncodeError:
        return None

    if len(b_tick) == 0 or len(b_tick) > 255:
        return None

    return tick


def parse_tid(data: dict, key: str = "tid") -> Union[int, None]:
    """
    Parse the tid value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        key (str, optional): The key to retrieve the tid value. Defaults to "tid".

    Returns:
        Union[int, None]: The parsed tid value or None if it cannot be parsed.
    """
    if key not in data:
        return None

    tid = data[key]
    if not isinstance(tid, str):
        return None

    try:
        tid = int(tid)
    except ValueError:
        return None

    return tid


def parse_dec(data: dict) -> Union[int, None]:
    """
    Parse the dec value from the given data dictionary.

    Args:
        data (dict): The data dictionary.

    Returns:
        Union[int, None]: The parsed dec value or None if it cannot be parsed.
    """
    if "dec" not in data:
        return 18

    dec = data["dec"]
    if not isinstance(dec, str):
        return None

    try:
        dec = int(dec)
    except ValueError:
        return None

    if dec < 0 or dec > 18:
        return None

    return dec


def parse_ug(data: dict, default: bool = True) -> Union[bool, None]:
    """
    Parse the ug value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        default (bool, optional): The default value if "ug" is not present. Defaults to True.

    Returns:
        Union[bool, None]: The parsed ug value or None if it cannot be parsed.
    """
    if "ug" not in data:
        if default is True:
            return False
        else:
            return None

    ug = data["ug"]
    if not isinstance(ug, str):
        return None
    ug = ug.lower()

    if ug not in ["true", "false"]:
        return None

    if ug == "true":
        return True
    else:
        return False


def parse_mp(data: dict, default: bool = True) -> Union[bool, None]:
    """
    Parse the mp value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        default (bool, optional): The default value if "mp" is not present. Defaults to True.

    Returns:
        Union[bool, None]: The parsed mp value or None if it cannot be parsed.
    """
    if "mp" not in data:
        if default is True:
            return False
        else:
            return None

    mp = data["mp"]
    if not isinstance(mp, str):
        return None

    mp = mp.lower()

    if mp not in ["true", "false"]:
        return None

    if mp == "true":
        return True
    else:
        return False


def parse_dl(data: dict, timestamp: int, key: str = "dl") -> Union[int, None]:
    """
    Parse the dl value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        timestamp (int): The timestamp value.
        key (str, optional): The key to retrieve the dl value. Defaults to "dl".

    Returns:
        Union[int, None]: The parsed dl value or None if it cannot be parsed.
    """
    if key not in data:
        return None

    dl = data.get(key)
    if not isinstance(dl, str):
        return None

    try:
        dl = int(dl)
    except ValueError:
        return None

    if dl <= timestamp:
        return None

    return dl


def parse_ids(data: dict, key: str) -> Union[list[int], None]:
    """
    Parse the ids value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        key (str): The key to retrieve the ids value.

    Returns:
        Union[list[int], None]: The parsed ids value or None if it cannot be parsed.
    """
    if key not in data:
        return None

    ids = data.get(key)
    if not isinstance(ids, list):
        return None

    new_ids = []
    for id in ids:
        if not isinstance(id, str):
            return None
        try:
            tid = int(id)
        except ValueError:
            return None

        new_ids.append(tid)

    return new_ids


def parse_mba(data: dict, dec: int, max: Decimal) -> Union[Decimal, None]:
    """
    Parse the mba value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        dec (int): The decimal value.
        max (Decimal): The maximum value.

    Returns:
        Union[Decimal, None]: The parsed mba value or None if it cannot be parsed.
    """
    if "mba" not in data:
        return Decimal("1")
    return parse_amt(data, dec, "mba", max, False)


def parse_max(data: dict, dec: int) -> Union[Decimal, None]:
    """
    Parse the max value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        dec (int): The decimal value.

    Returns:
        Union[Decimal, None]: The parsed max value or None if it cannot be parsed.
    """
    return parse_amt(data, dec, "max")


def parse_lim(
    data: dict, dec: int, max: Decimal, default: bool = True
) -> Union[Decimal, None]:
    """
    Parse the lim value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        dec (int): The decimal value.
        max (Decimal): The maximum value.
        default (bool, optional): The default value if "lim" is not present. Defaults to True.

    Returns:
        Union[Decimal, None]: The parsed lim value or None if it cannot be parsed.
    """
    if "lim" not in data:
        if default is True:
            return Decimal("1")
        else:
            return None
    return parse_amt(data, dec, "lim", max)


def parse_er(data: dict, dec: int) -> Union[Decimal, None]:
    """
    Parse the er value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        dec (int): The decimal value.

    Returns:
        Union[Decimal, None]: The parsed er value or None if it cannot be parsed.
    """
    return parse_amt(data, dec, "er")


max_uint64 = 2**64 - 1
max_amt = Decimal(f"{max_uint64}.999999999999999999")
max_precision = 38


def parse_amt(
    data: dict,
    dec: int,
    key: str = "amt",
    lim: Decimal = max_amt,
    be_zero: bool = False,
) -> Union[Decimal, None]:
    """
    Parse the amt value from the given data dictionary.

    Args:
        data (dict): The data dictionary.
        dec (int): The decimal value.
        key (str, optional): The key to retrieve the amt value. Defaults to "amt".
        lim (Decimal, optional): The limit value. Defaults to max_amt.
        be_zero (bool, optional): Whether amt can be zero. Defaults to False.

    Returns:
        Union[Decimal, None]: The parsed amt value or None if it cannot be parsed.
    """
    if key not in data:
        return None

    amt = data[key]
    if not isinstance(amt, str):
        return None

    if "+" in amt or "-" in amt:
        return None

    getcontext().prec = max_precision

    if "." in amt:
        if amt[0] == "." or amt[-1] == ".":
            return None

        if len(amt.split(".")[1]) > dec:
            return None

        try:
            amt = Decimal(amt)
        except ValueError:
            return None

    else:
        try:
            amt = int(amt)
            amt = Decimal(amt)
        except ValueError:
            return None

    if amt > lim or amt < 0:
        return None

    if be_zero is False and amt == 0:
        return None

    return amt
