"""rosbag-util package."""

__all__ = ["__version__"]

try:
    from ._version import __version__
except Exception:
    __version__ = "0.0.0"
