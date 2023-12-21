class Pending_Inscriptions:
    """
    Represents an pending inscriptions list.

    Attributes:
        id (int): The inscription ID.
        inscriptions (list(str)): The list of the pending inscription IDs.
    """

    def __init__(
        self,
        id: str,
        inscriptions: list,
    ) -> None:
        self.id = id
        self.inscriptions = inscriptions
