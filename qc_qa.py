import csv
import os
import uuid
from datetime import datetime

import tkinter as tk
from tkinter import messagebox, ttk

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv_data")
os.makedirs(DATA_DIR, exist_ok=True)

LOTS_FILE = os.path.join(DATA_DIR, "qc_inspection_lots.csv")
COA_FILE = os.path.join(DATA_DIR, "qc_coa.csv")
NCR_FILE = os.path.join(DATA_DIR, "qc_ncr.csv")
SCORECARD_FILE = os.path.join(DATA_DIR, "qc_scorecards.csv")

LOT_HEADERS = [
    "lot_id",
    "po_no",
    "material",
    "supplier",
    "supplier_batch",
    "qty_received",
    "qty_sampled",
    "inspection_status",
    "quality_status",
    "inspector",
    "created_on",
]

COA_HEADERS = [
    "coa_id",
    "material",
    "supplier",
    "supplier_batch",
    "coa_no",
    "issue_date",
    "verified",
    "verification_status",
    "created_on",
]

NCR_HEADERS = [
    "ncr_id",
    "lot_id",
    "material",
    "supplier",
    "defect_code",
    "severity",
    "qty_affected",
    "description",
    "disposition",
    "status",
    "created_on",
]

SCORECARD_HEADERS = [
    "supplier",
    "receipts",
    "pass_rate",
    "defect_rate",
    "ncr_count",
    "rating",
    "updated_on",
]


def ensure_csv(path, headers):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()


def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def save_csv(path, rows, headers):
    ensure_csv(path, headers)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


class QCQAView(ttk.Frame):
    def __init__(self, parent, user_data=None):
        super().__init__(parent, padding=10)
        self.user_data = user_data or {}
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.notebook.add(OverviewTab(self.notebook), text=" Overview ")
        self.notebook.add(InspectionLotsTab(self.notebook), text=" Inspection Lots ")
        self.notebook.add(CoATab(self.notebook), text=" CoA & Specs ")
        self.notebook.add(NCRTab(self.notebook), text=" NCR & Disposition ")
        self.notebook.add(ScorecardTab(self.notebook), text=" Supplier Scorecard ")


class OverviewTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.setup_ui()
        self.refresh_metrics()

    def setup_ui(self):
        header = ttk.Label(self, text="Quality Control & Quality Assurance", font=("Helvetica", 14, "bold"))
        header.pack(anchor="w", pady=(0, 10))

        summary = ttk.LabelFrame(self, text=" Quality Snapshot ", padding=10)
        summary.pack(fill="x", pady=(0, 12))

        self.total_lots_var = tk.StringVar(value="0")
        self.accepted_var = tk.StringVar(value="0")
        self.rejected_var = tk.StringVar(value="0")
        self.open_ncr_var = tk.StringVar(value="0")

        ttk.Label(summary, text="Inspection Lots:").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ttk.Label(summary, textvariable=self.total_lots_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, padx=8, pady=6, sticky="w")

        ttk.Label(summary, text="Accepted:").grid(row=0, column=2, padx=8, pady=6, sticky="w")
        ttk.Label(summary, textvariable=self.accepted_var, font=("Helvetica", 10, "bold"), foreground="green").grid(row=0, column=3, padx=8, pady=6, sticky="w")

        ttk.Label(summary, text="Rejected:").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        ttk.Label(summary, textvariable=self.rejected_var, font=("Helvetica", 10, "bold"), foreground="red").grid(row=1, column=1, padx=8, pady=6, sticky="w")

        ttk.Label(summary, text="Open NCR:").grid(row=1, column=2, padx=8, pady=6, sticky="w")
        ttk.Label(summary, textvariable=self.open_ncr_var, font=("Helvetica", 10, "bold"), foreground="orange").grid(row=1, column=3, padx=8, pady=6, sticky="w")

        info = ttk.LabelFrame(self, text=" QC/QA Controls ", padding=10)
        info.pack(fill="both", expand=True)

        ttk.Label(info, text="• Incoming materials are placed on quality hold until inspection is approved.").pack(anchor="w", pady=2)
        ttk.Label(info, text="• GRN quantities cannot be released into inventory before acceptance or approved disposition.").pack(anchor="w", pady=2)
        ttk.Label(info, text="• Failed inspections create NCRs and trigger supplier quality alerts. ").pack(anchor="w", pady=2)
        ttk.Label(info, text="• Accepted lots are linked to supplier batch, CoA, and downstream inventory traceability.").pack(anchor="w", pady=2)

    def refresh_metrics(self):
        lots = load_csv(LOTS_FILE)
        ncr = load_csv(NCR_FILE)
        accepted = sum(1 for row in lots if row.get("quality_status", "").upper() == "ACCEPTED")
        rejected = sum(1 for row in lots if row.get("quality_status", "").upper() in {"REJECTED", "RETURN_TO_VENDOR", "SCRAPPED"})
        open_ncr = sum(1 for row in ncr if row.get("status", "").upper() in {"OPEN", "IN_REVIEW"})

        self.total_lots_var.set(str(len(lots)))
        self.accepted_var.set(str(accepted))
        self.rejected_var.set(str(rejected))
        self.open_ncr_var.set(str(open_ncr))


class InspectionLotsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.setup_ui()
        self.refresh_tree()

    def setup_ui(self):
        form = ttk.LabelFrame(self, text=" Create Inspection Lot ", padding=10)
        form.pack(fill="x", pady=(0, 12))

        fields = [
            ("PO No", 0, 0),
            ("Material", 0, 2),
            ("Supplier", 1, 0),
            ("Supplier Batch", 1, 2),
            ("Qty Received", 2, 0),
            ("Qty Sampled", 2, 2),
            ("Inspector", 3, 0),
            ("Status", 3, 2),
        ]

        self.po_var = tk.StringVar()
        self.material_var = tk.StringVar()
        self.supplier_var = tk.StringVar()
        self.batch_var = tk.StringVar()
        self.qty_received_var = tk.StringVar(value="0")
        self.qty_sampled_var = tk.StringVar(value="0")
        self.inspector_var = tk.StringVar(value="QA Engineer")
        self.status_var = tk.StringVar(value="Pending Inspection")

        widgets = {
            "PO No": self.po_var,
            "Material": self.material_var,
            "Supplier": self.supplier_var,
            "Supplier Batch": self.batch_var,
            "Qty Received": self.qty_received_var,
            "Qty Sampled": self.qty_sampled_var,
            "Inspector": self.inspector_var,
            "Status": self.status_var,
        }

        for label_text, row, col in fields:
            ttk.Label(form, text=f"{label_text}:").grid(row=row, column=col, sticky="w", padx=6, pady=6)
            if label_text == "Status":
                combo = ttk.Combobox(form, textvariable=self.status_var, values=["Pending Inspection", "Under Review", "Accepted", "Rejected", "Disposed"], state="readonly", width=22)
                combo.grid(row=row, column=col + 1, padx=6, pady=6, sticky="ew")
            elif label_text in {"Qty Received", "Qty Sampled"}:
                entry = ttk.Entry(form, textvariable=widgets[label_text], width=25)
                entry.grid(row=row, column=col + 1, padx=6, pady=6, sticky="ew")
            else:
                entry = ttk.Entry(form, textvariable=widgets[label_text], width=25)
                entry.grid(row=row, column=col + 1, padx=6, pady=6, sticky="ew")

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Create Lot", command=self.create_lot).pack(side="left", padx=5)
        ttk.Button(actions, text="Accept Selected", command=self.accept_selected).pack(side="left", padx=5)
        ttk.Button(actions, text="Reject Selected", command=self.reject_selected).pack(side="left", padx=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("lot_id", "po_no", "material", "supplier", "batch", "qty_received", "qty_sampled", "status", "quality"), show="headings")
        for col in ["lot_id", "po_no", "material", "supplier", "batch", "qty_received", "qty_sampled", "status", "quality"]:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120, anchor="w")
        self.tree.pack(fill="both", expand=True)

    def create_lot(self):
        lot = {
            "lot_id": str(uuid.uuid4()),
            "po_no": self.po_var.get().strip(),
            "material": self.material_var.get().strip(),
            "supplier": self.supplier_var.get().strip(),
            "supplier_batch": self.batch_var.get().strip(),
            "qty_received": self.qty_received_var.get().strip() or "0",
            "qty_sampled": self.qty_sampled_var.get().strip() or "0",
            "inspection_status": self.status_var.get(),
            "quality_status": "HOLD" if self.status_var.get() != "Accepted" else "ACCEPTED",
            "inspector": self.inspector_var.get().strip() or "QA Engineer",
            "created_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if not lot["po_no"] or not lot["material"]:
            messagebox.showwarning("Input Required", "PO No and Material are required.", parent=self)
            return

        rows = load_csv(LOTS_FILE)
        rows.append(lot)
        save_csv(LOTS_FILE, rows, LOT_HEADERS)
        self.refresh_tree()
        messagebox.showinfo("Saved", "Inspection lot created successfully.", parent=self)
        self.clear_form()

    def accept_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Lot", "Please select an inspection lot.", parent=self)
            return
        lot_id = self.tree.item(selected[0], "values")[0]
        rows = load_csv(LOTS_FILE)
        for row in rows:
            if row.get("lot_id") == lot_id:
                row["inspection_status"] = "Accepted"
                row["quality_status"] = "ACCEPTED"
        save_csv(LOTS_FILE, rows, LOT_HEADERS)
        self.refresh_tree()

    def reject_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Lot", "Please select an inspection lot.", parent=self)
            return
        lot_id = self.tree.item(selected[0], "values")[0]
        rows = load_csv(LOTS_FILE)
        for row in rows:
            if row.get("lot_id") == lot_id:
                row["inspection_status"] = "Rejected"
                row["quality_status"] = "REJECTED"
        save_csv(LOTS_FILE, rows, LOT_HEADERS)
        self.refresh_tree()

    def clear_form(self):
        self.po_var.set("")
        self.material_var.set("")
        self.supplier_var.set("")
        self.batch_var.set("")
        self.qty_received_var.set("0")
        self.qty_sampled_var.set("0")
        self.inspector_var.set("QA Engineer")
        self.status_var.set("Pending Inspection")

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in load_csv(LOTS_FILE):
            self.tree.insert("", "end", values=(
                row.get("lot_id", ""),
                row.get("po_no", ""),
                row.get("material", ""),
                row.get("supplier", ""),
                row.get("supplier_batch", ""),
                row.get("qty_received", ""),
                row.get("qty_sampled", ""),
                row.get("inspection_status", ""),
                row.get("quality_status", ""),
            ))


class CoATab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.setup_ui()
        self.refresh_tree()

    def setup_ui(self):
        form = ttk.LabelFrame(self, text=" CoA Record ", padding=10)
        form.pack(fill="x", pady=(0, 12))

        self.material_var = tk.StringVar()
        self.supplier_var = tk.StringVar()
        self.batch_var = tk.StringVar()
        self.coa_no_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Pending")
        self.verified_var = tk.BooleanVar(value=False)

        labels = [
            ("Material", self.material_var),
            ("Supplier", self.supplier_var),
            ("Supplier Batch", self.batch_var),
            ("CoA No", self.coa_no_var),
        ]

        for idx, (label, var) in enumerate(labels):
            ttk.Label(form, text=f"{label}:").grid(row=idx, column=0, sticky="w", padx=6, pady=6)
            ttk.Entry(form, textvariable=var, width=28).grid(row=idx, column=1, padx=6, pady=6, sticky="ew")

        ttk.Label(form, text="Verification Status:").grid(row=4, column=0, sticky="w", padx=6, pady=6)
        ttk.Combobox(form, textvariable=self.status_var, values=["Pending", "Verified", "Mismatch"], state="readonly", width=20).grid(row=4, column=1, padx=6, pady=6, sticky="ew")
        ttk.Checkbutton(form, text="Verified Against Technical Spec", variable=self.verified_var).grid(row=5, column=0, columnspan=2, sticky="w", padx=6, pady=6)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Save CoA", command=self.save_coa).pack(side="left", padx=5)
        ttk.Button(actions, text="Mark Verified", command=self.mark_verified).pack(side="left", padx=5)

        self.tree = ttk.Treeview(self, columns=("coa_id", "material", "supplier", "batch", "coa_no", "status", "verified"), show="headings")
        for col in ["coa_id", "material", "supplier", "batch", "coa_no", "status", "verified"]:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=130, anchor="w")
        self.tree.pack(fill="both", expand=True)

    def save_coa(self):
        row = {
            "coa_id": str(uuid.uuid4()),
            "material": self.material_var.get().strip(),
            "supplier": self.supplier_var.get().strip(),
            "supplier_batch": self.batch_var.get().strip(),
            "coa_no": self.coa_no_var.get().strip(),
            "issue_date": datetime.now().strftime("%Y-%m-%d"),
            "verified": "Yes" if self.verified_var.get() else "No",
            "verification_status": self.status_var.get(),
            "created_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        rows = load_csv(COA_FILE)
        rows.append(row)
        save_csv(COA_FILE, rows, COA_HEADERS)
        self.refresh_tree()
        self.clear_form()

    def mark_verified(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select CoA", "Choose a CoA record to verify.", parent=self)
            return
        coa_id = self.tree.item(selected[0], "values")[0]
        rows = load_csv(COA_FILE)
        for row in rows:
            if row.get("coa_id") == coa_id:
                row["verified"] = "Yes"
                row["verification_status"] = "Verified"
        save_csv(COA_FILE, rows, COA_HEADERS)
        self.refresh_tree()

    def clear_form(self):
        self.material_var.set("")
        self.supplier_var.set("")
        self.batch_var.set("")
        self.coa_no_var.set("")
        self.status_var.set("Pending")
        self.verified_var.set(False)

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in load_csv(COA_FILE):
            self.tree.insert("", "end", values=(
                row.get("coa_id", ""),
                row.get("material", ""),
                row.get("supplier", ""),
                row.get("supplier_batch", ""),
                row.get("coa_no", ""),
                row.get("verification_status", ""),
                row.get("verified", ""),
            ))


class NCRTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.setup_ui()
        self.refresh_tree()

    def setup_ui(self):
        form = ttk.LabelFrame(self, text=" Create NCR ", padding=10)
        form.pack(fill="x", pady=(0, 12))

        self.lot_id_var = tk.StringVar()
        self.material_var = tk.StringVar()
        self.supplier_var = tk.StringVar()
        self.defect_code_var = tk.StringVar()
        self.severity_var = tk.StringVar(value="Medium")
        self.qty_var = tk.StringVar(value="0")
        self.disposition_var = tk.StringVar(value="Return to Vendor")
        self.status_var = tk.StringVar(value="Open")
        self.description = tk.Text(form, height=4, width=55)

        fields = [
            ("Lot ID", self.lot_id_var, 0),
            ("Material", self.material_var, 1),
            ("Supplier", self.supplier_var, 2),
            ("Defect Code", self.defect_code_var, 3),
            ("Severity", self.severity_var, 4),
            ("Qty Affected", self.qty_var, 5),
            ("Disposition", self.disposition_var, 6),
            ("Status", self.status_var, 7),
        ]

        for label, variable, row in fields:
            ttk.Label(form, text=f"{label}:").grid(row=row, column=0, sticky="w", padx=6, pady=6)
            if label in {"Severity", "Disposition", "Status"}:
                values = {
                    "Severity": ["Low", "Medium", "High", "Critical"],
                    "Disposition": ["Return to Vendor", "Scrap", "Rework", "Conditional Use"],
                    "Status": ["Open", "In Review", "Approved", "Closed"],
                }[label]
                ttk.Combobox(form, textvariable=variable, values=values, state="readonly", width=25).grid(row=row, column=1, padx=6, pady=6, sticky="ew")
            else:
                ttk.Entry(form, textvariable=variable, width=30).grid(row=row, column=1, padx=6, pady=6, sticky="ew")

        ttk.Label(form, text="Description:").grid(row=8, column=0, sticky="nw", padx=6, pady=6)
        self.description.grid(row=8, column=1, padx=6, pady=6, sticky="ew")

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Create NCR", command=self.create_ncr).pack(side="left", padx=5)
        ttk.Button(actions, text="Close NCR", command=self.close_ncr).pack(side="left", padx=5)

        self.tree = ttk.Treeview(self, columns=("ncr_id", "lot_id", "material", "supplier", "defect", "severity", "qty", "status", "disposition"), show="headings")
        for col in ["ncr_id", "lot_id", "material", "supplier", "defect", "severity", "qty", "status", "disposition"]:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=120, anchor="w")
        self.tree.pack(fill="both", expand=True)

    def create_ncr(self):
        row = {
            "ncr_id": str(uuid.uuid4()),
            "lot_id": self.lot_id_var.get().strip(),
            "material": self.material_var.get().strip(),
            "supplier": self.supplier_var.get().strip(),
            "defect_code": self.defect_code_var.get().strip(),
            "severity": self.severity_var.get(),
            "qty_affected": self.qty_var.get().strip() or "0",
            "description": self.description.get("1.0", "end").strip(),
            "disposition": self.disposition_var.get(),
            "status": self.status_var.get(),
            "created_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if not row["lot_id"] or not row["material"]:
            messagebox.showwarning("Input Required", "Lot ID and Material are required.", parent=self)
            return
        rows = load_csv(NCR_FILE)
        rows.append(row)
        save_csv(NCR_FILE, rows, NCR_HEADERS)
        self.refresh_tree()
        self.clear_form()

    def close_ncr(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select NCR", "Choose an NCR to close.", parent=self)
            return
        ncr_id = self.tree.item(selected[0], "values")[0]
        rows = load_csv(NCR_FILE)
        for row in rows:
            if row.get("ncr_id") == ncr_id:
                row["status"] = "Closed"
        save_csv(NCR_FILE, rows, NCR_HEADERS)
        self.refresh_tree()

    def clear_form(self):
        self.lot_id_var.set("")
        self.material_var.set("")
        self.supplier_var.set("")
        self.defect_code_var.set("")
        self.severity_var.set("Medium")
        self.qty_var.set("0")
        self.disposition_var.set("Return to Vendor")
        self.status_var.set("Open")
        self.description.delete("1.0", "end")

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in load_csv(NCR_FILE):
            self.tree.insert("", "end", values=(
                row.get("ncr_id", ""),
                row.get("lot_id", ""),
                row.get("material", ""),
                row.get("supplier", ""),
                row.get("defect_code", ""),
                row.get("severity", ""),
                row.get("qty_affected", ""),
                row.get("status", ""),
                row.get("disposition", ""),
            ))


class ScorecardTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.setup_ui()
        self.refresh_tree()

    def setup_ui(self):
        self.tree = ttk.Treeview(self, columns=("supplier", "receipts", "pass_rate", "defect_rate", "ncr_count", "rating"), show="headings")
        for col in ["supplier", "receipts", "pass_rate", "defect_rate", "ncr_count", "rating"]:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=140, anchor="w")
        self.tree.pack(fill="both", expand=True)

        ttk.Button(self, text="Refresh Scorecards", command=self.refresh_tree).pack(anchor="w", pady=(8, 0))

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        lots = load_csv(LOTS_FILE)
        ncr_rows = load_csv(NCR_FILE)
        supplier_map = {}

        for row in lots:
            supplier = row.get("supplier", "Unknown")
            supplier_map.setdefault(supplier, {"receipts": 0, "accepted": 0, "ncr": 0})
            supplier_map[supplier]["receipts"] += 1
            if row.get("quality_status", "").upper() == "ACCEPTED":
                supplier_map[supplier]["accepted"] += 1

        for row in ncr_rows:
            supplier = row.get("supplier", "Unknown")
            supplier_map.setdefault(supplier, {"receipts": 0, "accepted": 0, "ncr": 0})
            supplier_map[supplier]["ncr"] += 1

        for supplier, data in supplier_map.items():
            receipts = data["receipts"]
            accepted = data["accepted"]
            pass_rate = (accepted / receipts * 100) if receipts else 0
            defect_rate = (data["ncr"] / receipts * 100) if receipts else 0
            rating = "A" if pass_rate >= 95 and defect_rate <= 5 else "B" if pass_rate >= 85 else "C" if pass_rate >= 70 else "D"
            self.tree.insert("", "end", values=(
                supplier,
                receipts,
                f"{pass_rate:.1f}%",
                f"{defect_rate:.1f}%",
                data["ncr"],
                rating,
            ))
