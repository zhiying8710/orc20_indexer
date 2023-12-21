from decimal import Decimal


class Token:
    """
    Represents a token in the system.

    Args:
        id (int): The number of the inscription which the token deployed on.
        tick (str): The ticker symbol of the token.
        max (Decimal): The maximum supply of the token.
        lim (Decimal): The limit amount per mint inscription.
        dec (int): The number of decimal places for the token.
        ug (bool): Indicates if the token is upgradable.
        mp (bool): Indicates if the token is a mint-protected token.
        deployer (str): The address of the token deployer.
        deploy_time (int): The timestamp of when the token was deployed.
        inscription_id (str): The ID of the inscription which the token deployed on.
        first_number (int, optional): The number of the inscription that first mint. Defaults to 0.
        first_id (str, optional): The ID of the inscription that first mint. Defaults to "".
        first_time (int, optional): The timestamp of inscription that first mint. Defaults to 0.
        last_number (int, optional): The number of the inscription that last mint. Defaults to 0.
        last_id (str, optional): The ID of the inscription that last mint. Defaults to "".
        last_time (int, optional): The timestamp of the inscription that last mint. Defaults to 0.
        minted (Decimal, optional): The total amount of tokens minted. Defaults to Decimal("0").
        burned (Decimal, optional): The total amount of tokens burned. Defaults to Decimal("0").
        circulating (Decimal, optional): The total amount of tokens in circulation. Defaults to Decimal("0").
        holders (int, optional): The number of token holders. Defaults to 0.
        last_upgrade_time (int, optional): The timestamp of the last token upgrade. Defaults to 0.
        upgrade_records (list[str], optional): The list of upgrade records. Defaults to [].
    """

    def __init__(
        self,
        id: int,
        tick: str,
        max: Decimal,
        lim: Decimal,
        dec: int,
        ug: bool,
        mp: bool,
        deployer: str,
        deploy_time: int,
        inscription_id: str,
        first_number: int = 0,
        first_id: str = "",
        first_time: int = 0,
        last_number: int = 0,
        last_id: str = "",
        last_time: int = 0,
        minted: Decimal = Decimal("0"),
        burned: Decimal = Decimal("0"),
        circulating: Decimal = Decimal("0"),
        holders: int = 0,
        last_upgrade_time: int = 0,
        upgrade_records: list[str] = [],
    ) -> None:
        self.id = id
        self.tick = tick
        self.max = max
        self.lim = lim
        self.dec = dec
        self.ug = ug
        self.mp = mp
        self.deployer = deployer
        self.deploy_time = deploy_time
        self.inscription_id = inscription_id
        self.first_number = first_number
        self.first_id = first_id
        self.first_time = first_time
        self.last_number = last_number
        self.last_id = last_id
        self.last_time = last_time
        self.minted = minted
        self.burned = burned
        self.circulating = circulating
        self.holders = holders
        self.last_upgrade_time = last_upgrade_time
        self.upgrade_records = upgrade_records
