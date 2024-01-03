

class Inscription:

    def __init__(
            self,
            id: int,
            inscription_number: int,
            inscription_id: str,
            owner: str,
            content_type: str,
            content: str,
            timestamp: int,
            genesis_height: int,
            location: str
    ):
        self.id = id
        self.inscription_number = inscription_number
        self.inscription_id = inscription_id
        self.owner = owner
        self.content_type = content_type
        self.content = content
        self.timestamp = timestamp
        self.genesis_height = genesis_height
        self.location = location
