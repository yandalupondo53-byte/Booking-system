"""form1.py - the main window (port of Unit1.pas / Unit1.dfm).

The Delphi form was a TPageControl whose tab headers were hidden and switched in
code. Here every "tab" is a Page (a Canvas with a background picture) and
show() displays one at a time. Widget positions are taken from the .dfm.
"""
from __future__ import annotations

import datetime as dt
import os
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from dm_shop import (APP_DIR, BOOKING_COLUMNS, PERSON_COLUMNS, ROLE_ADMIN, DmShop, Person)

try:  # optional: gives a real calendar drop-down like TDateTimePicker
    from tkcalendar import DateEntry
except ImportError:  # pragma: no cover
    DateEntry = None

ASSETS = os.path.join(APP_DIR, "assets")
BOOKINGS_TXT = os.path.join(APP_DIR, "Bookings.txt")
HELP_TXT = os.path.join(APP_DIR, "Help.txt")

WIDTH, HEIGHT = 747, 673  # ClientWidth / ClientHeight of Form1
LABEL_FONT = ("Segoe UI", -23)  # negative size = pixels, same as Delphi's Font.Height
ENTRY_FONT = ("Segoe UI", -15)
LIGHT = "#f0f0f0"  # clMenuBar / clMenu
WHITE = "#ffffff"  # clWindow


def fmt_date(d: dt.date) -> str:
    """Delphi's DateToStr (short date, en-ZA style)."""
    return d.strftime("%Y/%m/%d")


def fmt_time(t: dt.time) -> str:
    """Delphi's TimeToStr (long time)."""
    return t.strftime("%H:%M:%S")


# ---------------------------------------------------------------- widgets
class DateField(ttk.Frame):
    """Stands in for a TDateTimePicker (date mode)."""

    def __init__(self, master, initial: dt.date | None = None, **kw):
        super().__init__(master)
        initial = initial or dt.date.today()
        if DateEntry is not None:
            self._inner = DateEntry(self, date_pattern="yyyy-mm-dd", font=ENTRY_FONT)
            self._inner.set_date(initial)
        else:
            self._inner = ttk.Entry(self, font=ENTRY_FONT)
            self._inner.insert(0, initial.isoformat())
        self._inner.pack(fill="both", expand=True)

    def get_date(self) -> dt.date:
        if DateEntry is not None:
            return self._inner.get_date()
        return dt.date.fromisoformat(self._inner.get().strip())  # expects YYYY-MM-DD


class TimeField(ttk.Frame):
    """Stands in for a TDateTimePicker (time mode, 'hh:mm')."""

    def __init__(self, master, initial: dt.time | None = None):
        super().__init__(master)
        initial = initial or dt.datetime.now().time()
        self._h = tk.StringVar(value=f"{initial.hour:02d}")
        self._m = tk.StringVar(value=f"{initial.minute:02d}")
        ttk.Spinbox(self, from_=0, to=23, width=3, wrap=True, format="%02.0f",
                    textvariable=self._h, font=ENTRY_FONT).pack(side="left")
        ttk.Label(self, text=":", font=ENTRY_FONT).pack(side="left")
        ttk.Spinbox(self, from_=0, to=59, width=3, wrap=True, format="%02.0f",
                    textvariable=self._m, font=ENTRY_FONT).pack(side="left")

    def get_time(self) -> dt.time:
        return dt.time(int(self._h.get()), int(self._m.get()))


class Images:
    """Loads pictures from assets/ and keeps them alive (Tk drops unreferenced images)."""

    def __init__(self):
        self._keep: list[ImageTk.PhotoImage] = []

    @staticmethod
    def exists(name: str) -> bool:
        return os.path.exists(os.path.join(ASSETS, name))

    def _load(self, name: str) -> Image.Image:
        return Image.open(os.path.join(ASSETS, name)).convert("RGBA")

    def _photo(self, img: Image.Image) -> ImageTk.PhotoImage:
        photo = ImageTk.PhotoImage(img)
        self._keep.append(photo)
        return photo

    def stretch(self, name: str, w: int, h: int) -> ImageTk.PhotoImage:  # Stretch = True
        return self._photo(self._load(name).resize((w, h), Image.LANCZOS))

    def fit(self, name: str, w: int, h: int):  # Proportional = True; returns (photo, dx, dy)
        img = self._load(name)
        scale = min(w / img.width, h / img.height)
        size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
        img = img.resize(size, Image.LANCZOS)
        return self._photo(img), (w - size[0]) // 2, (h - size[1]) // 2


class Page(tk.Canvas):
    """One tab sheet: a canvas with a stretched background and helpers to add controls."""

    def __init__(self, form: "Form1", background: bool = True):
        super().__init__(form.root, width=WIDTH, height=HEIGHT, highlightthickness=0, bd=0, bg="#222222")
        self.form = form
        self.on_show = None
        if background:
            self._bg = form.images.stretch("background.png", 813, HEIGHT)
            self.create_image(0, 0, image=self._bg, anchor="nw")

    def label(self, x, y, text, font=LABEL_FONT, fill=LIGHT):
        return self.create_text(x, y, text=text, font=font, fill=fill, anchor="nw")

    def picture(self, x, y, w, h, name, click=None, press=None, release=None):
        photo, dx, dy = self.form.images.fit(name, w, h)
        item = self.create_image(x + dx, y + dy, image=photo, anchor="nw")
        if click:
            self.tag_bind(item, "<Button-1>", lambda _e: click())
        if press:
            self.tag_bind(item, "<ButtonPress-1>", lambda _e: press())
        if release:
            self.tag_bind(item, "<ButtonRelease-1>", lambda _e: release())
        if click or press:
            self.tag_bind(item, "<Enter>", lambda _e: self.config(cursor="hand2"))
            self.tag_bind(item, "<Leave>", lambda _e: self.config(cursor=""))
        return item

    def put(self, widget, x, y, w, h):
        self.create_window(x, y, window=widget, anchor="nw", width=w, height=h)
        return widget

    def entry(self, x, y, w, h=23, password=False, disabled=False):
        e = tk.Entry(self, font=ENTRY_FONT, show="*" if password else "")
        self.put(e, x, y, w, h)
        if disabled:
            e.config(state="disabled")
        return e

    def button(self, x, y, w, h, text, command, font=None):
        b = tk.Button(self, text=text, command=command, wraplength=w - 10)
        if font:
            b.config(font=font)
        return self.put(b, x, y, w, h)

    def password_toggle(self, x, y, w, h, entry: tk.Entry):
        """Press-and-hold the eye icon to reveal the password (imgShowHide handlers)."""
        shown = "hide_password.png" if Images.exists("hide_password.png") else None
        hidden = "show_password.png" if Images.exists("show_password.png") else "show_hide.png"
        item = self.picture(x, y, w, h, hidden)

        def swap(name):
            if shown:  # only if the optional second icon is present
                photo, _dx, _dy = self.form.images.fit(name, w, h)
                self.itemconfig(item, image=photo)

        def reveal():
            entry.config(show="")
            swap(shown)

        def conceal():
            entry.config(show="*")
            swap(hidden)

        self.tag_bind(item, "<ButtonPress-1>", lambda _e: reveal())
        self.tag_bind(item, "<ButtonRelease-1>", lambda _e: conceal())


# ------------------------------------------------------------------- form
class Form1:
    def __init__(self, root: tk.Tk, dm: DmShop):
        self.root = root
        self.dm = dm
        self.images = Images()
        self.user: Person | None = None  # the person who is logged in
        self.pages: dict[str, Page] = {}

        root.title("Chateau de Yanda")
        root.geometry(f"{WIDTH}x{HEIGHT}")
        root.resizable(False, False)

        self._build_identification()
        self._build_admin()
        self._build_user()
        self._build_registration()
        self._build_databases()
        self._build_admin_tab()
        self._build_booking_tab()
        self._build_profile_tab()
        self._build_edit_tab()

        self.show("Identification")  # FormCreate

    # -- navigation (replaces the TabVisible juggling) -------------------
    def show(self, name: str) -> None:
        for page in self.pages.values():
            page.place_forget()
        page = self.pages[name]
        page.place(x=0, y=0)
        if page.on_show:
            page.on_show()

    def _add(self, name: str, background: bool = True) -> Page:
        page = Page(self, background)
        self.pages[name] = page
        return page

    # -- Identification --------------------------------------------------
    def _build_identification(self):
        p = self._add("Identification", background=False)
        p.picture(3, -104, 771, 753, "logo.png")
        p.picture(80, 536, 233, 73, "admin_button.png", click=lambda: self.show("Admin"))
        p.picture(432, 536, 233, 73, "user_button.png", click=lambda: self.show("User"))

    # -- Admin login -----------------------------------------------------
    def _build_admin(self):
        p = self._add("Admin")
        p.label(16, 198, "Administration ID/Username:")
        p.label(212, 248, "Password:")
        p.picture(32, 16, 73, 65, "back.png", click=lambda: self.show("Identification"))
        self.edt_admin_username = p.entry(327, 208, 291)
        self.edt_admin_password = p.entry(328, 258, 290, password=True)
        p.password_toggle(640, 258, 41, 31, self.edt_admin_password)
        p.picture(327, 344, 153, 57, "login_button.png", click=self.admin_login)

    def admin_login(self):
        person = self.dm.find_login(self.edt_admin_username.get(), self.edt_admin_password.get(), ROLE_ADMIN)
        if person:
            messagebox.showinfo("Chateau de Yanda", f"WELCOME!! {person.first_name} {person.surname}")
            self.show("AdminTab")
        else:
            messagebox.showinfo("Chateau de Yanda", "Username not Found")

    # -- User login ------------------------------------------------------
    def _build_user(self):
        p = self._add("User")
        p.label(200, 198, "Email:")
        p.label(160, 264, "Password:")
        p.picture(40, 24, 97, 73, "back.png", click=lambda: self.show("Identification"))
        p.label(40, 480, "Don't have an account?", font=("Segoe UI", -15))
        self.edt_username = p.entry(288, 198, 273)
        self.edt_user_password = p.entry(288, 264, 273, password=True)
        p.password_toggle(608, 264, 41, 31, self.edt_user_password)
        p.picture(288, 328, 129, 49, "login_button.png", click=self.user_login)
        p.button(224, 480, 75, 25, "Register", lambda: self.show("Registration"))

    def user_login(self):
        # Like the original (GetDetails) this matches username + password with no role check.
        person = self.dm.find_login(self.edt_username.get(), self.edt_user_password.get())
        if person:
            self.user = person
            self.pages["ProfileTab"].itemconfig(self.lbl_name, text=f"{person.first_name} {person.surname}")
            self.show("ProfileTab")
        else:
            messagebox.showinfo("Chateau de Yanda", "Username not Found")

    # -- Registration ----------------------------------------------------
    def _build_registration(self):
        p = self._add("Registration")
        p.label(161, 168, "Username:")
        p.label(203, 224, "Name:")
        p.label(174, 280, "Surname:")
        p.label(203, 327, "Email:")
        p.label(96, 364, "Create Password:")
        p.picture(48, 32, 65, 57, "back.png", click=lambda: self.show("Identification"))
        self.edt_register_username = p.entry(296, 178, 201)
        self.edt_name = p.entry(296, 234, 201)
        self.edt_surname = p.entry(296, 290, 201)
        self.edt_user_email = p.entry(296, 337, 201)
        self.edt_create_password = p.entry(296, 374, 201, password=True)
        p.password_toggle(528, 374, 41, 31, self.edt_create_password)
        p.picture(296, 440, 153, 57, "register_button.png", click=self.register)

    def register(self):
        username = self.edt_register_username.get()
        first, surname = self.edt_name.get(), self.edt_surname.get()
        email, password = self.edt_user_email.get(), self.edt_create_password.get()
        if not (username.strip() and first.strip() and surname.strip() and password):
            messagebox.showinfo("Chateau de Yanda", "Please fill in every field.")
            return
        if self.dm.name_exists(first, surname):  # original checks first name + surname
            messagebox.showinfo("Chateau de Yanda", "User already exists")
            return
        try:
            self.dm.add_user(username, password, first, surname, email)
        except Exception as exc:  # e.g. duplicate Username (primary key)
            messagebox.showerror("Chateau de Yanda", f"Could not register: {exc}")
            return
        messagebox.showinfo("Chateau de Yanda", "Registration successful. You can now log in.")
        self.show("User")

    # -- DataBases (the two DBGrids) -------------------------------------
    def _build_databases(self):
        p = self._add("DataBases")
        p.picture(32, 3, 97, 73, "back.png", click=lambda: self.show("AdminTab"))
        self.grid_personal = self._grid(p, 32, 72, 701, 289, PERSON_COLUMNS)
        self.grid_bookings = self._grid(p, 32, 384, 701, 249, BOOKING_COLUMNS)
        p.on_show = self.refresh_grids  # DataBasesEnter

    @staticmethod
    def _grid(page: Page, x, y, w, h, columns) -> ttk.Treeview:
        frame = ttk.Frame(page)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="w")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        page.put(frame, x, y, w, h)
        return tree

    def refresh_grids(self):
        for tree, rows in ((self.grid_personal, self.dm.all_people()), (self.grid_bookings, self._booking_rows())):
            tree.delete(*tree.get_children())
            for row in rows:
                tree.insert("", "end", values=row)

    def _booking_rows(self):
        rows = []
        for u, table, date, slot, arrival in self.dm.all_bookings():
            shown = date.strftime("%Y/%m/%d") if isinstance(date, (dt.date, dt.datetime)) else date
            rows.append((u, table, shown, slot, arrival))
        return rows

    # -- AdminTab --------------------------------------------------------
    def _build_admin_tab(self):
        p = self._add("AdminTab")
        p.button(32, 49, 225, 57, "Display the bookings made on this date: ", self.display_specific_bookings)
        self.dtp_date_locator = p.put(DateField(p), 32, 120, 225, 33)
        p.button(32, 240, 225, 65, "Display All Bookings", self.display_all_bookings)
        p.button(32, 360, 225, 73, "View Databases", lambda: self.show("DataBases"))
        p.button(32, 600, 225, 28, "Log out", self.logout)  # added: the original had no way back
        text = tk.Text(p, font=("Segoe UI", -12), state="disabled", wrap="none",
                       tabs=("170", "230", "330"))
        self.red_display = p.put(text, 312, 11, 441, 617)
        p.on_show = self._clear_display  # pgclMainEnter

    def logout(self):
        self.user = None
        self.show("Identification")

    def _clear_display(self):
        self.red_display.config(state="normal")
        self.red_display.delete("1.0", "end")
        self.red_display.config(state="disabled")

    def _display(self, lines):
        self.red_display.config(state="normal")
        self.red_display.delete("1.0", "end")
        self.red_display.insert("end", "\n".join(lines) + "\n")
        self.red_display.config(state="disabled")

    HEADER = ["Username\tTable\tDate\t\tTimeslots", "=" * 52]

    @staticmethod
    def _read_bookings():
        """Bookings.txt lines as (username, table, date, timeslots), or None if missing."""
        if not os.path.exists(BOOKINGS_TXT):
            return None
        rows = []
        with open(BOOKINGS_TXT, encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if line:
                    parts = line.split(",", 3)
                    rows.append(tuple(parts) + ("",) * (4 - len(parts)))
        return rows

    def display_all_bookings(self):
        self._display(self.HEADER)
        rows = self._read_bookings()
        if rows is None:
            messagebox.showinfo("Chateau de Yanda", "File not Found")
            return
        self._display(self.HEADER + ["\t".join(r) for r in rows])

    def display_specific_bookings(self):
        try:
            chosen = self.dtp_date_locator.get_date()
        except ValueError:
            messagebox.showinfo("Chateau de Yanda", "Please enter the date as YYYY-MM-DD.")
            return
        rows = self._read_bookings()
        if rows is None:
            messagebox.showinfo("Chateau de Yanda", "File not Found")
            return
        # The Delphi loop only ever kept the last line of the file, so it missed most bookings;
        # this shows every booking made on the chosen date, which is what it was meant to do.
        matches = [r for r in rows if r[2] == fmt_date(chosen)]
        if matches:
            self._display(self.HEADER + ["\t".join(r) for r in matches])
        else:
            messagebox.showinfo("Chateau de Yanda", "No user booked on " + fmt_date(chosen))

    # -- BookingTab ------------------------------------------------------
    def _build_booking_tab(self):
        p = self._add("BookingTab")
        p.label(35, 187, "TableNo. :", fill=WHITE)
        p.label(24, 262, "Date:", fill=WHITE)
        p.label(24, 358, "TimeSlots :", fill=WHITE)
        p.label(352, 358, "Until :", fill=WHITE)
        p.picture(56, 40, 97, 73, "back.png", click=lambda: self.show("ProfileTab"))
        p.picture(656, 65, 49, 48, "help.jpg", click=self.show_help)
        self.spn_table = p.put(ttk.Spinbox(p, from_=1, to=20, font=ENTRY_FONT), 140, 187, 137, 24)
        self.spn_table.set(1)
        self.dtp_booking_date = p.put(DateField(p), 140, 262, 197, 31)
        self.dtp_arrival = p.put(TimeField(p), 140, 359, 197, 31)
        self.dtp_leaving = p.put(TimeField(p), 444, 358, 197, 31)
        p.button(64, 488, 169, 65, "Book Table", self.book_table, font=("Segoe UI", -20))
        self.mem_help = p.put(tk.Text(p, font=("Segoe UI", -12), wrap="word"), 296, 136, 441, 101)

    def show_help(self):
        self.mem_help.delete("1.0", "end")
        if not os.path.exists(HELP_TXT):
            messagebox.showinfo("Chateau de Yanda", "File not Found")
            return
        with open(HELP_TXT, encoding="utf-8") as fh:
            self.mem_help.insert("end", fh.read())

    def book_table(self):
        try:
            table = int(self.spn_table.get())
            day = self.dtp_booking_date.get_date()
            arrive, leave = self.dtp_arrival.get_time(), self.dtp_leaving.get_time()
        except ValueError:
            messagebox.showinfo("Chateau de Yanda", "Please check the table number, date and times.")
            return
        if not 1 <= table <= 20:
            messagebox.showinfo("Chateau de Yanda", "Table number must be between 1 and 20.")
            return
        if leave <= arrive:  # added check
            messagebox.showinfo("Chateau de Yanda", "The leaving time must be after the arrival time.")
            return
        slot = f"{fmt_time(arrive)} - {fmt_time(leave)}"
        if self.dm.booking_exists(table, day, slot):
            messagebox.showinfo("Chateau de Yanda",
                                "Our apologies, but this table is already booked for " + fmt_date(day))
            return
        self.dm.add_booking(self.user.username, table, day, slot)
        # Keep a plain-text copy: the admin screens read their lists from Bookings.txt.
        # (The Delphi code also wrote a line when the table was already taken; that was a bug.)
        with open(BOOKINGS_TXT, "a", encoding="utf-8") as fh:
            fh.write(f"{self.user.username},{table},{fmt_date(day)},{slot}\n")
        messagebox.showinfo("Chateau de Yanda",
                            "Thank you for booking with ChateauDeYanda.Your Booking was successful!!")

    # -- ProfileTab ------------------------------------------------------
    def _build_profile_tab(self):
        p = self._add("ProfileTab")
        p.picture(280, 94, 225, 179, "profile.png")
        script = ("Segoe Script", -37, "italic")
        p.label(128, 342, "Welcome,", font=script, fill=WHITE)
        self.lbl_name = p.label(319, 342, "", font=script, fill=WHITE)
        p.button(280, 480, 193, 73, "Book Table", lambda: self.show("BookingTab"),
                 font=("Segoe UI Semibold", -23, "bold italic"))
        p.button(492, 94, 129, 25, "Edit Info", self.open_edit)

    # -- EditTab ---------------------------------------------------------
    def _build_edit_tab(self):
        p = self._add("EditTab")
        p.label(169, 64, "Username:")
        p.label(169, 110, "Name:")
        p.label(182, 168, "Surname:")
        p.label(216, 224, "Email:")
        p.label(104, 286, "Create Password:")
        p.picture(40, 22, 97, 73, "back.png", click=lambda: self.show("ProfileTab"))
        self.edt_username_change = p.entry(304, 74, 201)
        self.edt_name_change = p.entry(304, 120, 201)
        self.edt_surname_change = p.entry(304, 168, 201)
        self.edt_email_change = p.entry(304, 224, 201)
        self.edt_password_change = p.entry(304, 286, 201)  # shown in plain text, as in the original
        p.button(304, 376, 97, 25, "Save", self.save_changes)

    def open_edit(self):
        u = self.user
        for entry, value in ((self.edt_password_change, u.password), (self.edt_username_change, u.username),
                             (self.edt_email_change, u.email), (self.edt_name_change, u.first_name),
                             (self.edt_surname_change, u.surname)):
            entry.config(state="normal")
            entry.delete(0, "end")
            entry.insert(0, value)
        for entry in (self.edt_name_change, self.edt_surname_change):  # Enabled = False in the .dfm
            entry.config(state="disabled")
        self.show("EditTab")

    def save_changes(self):
        u = self.user
        username = self.edt_username_change.get().strip()
        password = self.edt_password_change.get()
        email = self.edt_email_change.get()
        if not username or not password:
            messagebox.showinfo("Chateau de Yanda", "Username and password cannot be empty.")
            return
        try:
            self.dm.update_user(u.username, username, password, email)
        except Exception as exc:
            messagebox.showerror("Chateau de Yanda", f"Could not update: {exc}")
            return
        u.username, u.password, u.email = username, password, email
        messagebox.showinfo("Chateau de Yanda", "Information has been successfully Updated")
