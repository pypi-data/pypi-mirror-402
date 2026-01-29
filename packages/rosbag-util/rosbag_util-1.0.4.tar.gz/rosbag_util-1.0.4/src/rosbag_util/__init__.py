"""rosbag-util package."""

from .extract import main as extract
from .undistort_images import main as undistort_images

__all__ = ["__version__", "extract", "undistort_images"]

try:
    from ._version import __version__
except Exception:
    __version__ = "0.0.0"
