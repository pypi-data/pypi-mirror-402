import logging
from logging import DEBUG, INFO, WARNING

from rich.logging import RichHandler


def configure_logging(debug: bool = False, rich: bool = False):
    # Define log-levels for external (and internal) packages we depend on
    if debug:
        log_levels = {
            "aiormq": INFO,
            "aio_pika": INFO,
            "procon": DEBUG,
        }
    else:
        log_levels = {
            "aiormq": WARNING,
            "aio_pika": WARNING,
            "procon": INFO,
        }

    config_options = {}
    if rich:
        import click, aiormq, aio_pika, asyncio
        # use rich for colored, more structured formatting
        handlers = [
            RichHandler(
                rich_tracebacks=True,
                # tracebacks_show_locals=True,
                #     log_time_format="%d-%m-%y %H:%M:%S.%f",
                #     omit_repeated_times=False,
                #     enable_link_path=False,
                #     show_path=False,
                #     show_level=False
                tracebacks_suppress=[click, aiormq, aio_pika, asyncio]
            )
        ]
        config_options["handlers"] = handlers
    else:
        # use plain formatting
        config_options["format"] = "%(asctime)s %(levelname)s %(message)s"
        config_options["datefmt"] = "%d-%m-%y %H:%M:%S"

    config_options["level"] = "INFO"
    logging.basicConfig(**config_options)

    for logger, level in log_levels.items():
        logging.getLogger(logger).setLevel(level)
