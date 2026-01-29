import asyncio
import logging

log = logging.getLogger(__name__)

def handle_task_result(task: asyncio.Task, description: str = "", msg_on_success: bool = False):
    description = description or task.get_name()  # use the raw task name if no human-readable text was given
    try:
        # Calling .result() on a finished task raises the exception if one occurred
        task.result()
        if msg_on_success:
            log.debug(f"{description} finished successfully")
    except asyncio.CancelledError:
        log.debug(f"{description} was cancelled")
    except Exception as e:
        log.exception(f"{description} raised an exception: {e}")