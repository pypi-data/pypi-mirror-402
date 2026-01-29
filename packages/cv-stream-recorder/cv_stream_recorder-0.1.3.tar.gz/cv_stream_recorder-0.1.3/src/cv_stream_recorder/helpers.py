import logging
import os
import signal
import subprocess
import time
import errno

from urllib.parse import urlparse
from .utils.logging_config import setup_logging


logger = logging.getLogger(__name__)
setup_logging()


def check_url(url: str) -> bool:
    """Return True if URL is valid, False otherwise."""
    logger.info(f"check_url: {url}")

    if not isinstance(url, str) or not url.strip():
        return False

    parsed = urlparse(url)

    # Scheme is required (http, https, rtsp, rtmp)
    if parsed.scheme not in ("http", "https", "rtmp", "rtsp", "udp", "tcp", "file"):
        logger.error(f"check_url: Invalid scheme: {parsed.scheme}")
        return False

    # With URL network: need netloc
    if parsed.scheme != "file" and not parsed.netloc:
        logger.error("check_url: Invalid netloc")
        return False

    # With file URL: need path
    if parsed.scheme == "file" and not parsed.path:
        logger.error("check_url: Invalid path")
        return False

    logger.info("check_url: URL is valid")
    return True


def check_folder_path(folder_path: str) -> bool:
    """Return True if folder path exists or can be created, and is writable."""
    logger.info(f"check_folder_path: {folder_path}")

    if not isinstance(folder_path, str) or not folder_path.strip():
        logger.error("check_folder_path: Invalid folder path")
        return False

    try:
        # Create if not exists
        os.makedirs(folder_path, exist_ok=True)

        # Check write permission
        test_file = os.path.join(folder_path, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")

        # Remove test file
        os.remove(test_file)

        logger.info("check_folder_path: Folder path is valid")
        return True

    except (OSError, FileNotFoundError) as e:
        logger.error(f"check_folder_path: Error checking folder path: {e}")
        return False


def stop_process(pid: int, timeout: float = 3.0) -> bool:
    """Terminate a process with the given PID using SIGINT via subprocess."""
    logger.info(f"stop_process: Terminating process {pid}")

    if not isinstance(pid, int) or pid <= 0:
        logger.error(f"stop_process: Invalid PID: {pid}")
        return False

    logger.info(f"stop_process: Sending SIGINT to process {pid}")

    try:
        os.kill(pid, signal.SIGINT)

    except OSError as e:
        if e.errno == errno.ESRCH:  # No such process
            logger.warning(f"stop_process: Process {pid} does not exist")
            return True
        elif e.errno == errno.EPERM:  # Permission denied
            logger.error(f"stop_process: No permission to kill process {pid}")
        else:
            logger.error(f"stop_process: Error sending SIGINT: {e}")
        return False

    # Wait for process to exit gracefully
    start = time.time()
    while time.time() - start < timeout:
        try:
            os.kill(pid, 0)  # check if alive
        except OSError as e:
            if e.errno == errno.ESRCH:
                logger.info(f"stop_process: Process {pid} exited gracefully")
                return True
            return False
        time.sleep(0.2)

    logger.warning(f"stop_process: Process {pid} did not exit within timeout")
    return False