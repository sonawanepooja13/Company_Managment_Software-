import tkinter as tk
from tkinter import ttk, messagebox


class PanelManufacturingView(ttk.Frame):
    """Panel Manufacturing Workspace View Component."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        
        self.setup_ui()

    def setup_ui(self):
        # Header Section
        header_frame = ttk.Frame(self, padding="15")
        header_frame.pack(fill="x")

        ttk.Label(
            header_frame,
            text="Panel Manufacturing Dashboard",
            font=("Helvetica", 14, "bold"),
        ).pack(side="left")

        # Action Button Bar
        btn_bar = ttk.Frame(self, padding="10")
        btn_bar.pack(fill="x")

        ttk.Button(
            btn_bar, text="➕ Create Assembly Job", command=self.create_job_dialog
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_bar, text="📋 Refresh Orders", command=self.load_orders
        ).pack(side="left", padx=5)

        # Tabbed Layout for Operations
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Active Production Jobs
        self.tab_active = ttk.Frame(notebook)
        notebook.add(self.tab_active, text=" Active Assembly Line ")
        self.setup_active_jobs_tab()

        # Tab 2: Quality Inspection (QC)
        self.tab_qc = ttk.Frame(notebook)
        notebook.add(self.tab_qc, text=" Quality Control & Testing ")
        self.setup_qc_tab()

    def setup_active_jobs_tab(self):
        columns = ("Job ID", "Panel Type", "Stage", "Assigned Tech", "Status", "Target Date")
        self.job_tree = ttk.Treeview(
            self.tab_active, columns=columns, show="headings"
        )
        
        for col in columns:
            self.job_tree.heading(col, text=col)
            self.job_tree.column(col, width=130, anchor="center")

        self.job_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.load_orders()

    def setup_qc_tab(self):
        qc_frame = ttk.LabelFrame(self.tab_qc, text=" High Voltage & Logic Testing ", padding=15)
        qc_frame.pack(fill="x", padx=15, pady=15)

        ttk.Label(qc_frame, text="Panel Serial No:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_serial = ttk.Entry(qc_frame, width=20)
        self.ent_serial.grid(row=0, column=1, sticky="w", pady=5, padx=5)

        ttk.Label(qc_frame, text="QC Inspector:").grid(row=0, column=2, sticky="w", pady=5, padx=(15, 0))
        self.ent_inspector = ttk.Entry(qc_frame, width=20)
        self.ent_inspector.insert(0, self.user_data.get("full_name", self.user_data.get("username", "")))
        self.ent_inspector.grid(row=0, column=3, sticky="w", pady=5, padx=5)

        self.chk_insulation = tk.BooleanVar()
        self.chk_wiring = tk.BooleanVar()
        
        ttk.Checkbutton(qc_frame, text="Insulation Resistance Test Passed", variable=self.chk_insulation).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Checkbutton(qc_frame, text="Wiring Continuity & Torque Verified", variable=self.chk_wiring).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

        ttk.Button(qc_frame, text="Submit QC Sign-off", command=self.save_qc_record).grid(row=3, column=3, sticky="e", pady=10)

    def load_orders(self):
        """Loads demo manufacturing jobs into table."""
        for item in self.job_tree.get_children():
            self.job_tree.delete(item)

        # Sample initial panel data
        sample_jobs = [
            ("JOB-101", "Duplex Booster VFD", "Wiring", "John Doe", "In Progress", "2026-08-25"),
            ("JOB-102", "Simplex Starter Panel", "Quality Testing", "Alice Smith", "Testing", "2026-08-22"),
            ("JOB-103", "Triplex Pump Logic Panel", "Enclosure Preparation", "Bob Johnson", "Pending", "2026-08-28"),
        ]
        
        for job in sample_jobs:
            self.job_tree.insert("", "end", values=job)

    def create_job_dialog(self):
        """Dialog to add a new manufacturing job."""
        dialog = tk.Toplevel(self)
        dialog.title("Create Assembly Job")
        dialog.geometry("340x260")
        dialog.minsize(340, 260)
        dialog.resizable(True, True)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Panel Type:").pack(anchor="w", padx=15, pady=(15, 2))
        ent_type = ttk.Entry(dialog, width=35)
        ent_type.pack(padx=15)

        ttk.Label(dialog, text="Assigned Technician:").pack(anchor="w", padx=15, pady=(8, 2))
        ent_tech = ttk.Entry(dialog, width=35)
        ent_tech.pack(padx=15)

        ttk.Label(dialog, text="Target Completion Date:").pack(anchor="w", padx=15, pady=(8, 2))
        ent_date = ttk.Entry(dialog, width=35)
        ent_date.insert(0, "2026-08-30")
        ent_date.pack(padx=15)

        def save_job():
            p_type = ent_type.get().strip()
            tech = ent_tech.get().strip()
            date_val = ent_date.get().strip()

            if p_type and tech:
                new_id = f"JOB-{101 + len(self.job_tree.get_children())}"
                self.job_tree.insert("", "end", values=(new_id, p_type, "Assembly", tech, "In Progress", date_val))
                messagebox.showinfo("Success", f"Job {new_id} added successfully!", parent=dialog)
                dialog.destroy()
            else:
                messagebox.showwarning("Input Error", "Please fill required fields.", parent=dialog)

        ttk.Button(dialog, text="Save Job", command=save_job).pack(pady=15)

    def save_qc_record(self):
        serial = self.ent_serial.get().strip()
        if not serial:
            messagebox.showwarning("Warning", "Please enter panel serial number.")
            return

        if self.chk_insulation.get() and self.chk_wiring.get():
            messagebox.showinfo("QC Status", f"Panel {serial} successfully approved for dispatch!")
            self.ent_serial.delete(0, tk.END)
            self.chk_insulation.set(False)
            self.chk_wiring.set(False)
        else:
            messagebox.showerror("QC Failed", f"Panel {serial} cannot pass without completing all test checks.")