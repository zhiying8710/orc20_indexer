from decimal import Decimal


class OTC:
    """
    Represents an OTC order.

    Attributes:
        id (int): The unique identifier of the OTC trade.
        tick1 (str): The ticker symbol of the first token in the trade.
        tid1 (int): The token ID of the first token in the trade.
        supply (Decimal): The supply of the first token in the trade.
        tick2 (str): The ticker symbol of the second token in the trade.
        tid2 (int): The token ID of the second token in the trade.
        er (Decimal): The exchange rate between the two tokens.
        mba (Decimal): The minimum buy amount for the trade.
        dl (int): The deadline for the trade.
        owner (str): The address of the trade owner.
        deploy_time (int): The timestamp of when the trade was deployed.
        inscription_id (str): The ID of the trade inscription.
        valid (bool, optional): Indicates if the trade is valid. Defaults to True.
        success (bool, optional): Indicates if the trade was successful. Defaults to False.
        received (Decimal, optional): The amount of tokens received in the trade. Defaults to 0.
        execute_id (str, optional): The ID of the trade execution. Defaults to "".
    """

    def __init__(
        self,
        id: int,
        tick1: str,
        tid1: int,
        supply: Decimal,
        tick2: str,
        tid2: int,
        er: Decimal,
        mba: Decimal,
        dl: int,
        owner: str,
        deploy_time: int,
        inscription_id: str,
        valid: bool = True,
        success: bool = False,
        received: Decimal = Decimal("0"),
        execute_id: str = "",
    ) -> None:
        self.id = id
        self.tick1 = tick1
        self.tid1 = tid1
        self.supply = supply
        self.tick2 = tick2
        self.tid2 = tid2
        self.er = er
        self.mba = mba
        self.dl = dl
        self.owner = owner
        self.deploy_time = deploy_time
        self.inscription_id = inscription_id
        self.valid = valid
        self.success = success
        self.received = received
        self.execute_id = execute_id
