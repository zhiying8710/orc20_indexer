import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.structure.event import Event
from src.data.processer.interface import Interface as DataProcesser
from src.storage import register_handler


from src.handler.core.deploy import handle_deploy
from src.handler.core.upgrade import handle_upgrade
from src.handler.core.mint import handle_mint
from src.handler.core.burn import handle_burn
from src.handler.core.transfer import handle_transfer


from src.handler.otc.create import handle_create as handle_otc_create
from src.handler.otc.buy import handle_buy as handle_otc_buy
from src.handler.otc.execute import handle_execute as handle_otc_execute


@register_handler("deploy")
async def deploy(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the 'deploy' event.

    Args:
        event (Event): The event object.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    return await handle_deploy(event, data_processer)


@register_handler("upgrade")
async def upgrade(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the 'upgrade' event.

    Args:
        event (Event): The event object.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    return await handle_upgrade(event, data_processer)


@register_handler("mint")
async def mint(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the 'mint' event.

    Args:
        event (Event): The event object.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    return await handle_mint(event, data_processer)


@register_handler("burn")
async def burn(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the 'burn' event.

    Args:
        event (Event): The event object.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    return await handle_burn(event, data_processer)


@register_handler("transfer")
async def transfer(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the 'transfer' event.

    Args:
        event (Event): The event object.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    return await handle_transfer(event, data_processer)


@register_handler("otc-create")
async def otc_create(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the 'otc-create' event.

    Args:
        event (Event): The event object.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    return await handle_otc_create(event, data_processer)


@register_handler("otc-buy")
async def otc_buy(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the 'otc-buy' event.

    Args:
        event (Event): The event object.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    return await handle_otc_buy(event, data_processer)


@register_handler("otc-execute")
async def otc_execute(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the 'otc-execute' event.

    Args:
        event (Event): The event object.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.
    """
    return await handle_otc_execute(event, data_processer)
