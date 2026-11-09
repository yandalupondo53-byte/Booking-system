"""dm_shop.py - the data module (port of dmShop_U.pas).

Every database call lives here. The original used ADO + the Jet 4.0 OLE DB
provider; Python talks to the same .mdb file through pyodbc and the Microsoft
Access ODBC driver (Windows).
"""
from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(APP_DIR, "dbChateauDeYanda.mdb")
ACCESS_DRIVER = "Microsoft Access Driver (*.mdb, *.accdb)"

ROLE_ADMIN = "A"
ROLE_USER = "U"


@dataclass
class Person:
    """One row of tblPersonal."""
    username: str
    password: str
    first_name: str
    surname: str
    role: str
    email: str


PERSON_COLUMNS = ("Username", "Password", "FirstName", "Surname", "Role", "Email")
BOOKING_COLUMNS = ("Username", "TableNo", "BookDate", "Timeslots", "Arrival")

_PERSON_SELECT = "SELECT Username, [Password], FirstName, Surname, Role, Email FROM tblPersonal"


def _text(value) -> str:
    return "" if value is None else str(value)


def _person(row) -> Person:
    return Person(*(_text(v) for v in row))


class DmShop:
    """Wraps a DB-API connection (pyodbc in production, sqlite3 in tests)."""

    def __init__(self, conn):
        self.conn = conn

    @classmethod
    def open_access(cls, path: str = DEFAULT_DB) -> "DmShop":
        import pyodbc  # imported here so the rest of the app doesn't need it

        if not os.path.exists(path):
            raise FileNotFoundError(f"Database not found: {path}")
        conn = pyodbc.connect(f"DRIVER={{{ACCESS_DRIVER}}};DBQ={path};", autocommit=True)
        return cls(conn)

    def close(self) -> None:
        self.conn.close()

    # -- helpers ---------------------------------------------------------
    def _query(self, sql: str, params=()):
        cur = self.conn.cursor()
        try:
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close()

    def _execute(self, sql: str, params=()) -> None:
        cur = self.conn.cursor()
        try:
            cur.execute(sql, params)
            self.conn.commit()
        finally:
            cur.close()

    # -- tblPersonal -----------------------------------------------------
    def all_people(self) -> list[tuple]:
        return [tuple(_text(v) for v in r) for r in self._query(_PERSON_SELECT)]

    def find_login(self, username: str, password: str, role: str | None = None) -> Person | None:
        """First person whose username and password match exactly (case-sensitive),
        optionally restricted to a role. Mirrors the Delphi table-scan loops."""
        for row in self._query(_PERSON_SELECT):
            p = _person(row)
            if p.username == username and p.password == password and (role is None or p.role == role):
                return p
        return None

    def name_exists(self, first_name: str, surname: str) -> bool:
        """Registration's 'User already exists' test (matches on first name + surname)."""
        return any(
            _text(r[0]) == first_name and _text(r[1]) == surname
            for r in self._query("SELECT FirstName, Surname FROM tblPersonal")
        )

    def add_user(self, username: str, password: str, first_name: str, surname: str, email: str) -> None:
        self._execute(
            "INSERT INTO tblPersonal (Username, [Password], FirstName, Surname, Role, Email) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, password, first_name, surname, ROLE_USER, email),
        )

    def update_user(self, old_username: str, new_username: str, password: str, email: str) -> None:
        self._execute(
            "UPDATE tblPersonal SET Username = ?, [Password] = ?, Email = ? WHERE Username = ?",
            (new_username, password, email, old_username),
        )

    # -- tblBookings -----------------------------------------------------
    def all_bookings(self) -> list[tuple]:
        rows = self._query("SELECT Username, TableNo, BookDate, Timeslots, Arrival FROM tblBookings")
        return [tuple("" if v is None else v for v in r) for r in rows]

    def booking_exists(self, table_no: int, date: dt.date, timeslot: str) -> bool:
        """Same table, same date, exactly the same time-slot text (as the original)."""
        for row in self._query("SELECT TableNo, BookDate, Timeslots FROM tblBookings"):
            if int(row[0]) == table_no and _as_date(row[1]) == date and _text(row[2]) == timeslot:
                return True
        return False

    def add_booking(self, username: str, table_no: int, date: dt.date, timeslot: str) -> None:
        self._execute(
            "INSERT INTO tblBookings (Username, TableNo, BookDate, Timeslots) VALUES (?, ?, ?, ?)",
            (username, table_no, dt.datetime.combine(date, dt.time.min), timeslot),
        )


def _as_date(value) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and value:
        return dt.date.fromisoformat(value[:10])
    return None
