"""Logging configuration module"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from queue import Queue


def setup_logger(name='medical_qa', log_level=logging.INFO):
    """
    Setup logger with file and console handlers.
    Uses QueueListener to ensure console output works from all threads.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if logger.handlers:
        return logger

    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Error file handler
    error_file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)

    # Console handler — via QueueListener so all threads feed one writer thread
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Queue: handlers write to queue, listener thread drains to console
    log_queue = Queue(-1)
    queue_handler = QueueHandler(log_queue)
    listener = QueueListener(log_queue, console_handler)
    listener.start()

    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(queue_handler)

    return logger


logger = setup_logger()
