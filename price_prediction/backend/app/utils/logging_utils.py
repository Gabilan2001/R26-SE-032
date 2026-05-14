import logging


def configure_logger(name: str = __name__):
    """Configure a reusable logger for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    return logging.getLogger(name)
