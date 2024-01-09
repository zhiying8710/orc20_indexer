
class Brc20_Token_Ledger_Log:
    def __init__(
            self,
            id: int,
            inscription_id: str,
            inscription_number: int,
            txid: str,
            block: int,
    ):
        self.id = id
        self.inscription_id = inscription_id
        self.inscription_number = inscription_number
        self.txid = txid
        self.block = block