"""Tally-style top bar + module tab strip (matches screenshot).

Green header: company name | Create dropdown | F.Y. dropdown.
White strip: Dashboard | Customer/Vendor | Products/Services | Sale Invoice
| Purchase Invoice | Payment | Expense Income | Other Documents | Report.
"""
import tkinter as tk
from tkinter import ttk


GREEN = "#0db578"
NAV_BG = "#ffffff"
NAV_FG = "#8a8a8a"
NAV_ACTIVE = "#1a1a1a"
UNDERLINE = "#ff6b6b"

TABS = (
    ("Dashboard", "\U0001f6e3"),
    ("Customer / Vendor", "\U0001f465"),
    ("Products / Services", "\U0001f4e6"),
    ("Sale\nInvoice", "\U0001f9fe"),
    ("Purchase\nInvoice", "\U0001f6d2"),
    ("Payment", "\u20b9"),
    ("Expense\nIncome", "\u2197"),
    ("Other\nDocuments", "\U0001f4c4"),
    ("Report", "\U0001f4ca"),
)

# Entries of the "Create" dropdown: documents first, then the master records.
CREATE_DOCUMENTS = (
    "Sale Invoice",
    "Purchase Invoice",
    "Payment In / Out",
    "Quotation",
    "Proforma Invoice",
    "Sales Order",
    "Purchase Order",
    "Delivery Challan",
    "Job Work",
    "Credit Note",
    "Debit Note",
    "Service Request",
)

CREATE_MASTERS = ("Customer / Vendor", "Product / Service")


class TallyShell:
    """Builds header + nav inside parent, exposes body frame for content."""

    def __init__(self, parent, on_tab, on_create, company="SAARK EXPLORATION PRIVATE LIMITED"):
        self.on_tab = on_tab
        self.on_create = on_create
        self.active = tk.StringVar(value="Dashboard")
        self.fy_var = tk.StringVar(value="F.Y. 2026-2027")
        self._btns = {}
        self._lines = {}

        header = tk.Frame(parent, bg=GREEN, height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text=company, font=("Helvetica", 12, "bold"),
                 bg=GREEN, fg="white", anchor="w").pack(side="left", padx=18)

        right = tk.Frame(header, bg=GREEN)
        right.pack(side="right", padx=10)

        self.create_btn = tk.Menubutton(right, text="\u2795   Create   \u25be",
                                        font=("Helvetica", 10), bg="white",
                                        fg="#333333", relief="flat", padx=12,
                                        pady=6, cursor="hand2")
        self.create_btn.pack(side="left", padx=6)
        menu = tk.Menu(self.create_btn, tearoff=0)
        for label in CREATE_DOCUMENTS:
            menu.add_command(label=label,
                             command=lambda l=label: self.on_create(l))
        menu.add_separator()
        for label in CREATE_MASTERS:
            menu.add_command(label=label,
                             command=lambda l=label: self.on_create(l))
        self.create_btn.configure(menu=menu)

        ttk.Combobox(right, textvariable=self.fy_var, width=14,
                     font=("Helvetica", 10), state="readonly",
                     values=["F.Y. 2024-2025", "F.Y. 2025-2026",
                             "F.Y. 2026-2027", "F.Y. 2027-2028"]).pack(side="left", padx=6)
        for icon in ("\U0001f4ac", "\U0001f514", "\U0001f464"):
            tk.Label(right, text=icon, font=("Helvetica", 13),
                     bg=GREEN, fg="white").pack(side="left", padx=7)

        nav = tk.Frame(parent, bg=NAV_BG, highlightthickness=1,
                       highlightbackground="#e5e5e5")
        nav.pack(fill="x", side="top")
        for i, (label, icon) in enumerate(TABS):
            nav.grid_columnconfigure(i, weight=1, uniform="tally")
            cell = tk.Frame(nav, bg=NAV_BG)
            cell.grid(row=0, column=i, sticky="nsew")
            btn = tk.Button(cell, text=f"{icon}\n{label}", font=("Helvetica", 9),
                            bg=NAV_BG, fg=NAV_FG, relief="flat", cursor="hand2",
                            justify="center", wraplength=110,
                            activebackground="#f2f2f2", bd=0, highlightthickness=0,
                            command=lambda l=label: self.select(l))
            btn.pack(fill="both", expand=True, padx=1, pady=(6, 2))
            line = tk.Frame(cell, bg=NAV_BG, height=3)
            line.pack(fill="x", side="bottom")
            self._btns[label] = btn
            self._lines[label] = line
        self.refresh()

        self.body = ttk.Frame(parent)
        self.body.pack(fill="both", expand=True)

    def select(self, label):
        self.active.set(label)
        self.refresh()
        self.on_tab(label)

    def set_active(self, label):
        if label in self._btns:
            self.active.set(label)
            self.refresh()

    def refresh(self):
        act = self.active.get()
        for label, btn in self._btns.items():
            on = (label == act)
            btn.configure(fg=NAV_ACTIVE if on else NAV_FG,
                          font=("Helvetica", 9, "bold") if on else ("Helvetica", 9))
            self._lines[label].configure(bg=UNDERLINE if on else NAV_BG)

    def clear_body(self):
        for w in self.body.winfo_children():
            w.destroy()
