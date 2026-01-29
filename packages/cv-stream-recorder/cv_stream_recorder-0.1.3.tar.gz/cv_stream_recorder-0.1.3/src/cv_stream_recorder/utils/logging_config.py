import logging


def setup_logging():
    log_format = '[{asctime}] {name} [{levelname}] {message}'
    datefmt = '%Y-%m-%d %H:%M:%S %z'
    logging.basicConfig(format=log_format, datefmt=datefmt, style='{', level=logging.INFO)
