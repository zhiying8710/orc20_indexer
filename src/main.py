import os
import sys
import copy
from loguru import logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import register
from src.storage import registered_handlers
from src.structure import Event
from src.data.processer.interface import Interface as DataProcesser


async def handle_event(
    event: Event, data_processer: DataProcesser, is_pending: bool = False
):
    """
    Handle an event.

    Args:
        event (Event): The event to be handled.
        data_processer (DataProcesser): The data processer object.
        is_pending (bool, optional): Indicates if the event is pending in mempool. Defaults to False.
    """
    event.valid = True
    event.error = ""
    event.handled = True

    content = event.content

    for key in content.keys():
        if key not in ["p", "op", "params"]:
            event.valid = False
            event.error = f"unknown key in instruction"
            await data_processer.save_event(event)
            return

    if content.get("p", "").lower() != "orc-20":
        event.valid = False
        event.error = f"invaild p"
        await data_processer.save_event(event)
        return

    op = content.get("op", "").lower()
    if op == "" or op not in registered_handlers.keys():
        event.valid = False
        event.error = f"invalid op"
        await data_processer.save_event(event)
        return

    params = content.get("params", {})
    if not params:
        event.valid = False
        event.error = f"invalid params"
        await data_processer.save_event(event)
        return

    event.operation = op

    if is_pending is False:
        copied_content = copy.deepcopy(content)
        event = await registered_handlers[op](event, data_processer)
        event.content = copied_content

    await data_processer.save_event(event)
    logger.info(
        f"handle{' pending ' if is_pending is True else ' '}event: {event.event_type}, {event.content}"
    )
