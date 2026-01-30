import logging
import os
import sys

# Create package-level logger
logger = logging.getLogger("lightcurve")
logger.addHandler(logging.NullHandler())  # Default to no output to respect lib isolation

def configure_logging(level=None):
    """
    Helper to configure Lightcurve logging for applications.
    
    Args:
        level: Logging level (e.g. logging.INFO). Defaults to LIGHTCURVE_LOG_LEVEL env var or INFO.
    """
    if level is None:
        env_level = os.getenv("LIGHTCURVE_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)
    
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [lightcurve] %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False  # Don't propagate to root logger by default if we configured it
    
    logger.info(f"Logging initialized at level {logging.getLevelName(level)}")
