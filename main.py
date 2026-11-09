"""main.py - program entry point (port of Project1.dpr)."""
import sys
import tkinter as tk
from tkinter import messagebox

from dm_shop import DEFAULT_DB, DmShop
from form1 import Form1


def main() -> None:
    root = tk.Tk()  # Application.Initialize
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
    try:
        dm_shop = DmShop.open_access(db_path)  # the data module opens the database
    except Exception as exc:
        messagebox.showerror("Chateau de Yanda", f"Could not open the database:\n{exc}")
        return
    Form1(root, dm_shop)  # Application.CreateForm(TForm1, Form1)
    root.mainloop()  # Application.Run
    dm_shop.close()


if __name__ == "__main__":
    main()
