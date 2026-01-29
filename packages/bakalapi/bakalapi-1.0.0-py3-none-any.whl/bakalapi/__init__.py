"""
Bakalapi - A Python library for accessing the Bakalapi timetable API.

This library provides a simple interface to query timetable information
by teacher, room, or class.
"""

from .client import BakalapiClient, BakalapiError, BakalapiAPIError
from .models import Hour, TimetableEntry, TimetableResponse

__version__ = "1.0.0"
__all__ = [
    "BakalapiClient",
    "BakalapiError",
    "BakalapiAPIError",
    "Hour",
    "TimetableEntry",
    "TimetableResponse",
]
