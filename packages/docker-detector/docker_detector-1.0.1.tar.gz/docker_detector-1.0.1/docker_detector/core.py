from functools import lru_cache
from pathlib import Path
import sys


@lru_cache(maxsize=1)
def _is_docker_cached() -> bool:
    """
    Internal cached implementation of Docker detection.
    """
    if not sys.platform.startswith("linux"):
        return False

    # Check for Docker environment file
    if Path("/.dockerenv").exists():
        return True

    # Check cgroup for docker
    try:
        if "docker" in Path("/proc/self/cgroup").read_text():
            return True
    except OSError:
        pass

    # Check mountinfo for Docker container paths
    try:
        if "/docker/containers/" in Path("/proc/self/mountinfo").read_text():
            return True
    except OSError:
        pass

    return False


def is_docker(force_refresh: bool = False) -> bool:
    """
    Return True if the current process is running inside Docker.
    
    Linux-only detection. Returns False on macOS and Windows.
    
    Args:
        force_refresh: If True, bypass the cache and perform a fresh check.
                       Defaults to False.
    
    Returns:
        True if running inside Docker, False otherwise.
    
    Examples:
        >>> is_docker()  # Uses cache
        False
        >>> is_docker(force_refresh=True)  # Bypasses cache
        False
    """
    if force_refresh:
        _is_docker_cached.cache_clear()
    return _is_docker_cached()
