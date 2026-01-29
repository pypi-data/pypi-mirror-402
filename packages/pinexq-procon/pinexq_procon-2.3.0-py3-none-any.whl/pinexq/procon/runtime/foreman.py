import asyncio
import platform
import signal
from asyncio import AbstractEventLoop, Future, Event, CancelledError

from ..runtime.worker import ProConWorker, log


class ProConForeman:
    """
    Helper class to set up the asyncio context for a Worker, start it,
    handle signals and exceptions.
    """

    worker: ProConWorker
    _worker_task: asyncio.Task
    loop: AbstractEventLoop
    is_shutting_down: Event

    # This code takes many hints and tips from:
    #  https://www.roguelynn.com/words/asyncio-we-did-it-wrong/

    def __init__(self, worker: ProConWorker, *, debug: bool = True):
        self.worker = worker
        self.is_shutting_down = Event()

        self.loop = asyncio.new_event_loop()
        self.loop.set_debug(debug)
        self.loop.set_exception_handler(self._handle_loop_exception)
        self.install_signal_handlers()
        self.start()

    # noinspection PyUnresolvedReferences
    def install_signal_handlers(self):
        # Windows does not support signals, so skip it there
        if platform.system() != 'Windows':
            log.info("Installing signal handlers")
            signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
            for s in signals:
                self.loop.add_signal_handler(
                    # Bind the variable `s` to avoid late binding.
                    # This is working even though the linter might tell otherwise.
                    s, lambda s=s: self._shutdown_on_signal(s)
                )

    def start(self):
        """Starts the worker and will block as long as the event loop runs."""
        log.info("Starting worker runtime")
        try:
            self.loop.run_until_complete(
                self.worker.run(),
            )
            log.debug("Worker task exited.")
        except KeyboardInterrupt:
            log.warning("Process received keyboard interrupt!")
        except Exception as exc:
            log.exception(f"Shutdown triggered by unhandled {exc.__class__.__name__} exception!")
        finally:
            if not self.is_shutting_down.is_set():
                self.loop.run_until_complete(
                    self.shutdown(wait_on_worker=False)
                )
            self.loop.close()
            log.info("Successfully shutdown worker runtime")

    def _shutdown_on_signal(self, sig: signal.Signals | None = None):
        """Handle system signals like SIGINT, SIGTERM"""
        if sig:
            log.warning(f"Received exit signal {sig.name}...")

        if not self.is_shutting_down.is_set():
            asyncio.create_task(
                self.shutdown(wait_on_worker=True), name="shutdown_on_signal"
            )

    def _shutdown_on_exception(self, exc: Exception | None):
        """Handle exceptions that are not explicitly handled in the framework  and bubble up to the 'foreman'."""
        if exc:
            log.warning(f"Shutting triggered by unhandled {exc.__class__.__name__} exception!")

        if not self.is_shutting_down.is_set():
            asyncio.create_task(
                self.shutdown(wait_on_worker=False), name="shutdown_on_exception"
            )

    async def shutdown(self, wait_on_worker: bool = False):
        """Cleanup running tasks and shutdown the async event loop.

        Args:
            wait_on_worker: If true, wait for the Worker task to finish its calculations.
        """
        if self.is_shutting_down.is_set():
            log.warning("Shutdown triggered while already shutting down!")
            return
        self.is_shutting_down.set()

        log.info("Shutting down...")

        # Signal the Worker to stop and wait for it to exit
        await self.worker.stop()
        if wait_on_worker:
            log.debug("Waiting for the Worker task to finish ...")
            await self._worker_task

        # Cleanup all dangling task
        tasks = [t for t in asyncio.all_tasks()
                 if t is not asyncio.current_task()]
        if tasks:
            log.warning(f"Cancelling {len(tasks)} outstanding tasks")
            log.debug(f"Tasks to be cancelled: {[t.get_name() for t in tasks]}")
            for task in tasks:
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        log.info("Stopping event loop")
        self.loop.stop()

    def _handle_loop_exception(self, loop: AbstractEventLoop, context: dict):
        """Global exception handler for event loop."""
        # context["message"] will always be there; but context variables may not
        task: asyncio.Task | None = context.get("task", None)
        task_name = f"[Task-name: {task.get_name()}]" if task else ""
        exception: Exception | None = context.get("exception", None)
        log.exception(f"Caught exception: {context['message']} {task_name}", exc_info=exception)

        # Most exceptions in the loop happen during shutdown. If that's not the case,
        #  be on the safe side and shut everything down.
        self._shutdown_on_exception(exception)
