import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
from datetime import datetime


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

DB_NAME = "accounts_finance.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            party TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# SAVE TRANSACTION
# ---------------------------------------------------------

def save_transaction():

    date = date_entry.get()
    party = party_entry.get()
    transaction_type = type_combo.get()
    amount = amount_entry.get()
    description = description_entry.get()

    if not date or not party or not transaction_type or not amount:
        messagebox.showerror(
            "Error",
            "Please fill Date, Party, Type and Amount."
        )
        return

    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror(
            "Error",
            "Amount must be a number."
        )
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (date, party, transaction_type, amount, description)
        VALUES (?, ?, ?, ?, ?)
    """, (
        date,
        party,
        transaction_type,
        amount,
        description
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Success",
        "Transaction saved successfully."
    )

    clear_fields()
    load_transactions()


# ---------------------------------------------------------
# CLEAR FIELDS
# ---------------------------------------------------------

def clear_fields():

    date_entry.delete(0, tk.END)
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    party_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    description_entry.delete(0, tk.END)

    type_combo.set("Sales")


# ---------------------------------------------------------
# LOAD TRANSACTIONS
# ---------------------------------------------------------

def load_transactions():

    for item in table.get_children():
        table.delete(item)

    conn = sqlite3.connect(DB_NAME)

    query = """
        SELECT id, date, party, transaction_type,
               amount, description
        FROM transactions
        ORDER BY id DESC
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    for _, row in df.iterrows():

        table.insert(
            "",
            tk.END,
            values=(
                row["id"],
                row["date"],
                row["party"],
                row["transaction_type"],
                f"{row['amount']:.2f}",
                row["description"]
            )
        )


# ---------------------------------------------------------
# EXPORT EXCEL
# ---------------------------------------------------------

def export_excel():

    conn = sqlite3.connect(DB_NAME)

    query = """
        SELECT *
        FROM transactions
        ORDER BY date
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    if df.empty:
        messagebox.showwarning(
            "Warning",
            "No transactions available."
        )
        return

    filename = "Accounts_Finance_Report.xlsx"

    df.to_excel(
        filename,
        index=False
    )

    messagebox.showinfo(
        "Excel Export",
        f"Excel file created:\n{filename}"
    )


# ---------------------------------------------------------
# EXPORT CSV
# ---------------------------------------------------------

def export_csv():

    conn = sqlite3.connect(DB_NAME)

    query = """
        SELECT *
        FROM transactions
        ORDER BY date
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    if df.empty:
        messagebox.showwarning(
            "Warning",
            "No transactions available."
        )
        return

    filename = "Accounts_Finance_Report.csv"

    df.to_csv(
        filename,
        index=False
    )

    messagebox.showinfo(
        "CSV Export",
        f"CSV file created:\n{filename}"
    )


# ---------------------------------------------------------
# GUI
# ---------------------------------------------------------

create_database()

root = tk.Tk()

root.title("Accounts & Finance Management System")
root.geometry("1100x650")

root.resizable(True, True)


# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

title_label = tk.Label(
    root,
    text="Accounts & Finance Management System",
    font=("Arial", 20, "bold")
)

title_label.pack(pady=15)


# ---------------------------------------------------------
# INPUT FRAME
# ---------------------------------------------------------

input_frame = tk.Frame(root)

input_frame.pack(pady=10)


# Date

tk.Label(
    input_frame,
    text="Date"
).grid(row=0, column=0, padx=10, pady=8)

date_entry = tk.Entry(
    input_frame,
    width=20
)

date_entry.grid(row=0, column=1)

date_entry.insert(
    0,
    datetime.now().strftime("%Y-%m-%d")
)


# Party

tk.Label(
    input_frame,
    text="Party / Customer"
).grid(row=0, column=2, padx=10)

party_entry = tk.Entry(
    input_frame,
    width=25
)

party_entry.grid(row=0, column=3)


# Transaction Type

tk.Label(
    input_frame,
    text="Transaction Type"
).grid(row=1, column=0, padx=10, pady=8)

type_combo = ttk.Combobox(
    input_frame,
    values=[
        "Sales",
        "Purchase",
        "Expense",
        "Receipt",
        "Payment"
    ],
    width=18,
    state="readonly"
)

type_combo.grid(row=1, column=1)

type_combo.set("Sales")


# Amount

tk.Label(
    input_frame,
    text="Amount"
).grid(row=1, column=2, padx=10)

amount_entry = tk.Entry(
    input_frame,
    width=25
)

amount_entry.grid(row=1, column=3)


# Description

tk.Label(
    input_frame,
    text="Description"
).grid(row=2, column=0, padx=10, pady=8)

description_entry = tk.Entry(
    input_frame,
    width=70
)

description_entry.grid(
    row=2,
    column=1,
    columnspan=3
)


# ---------------------------------------------------------
# BUTTONS
# ---------------------------------------------------------

button_frame = tk.Frame(root)

button_frame.pack(pady=15)


tk.Button(
    button_frame,
    text="Save Transaction",
    command=save_transaction,
    width=18
).grid(row=0, column=0, padx=8)


tk.Button(
    button_frame,
    text="Clear",
    command=clear_fields,
    width=15
).grid(row=0, column=1, padx=8)


tk.Button(
    button_frame,
    text="Export Excel",
    command=export_excel,
    width=15
).grid(row=0, column=2, padx=8)


tk.Button(
    button_frame,
    text="Export CSV",
    command=export_csv,
    width=15
).grid(row=0, column=3, padx=8)


# ---------------------------------------------------------
# TRANSACTION TABLE
# ---------------------------------------------------------

table_frame = tk.Frame(root)

table_frame.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)


columns = (
    "ID",
    "Date",
    "Party",
    "Type",
    "Amount",
    "Description"
)

table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)


for column in columns:

    table.heading(
        column,
        text=column
    )

    table.column(
        column,
        width=150
    )


table.column("ID", width=50)
table.column("Date", width=100)
table.column("Type", width=100)
table.column("Amount", width=120)


table.pack(
    side="left",
    fill="both",
    expand=True
)


# Scrollbar

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=table.yview
)

scrollbar.pack(
    side="right",
    fill="y"
)

table.configure(
    yscrollcommand=scrollbar.set
)


# ---------------------------------------------------------
# LOAD EXISTING DATA
# ---------------------------------------------------------

load_transactions()


# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------

root.mainloop()