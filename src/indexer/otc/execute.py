import os
import sys
from tokenize import Token
from typing import Union, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token, Balance, OTC, OTC_Record
from src.indexer.utils.field import parse_tid
from src.indexer.utils.commom import amt_mul, amt_sub, amt_add, amt_zero


def parse_params(event: Event) -> Tuple[Union[dict, None], str]:
    """
    Parse the parameters from the event content.

    Args:
        event (Event): The event object.

    Returns:
        Tuple[Union[dict, None], str]: A tuple containing the parsed parameters and an error message (if any).
    """
    params = event.content.get("params", {})

    oid = parse_tid(params, "oid")
    if oid is None:
        error = "invalid oid"
        return None, error

    params["oid"] = oid
    return params, ""


def is_valid_event(event: Event, otc: OTC, token2: Token) -> Tuple[bool, str]:
    """
    Check if the event is a valid OTC event.

    Args:
        event (Event): The event object.
        otc (OTC): The OTC object.
        token2 (Token): The second token object.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the event is valid and an error message (if any).
    """
    if otc.valid is False:
        error = "otc is not valid"
        return False, error

    max_otc_receive = amt_mul(otc.supply, otc.er, token2.dec)
    token1_left = amt_sub(max_otc_receive, otc.received, token2.dec)
    if otc.dl > event.timestamp and token1_left >= otc.mba:
        error = "otc is not due"
        return False, error

    return True, ""


def process_execute(
    event: Event,
    otc: OTC,
    token1: Token,
    token2: Token,
    buyer_records: list[OTC_Record],
    seller_token1_balance: Balance,
    seller_token2_balance: Balance,
    buyer_token1_balances: list[Balance],
    buyer_token2_balances: list[Balance],
) -> Tuple[Token, Token, OTC, list[Balance]]:
    """
    Process the execution of an OTC event.

    Args:
        event (Event): The event object.
        otc (OTC): The OTC object.
        token1 (Token): The first token object.
        token2 (Token): The second token object.
        buyer_records (list[OTC_Record]): The list of buyer OTC records.
        seller_token1_balance (Balance): The seller's token1 balance.
        seller_token2_balance (Balance): The seller's token2 balance.
        buyer_token1_balances (list[Balance]): The list of buyer's token1 balances.
        buyer_token2_balances (list[Balance]): The list of buyer's token2 balances.

    Returns:
        Tuple[Token, Token, OTC, list[Balance]]: A tuple containing the updated token1, token2, OTC, and balance objects.
    """
    max_otc_receive = amt_mul(otc.supply, otc.er, token2.dec)
    token2_left = amt_sub(max_otc_receive, otc.received, token2.dec)
    if token2_left < otc.mba:
        (token1, token2, otc, ret_balances) = distribute(
            event,
            token1,
            token2,
            otc,
            buyer_records,
            seller_token2_balance,
            buyer_token1_balances,
        )

        total_distribute_tick1_amount = amt_zero()
        for record in buyer_records:
            total_distribute_tick1_amount = amt_add(
                total_distribute_tick1_amount, record.amount_in, token1.dec
            )

        if total_distribute_tick1_amount < otc.supply:
            token1_left = amt_sub(otc.supply, total_distribute_tick1_amount, token1.dec)

            # find is there is a balance for seller in ret_balances
            for balance in ret_balances:
                if balance.address == otc.owner and balance.tid == otc.tid1:
                    seller_token1_balance = balance
                    ret_balances.remove(balance)
                    break

            # return token1 to seller
            if seller_token1_balance.balance == 0:
                token1.holders += 1

            seller_token1_balance.balance = amt_add(
                seller_token1_balance.balance, token1_left, token1.dec
            )
            seller_token1_balance.available_balance = amt_add(
                seller_token1_balance.available_balance, token1_left, token1.dec
            )
            ret_balances.append(seller_token1_balance)

        return (token1, token2, otc, ret_balances)

    else:
        return Refund(
            event,
            token1,
            token2,
            otc,
            buyer_records,
            seller_token1_balance,
            buyer_token2_balances,
        )


def distribute(
    event: Event,
    token1: Token,
    token2: Token,
    otc: OTC,
    buyer_records: list[OTC_Record],
    seller_token2_balance: Balance,
    buyer_token1_balances: list[Balance],
) -> Tuple[Token, Token, OTC, list[Balance]]:
    """
    Distribute the tokens and update the balances after a successful OTC execution.

    Args:
        event (Event): The event object.
        token1 (Token): The first token object.
        token2 (Token): The second token object.
        otc (OTC): The OTC object.
        buyer_records (list[OTC_Record]): The list of buyer OTC records.
        seller_token2_balance (Balance): The seller's token2 balance.
        buyer_token1_balances (list[Balance]): The list of buyer's token1 balances.

    Returns:
        Tuple[Token, Token, OTC, list[Balance]]: A tuple containing the updated token1, token2, OTC, and balance objects.
    """
    # update otc info
    otc.success = True
    otc.valid = False
    otc.execute_id = event.inscription_id

    # update seller balance
    if seller_token2_balance.balance == 0:
        token2.holders += 1

    seller_token2_balance.available_balance = amt_add(
        seller_token2_balance.available_balance, otc.received, token2.dec
    )
    seller_token2_balance.balance = amt_add(
        seller_token2_balance.balance, otc.received, token2.dec
    )

    # update buyer balance
    user_balance_map = {balance.address: balance for balance in buyer_token1_balances}
    for record in buyer_records:
        balance = user_balance_map[record.address]

        if balance.balance == 0:
            token1.holders += 1

        balance.available_balance = amt_add(
            balance.available_balance, record.amount_in, token1.dec
        )
        balance.balance = amt_add(balance.balance, record.amount_in, token1.dec)

        user_balance_map[record.address] = balance

    ret_balances = list(user_balance_map.values())
    ret_balances.append(seller_token2_balance)

    return (token1, token2, otc, ret_balances)


def Refund(
    event: Event,
    token1: Token,
    token2: Token,
    otc: OTC,
    buyer_records: list[OTC_Record],
    seller_token1_balance: Balance,
    buyer_token2_balances: list[Balance],
) -> Tuple[Token, Token, OTC, list[Balance]]:
    """
    Refund the tokens and update the balances after a failed OTC execution.

    Args:
        event (Event): The event object.
        token1 (Token): The first token object.
        token2 (Token): The second token object.
        otc (OTC): The OTC object.
        buyer_records (list[OTC_Record]): The list of buyer OTC records.
        seller_token1_balance (Balance): The seller's token1 balance.
        buyer_token2_balances (list[Balance]): The list of buyer's token2 balances.

    Returns:
        Tuple[Token, Token, OTC, list[Balance]]: A tuple containing the updated token1, token2, OTC, and balance objects.
    """
    # update otc info
    otc.success = False
    otc.valid = False
    otc.execute_id = event.inscription_id

    # update seller balance
    if seller_token1_balance.balance == 0:
        token1.holders += 1

    seller_token1_balance.available_balance = amt_add(
        seller_token1_balance.available_balance, otc.supply, token1.dec
    )
    seller_token1_balance.balance = amt_add(
        seller_token1_balance.balance, otc.supply, token1.dec
    )

    if len(buyer_records) == 0:
        return (token1, token2, otc, [seller_token1_balance])

    # update buyer balance
    user_balance_map = {balance.address: balance for balance in buyer_token2_balances}
    for record in buyer_records:
        balance = user_balance_map[record.address]

        if balance.balance == 0:
            token2.holders += 1

        balance.available_balance = amt_add(
            balance.available_balance, record.amount_out, token2.dec
        )
        balance.balance = amt_add(balance.balance, record.amount_out, token2.dec)

        user_balance_map[record.address] = balance

    ret_balances = list(user_balance_map.values())
    ret_balances.append(seller_token1_balance)

    return (token1, token2, otc, ret_balances)
