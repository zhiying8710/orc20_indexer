from enum import Enum


class EventType(Enum):
    TRANSFER = "TRANSFER"
    INSCRIBE = "INSCRIBE"


class Event:
    """
    Represents an event in the system.

    Attributes:
        id (str): The unique identifier of the event.
        event_type (EventType): The type of the event.
        block_height (int): The height of the block in which the event occurred.
        block_index (int): The index of the event within the block.
        timestamp (int): The timestamp of the event.
        inscription_id (str): The inscription ID associated with the event.
        inscription_number (int): The inscription number associated with the event.
        sender (str): The sender of the event.
        receiver (str): The receiver of the event.
        content (dict): The content of the event.
        operation (str, optional): The operation associated with the event. Defaults to "".
        function_id (int, optional): The function ID associated with the event. Defaults to 0.
        valid (bool, optional): Indicates if the event is valid. Defaults to True.
        error (str, optional): The error message associated with the event. Defaults to "".
    """

    def __init__(
        self,
        id: str,
        event_type: str,
        block_height: int,
        block_index: int,
        timestamp: int,
        inscription_id: str,
        inscription_number: int,
        sender: str,
        receiver: str,
        content: dict,
        operation: str = "",
        function_id: int = 0,
        valid: bool = True,
        error: str = "",
        handled: bool = False,
    ) -> None:
        self.id = id
        self.event_type = EventType[event_type]
        self.block_height = block_height
        self.block_index = block_index
        self.timestamp = timestamp
        self.inscription_id = inscription_id
        self.inscription_number = inscription_number
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.operation = operation
        self.function_id = function_id
        self.valid = valid
        self.error = error
        self.handled = handled

    @property
    def __dict__(self):
        """
        Returns the event as a dictionary.

        Returns:
            dict: The event represented as a dictionary.
        """
        return {
            "id": self.id,
            "event_type": self.event_type.name,
            "block_height": self.block_height,
            "block_index": self.block_index,
            "timestamp": self.timestamp,
            "inscription_id": self.inscription_id,
            "inscription_number": self.inscription_number,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "operation": self.operation,
            "function_id": self.function_id,
            "valid": self.valid,
            "error": self.error,
            "handled": self.handled
        }
