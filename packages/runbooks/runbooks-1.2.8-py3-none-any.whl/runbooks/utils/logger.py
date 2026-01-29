import logging
import os
import tempfile


## ==============================
## CONFIGURE LOGGING
## ==============================
def configure_logger(module_name: str) -> logging.Logger:
    """
    Configures and returns a logger for a given module.

    Args:
        module_name (str): The name of the module using the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    ## Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    ## Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    ## File Handler - Fix: Use user directory instead of root
    log_dir = os.path.expanduser("~/.runbooks/logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{module_name.replace('.', '_')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    ## Add handlers if not already added
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
