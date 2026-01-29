import logging

# Mapping from message type to the kernel channel it should be sent on
MSG_TYPE_TO_SHELL = {
    # Shell Channel Targets
    'execute_request': True,
    'inspect_request': True,
    'complete_request': True,
    'history_request': True,
    'is_complete_request': True,
    'comm_info_request': True,
    'kernel_info_request': True,
    'shutdown_request': True,
    'interrupt_request': True,
    'comm_open': True,
    'comm_msg': True,
    'comm_close': True,
    # Stdin Channel Targets
    'input_reply': False,
}


def setup_logging(level: int = logging.INFO) -> None:
    """Configures basic logging for the application."""
    log_format = (
        '%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s] - %(message)s'
    )
    logging.basicConfig(level=level, format=log_format)
    if level > logging.DEBUG:
        logging.getLogger('jupyter_client').setLevel(logging.WARNING)
        logging.getLogger('traitlets').setLevel(logging.WARNING)
        try:
            import zmq

            logging.getLogger('zmq').setLevel(logging.WARNING)
        except ImportError:
            pass


def get_logger(name: str) -> logging.Logger:
    """Gets a logger instance."""
    return logging.getLogger(name)
