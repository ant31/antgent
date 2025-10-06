import logging

from antgent.config import config

logger = logging.getLogger(__name__)


def get_workflow_queue() -> str:
    """
    Get the appropriate task queue for workflows.

    It finds the first worker with workflows defined in its configuration.
    If no worker has workflows, it falls back to the first worker's queue.
    """
    workers = config().workers
    for worker in workers:
        if worker.workflows:
            return worker.queue

    if not workers:
        raise ValueError("No temporal workers configured.")

    logger.warning("No worker with workflows configured. Falling back to first worker's queue.")
    return workers[0].queue
