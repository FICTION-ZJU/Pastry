import logging
import os
import time


def setup_logger(file_name, cmd_loglevel, file_loglevel):
    logger = logging.getLogger("pastry")
    logger.setLevel(min(cmd_loglevel, file_loglevel))

    # Clear existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Fixed log output path: outputs/logs/pastry_<timestamp>.log
    log_dir = os.path.join("outputs", "logs")
    os.makedirs(log_dir, exist_ok=True)
    logfile = os.path.join(log_dir, f"{int(time.time())}_{filename}.log")

    # create file handler
    fh = logging.FileHandler(logfile)
    fh.setLevel(file_loglevel)

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(cmd_loglevel)

    # create formatter and add it to the handlers
    fileformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    consoleformatter = logging.Formatter('%(name)s: %(message)s')

    ch.setFormatter(consoleformatter)
    fh.setFormatter(fileformatter)
    
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
