"""
Data models for Bakalapi timetable responses.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Hour:
    """Represents a school hour with its time range."""
    number: int
    start_time: str
    end_time: str

    @classmethod
    def from_dict(cls, data: dict) -> "Hour":
        """Create a Hour instance from a dictionary."""
        return cls(
            number=data["number"],
            start_time=data["start_time"],
            end_time=data["end_time"]
        )


@dataclass
class TimetableEntry:
    """Represents a single timetable entry."""
    day: str
    date: str
    hour_number: int
    time: str
    subject: str
    teacher: str
    room: str
    class_name: str
    theme: Optional[str]
    notice: Optional[str]
    changeinfo: Optional[str]
    entry_type: str

    @classmethod
    def from_dict(cls, data: dict) -> "TimetableEntry":
        """Create a TimetableEntry instance from a dictionary."""
        return cls(
            day=data["day"],
            date=data["date"],
            hour_number=data["hour_number"],
            time=data["time"],
            subject=data["subject"],
            teacher=data["teacher"],
            room=data["room"],
            class_name=data["class"],
            theme=data.get("theme"),
            notice=data.get("notice"),
            changeinfo=data.get("changeinfo"),
            entry_type=data["entry_type"]
        )


@dataclass
class TimetableResponse:
    """Represents a complete timetable response."""
    hours: List[Hour]
    timetable: List[TimetableEntry]

    @classmethod
    def from_dict(cls, data: dict) -> "TimetableResponse":
        """Create a TimetableResponse instance from a dictionary."""
        return cls(
            hours=[Hour.from_dict(h) for h in data["hours"]],
            timetable=[TimetableEntry.from_dict(t) for t in data["timetable"]]
        )
