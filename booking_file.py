"""booking_file.py - the Bookings.txt / Help.txt handling that lived inside Unit1.pas.

Each booking is one line:  username,table,date,timeslots
"""
from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKINGS_FILE = os.path.join(BASE_DIR, "Bookings.txt")
HELP_FILE = os.path.join(BASE_DIR, "Help.txt")

# Delphi's DateToStr uses the Windows short-date format. South Africa's default is
# yyyy/MM/dd. Change this if your existing Bookings.txt uses another style
# (for example "%d/%m/%Y"); filtering by date compares these strings.
DATE_FORMAT = "%Y/%m/%d"


def format_date(d: dt.date) -> str:
    return d.strftime(DATE_FORMAT)


def time_to_str(t: dt.time) -> str:
    """Delphi TimeToStr with a 24-hour system clock, e.g. 17:02:00."""
    return t.strftime("%H:%M:%S")


@dataclass
class BookingLine:
    username: str
    table: str
    date: str
    timeslots: str

    def as_row(self) -> str:
        return f"{self.username}\t{self.table}\t{self.date}\t{self.timeslots}"


def append_booking(username: str, table_no: int, book_date: dt.date,
                   timeslots: str, path: str = BOOKINGS_FILE) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{username},{table_no},{format_date(book_date)},{timeslots}\n")


def read_bookings(path: str = BOOKINGS_FILE) -> list[BookingLine] | None:
    """All bookings in the file, or None when the file does not exist."""
    if not os.path.exists(path):
        return None
    lines: list[BookingLine] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            raw = raw.rstrip("\r\n")
            if not raw.strip():
                continue
            parts = raw.split(",", 3)
            if len(parts) < 4:
                continue  # malformed line
            lines.append(BookingLine(*parts))
    return lines


def read_help(path: str = HELP_FILE) -> list[str] | None:
    """Lines of Help.txt, or None when the file does not exist."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\r\n") for line in f]
