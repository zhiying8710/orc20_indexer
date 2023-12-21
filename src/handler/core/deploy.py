import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.structure import Event, EventType
from src.indexer.core import deploy as deploy_indexer
from src.data.processer.interface import Interface as DataProcesser
from src.handler.utils.utils import error_event


async def handle_deploy(event: Event, data_processer: DataProcesser) -> Event:
    """
    Handle the deploy event.

    Args:
        event (Event): The deploy event to be handled.
        data_processer (DataProcesser): The data processer object.

    Returns:
        Event: The updated event object.

    Raises:
        ValueError: If the event type is not EventType.INSCRIBE.
    """
    if event.event_type != EventType.INSCRIBE:
        return error_event(event, "deploy event don't care about transfer")

    event.function_id = event.inscription_number

    params, error = deploy_indexer.parse_params(event)
    if params is None:
        return error_event(event, f"invalid inscription, {error}")

    token = deploy_indexer.process_deploy(event, params)

    await data_processer.save_token(token)

    return event
