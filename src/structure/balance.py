from decimal import Decimal


class Balance:
    """
    Represents a balance for a specific address and token.

    Attributes:
        id (str): The unique identifier of the balance.
        tick (str): The tick of the token.
        tid (int): The inscription number associated with the token.
        inscription_id (str): The inscription ID associated with the token.
        address (str): User address.
        balance (Decimal): The total balance.
        available_balance (Decimal): The available balance.
        transferable_balance (Decimal): The transferable balance.
        original_balance (Decimal): The original balance.

    """

    def __init__(
        self,
        id: str,
        tick: str,
        tid: int,
        inscription_id: str,
        address: str,
        balance: Decimal = Decimal("0"),
        available_balance: Decimal = Decimal("0"),
        transferable_balance: Decimal = Decimal("0"),
        original_balance: Decimal = Decimal("0"),
    ) -> None:
        self.id = id
        self.tid = tid
        self.tick = tick
        self.inscription_id = inscription_id
        self.address = address
        self.balance = balance
        self.available_balance = available_balance
        self.transferable_balance = transferable_balance
        self.original_balance = original_balance
