from decimal import Decimal


class Backup_Height:

    def __init__(
        self,
        id: int,  # event id
        block_height: int,
    ) -> None:
        self.id = id
        self.block_height = block_height
