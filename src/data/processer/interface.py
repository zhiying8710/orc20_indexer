import os
import sys
from typing import Union, Tuple
from abc import ABC, abstractmethod

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, Token, Balance, Pending_Inscriptions, OTC, OTC_Record


from abc import ABC, abstractmethod
from typing import Union, List


class Interface(ABC):
    """
    This is the interface for data processing.

    All methods defined in this interface should be implemented by the concrete class.
    """

    @abstractmethod
    async def save_event(self, event: Event):
        """
        Save an event.

        Args:
            event (Event): The event to be saved.
        """
        pass

    @abstractmethod
    async def save_pending_inscription(self, pending_inscription: Pending_Inscriptions):
        """
        Save a pending inscription.

        Args:
            pending_inscription (Pending_Inscriptions): The pending inscription to be saved.
        """
        pass

    @abstractmethod
    async def save_token(self, token: Token):
        """
        Save a token.

        Args:
            token (Token): The token to be saved.
        """
        pass

    @abstractmethod
    async def save_balance(self, balance: Balance):
        """
        Save a balance.

        Args:
            balance (Balance): The balance to be saved.
        """
        pass

    @abstractmethod
    async def batch_save_balances(self, balances: List[Balance]):
        """
        Save multiple balances.

        Args:
            balances (List[Balance]): The list of balances to be saved.
        """
        pass

    @abstractmethod
    async def save_otc(self, otc: OTC):
        """
        Save an OTC (Over-The-Counter) trade.

        Args:
            otc (OTC): The OTC trade to be saved.
        """
        pass

    @abstractmethod
    async def save_otc_record(self, otc_record: OTC_Record):
        """
        Save an OTC trade record.

        Args:
            otc_record (OTC_Record): The OTC trade record to be saved.
        """
        pass

    @abstractmethod
    async def get_pending_inscription(
        self, user: str
    ) -> Union[Pending_Inscriptions, None]:
        """
        Get a pending inscription by user.

        Args:
            user (str): The user associated with the pending inscription.

        Returns:
            Union[Pending_Inscriptions, None]: The pending inscription if found, None otherwise.
        """
        return None

    @abstractmethod
    async def get_token(self, token_id: int) -> Union[Token, None]:
        """
        Get a token by token ID.

        Args:
            token_id (int): The ID of the token.

        Returns:
            Union[Token, None]: The token if found, None otherwise.
        """
        return None

    @abstractmethod
    async def get_balance(self, address: str, token_id: int) -> Balance:
        """
        Get a balance by address and token ID.

        Args:
            address (str): The address associated with the balance.
            token_id (int): The ID of the token.

        Returns:
            Balance: The balance if found, None otherwise.
        """
        return None

    @abstractmethod
    async def get_otc(self, otc_id: int) -> Union[OTC, None]:
        """
        Get an OTC trade by ID.

        Args:
            otc_id (int): The ID of the OTC trade.

        Returns:
            Union[OTC, None]: The OTC trade if found, None otherwise.
        """
        return None

    @abstractmethod
    async def get_otc_records(self, oid: int) -> Union[List[OTC_Record], None]:
        """
        Get OTC trade records by OTC ID.

        Args:
            oid (int): The ID of the OTC trade.

        Returns:
            Union[List[OTC_Record], None]: The list of OTC trade records if found, None otherwise.
        """
        return None

    @abstractmethod
    async def delete_event_by_block(self, block_height):
        return None

    @abstractmethod
    async def get_min_unhandled_block_height(self):
        return None

    @abstractmethod
    async def restore_all_table(self):
        return None

    @abstractmethod
    async def get_backup_block_height(self):
        return None

    @abstractmethod
    def mark_block_events_as_unhandled(self, block_height):
        pass


