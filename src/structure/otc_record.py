from decimal import Decimal


class OTC_Record:
    """
    Represents an OTC record.

    Attributes:
        id (str): The event ID.
        oid (int): The OTC ID.
        inscription_id (str): The inscription ID.
        address (str): The address.
        amount_out (Decimal): The amount out.
        amount_in (Decimal): The amount in.
    """

    def __init__(
        self,
        id: str,  # event id
        oid: int,
        inscription_id: str,
        address: str,
        amount_out: Decimal,
        amount_in: Decimal,
    ) -> None:
        self.id = id
        self.oid = oid
        self.inscription_id = inscription_id
        self.address = address
        self.amount_out = amount_out
        self.amount_in = amount_in
