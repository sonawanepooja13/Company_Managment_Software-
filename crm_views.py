import tkinter as tk
from tkinter import ttk, messagebox
import crm_engine

class EnhancedCRMWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enterprise CRM Dashboard")
        self.geometry("1000x650")
        
        crm_engine.init_crm_db()
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # Summary Header
        self.header_frame = ttk.Frame(self, padding="10")
        self.header_frame.pack(fill="x")
        
        self.val_label = ttk.Label(self.header_frame, text="Pipeline Value: $0.00", font=("Helvetica", 11, "bold"))
        self.val_label.pack(side="left", padx=15)
        
        self.leads_label = ttk.Label(self.header_frame, text="Active Leads: 0", font=("Helvetica", 11, "bold"))
        self.leads_label.pack(side="left", padx=15)

        # Tab Navigation
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Contacts & Leads
        self.tab_contacts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_contacts, text=" Contacts & Leads ")
        self.setup_contacts_tab()

        # Tab 2: Activity Logger
        self.tab_activity = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_activity, text=" Interaction History ")
        self.setup_activity_tab()

    def setup_contacts_tab(self):
        btn_bar = ttk.Frame(self.tab_contacts, padding="5")
        btn_bar.pack(fill="x")
        
        ttk.Button(btn_bar, text="+ New Lead", command=self.open_add_contact_dialog).pack(side="left", padx=5)
        ttk.Button(btn_bar, text="Refresh", command=self.refresh_data).pack(side="left", padx=5)
        ttk.Button(btn_bar, text="Open Company Data", command=self.open_selected_company).pack(side="left", padx=5)

        # Contacts Table
        self.contact_tree = ttk.Treeview(
            self.tab_contacts, 
            columns=("ID", "Company", "Contact", "Email", "Phone", "Status"), 
            show="headings"
        )
        for col in ("ID", "Company", "Contact", "Email", "Phone", "Status"):
            self.contact_tree.heading(col, text=col)
            self.contact_tree.column(col, width=130, anchor="w")

        self.contact_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_activity_tab(self):
        form = ttk.LabelFrame(self.tab_activity, text=" Log New Interaction ", padding="10")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Contact ID:").grid(row=0, column=0, sticky="w", pady=4)
        self.ent_cid = ttk.Entry(form, width=10)
        self.ent_cid.grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Type:").grid(row=0, column=2, sticky="w", pady=4, padx=(10, 0))
        self.cmb_type = ttk.Combobox(form, values=["Call", "Email", "Meeting", "Note"], state="readonly", width=12)
        self.cmb_type.set("Call")
        self.cmb_type.grid(row=0, column=3, sticky="w", pady=4)

        ttk.Label(form, text="Summary:").grid(row=1, column=0, sticky="w", pady=4)
        self.ent_summary = ttk.Entry(form, width=60)
        self.ent_summary.grid(row=1, column=1, columnspan=3, sticky="w", pady=4)

        ttk.Button(form, text="Save Log", command=self.save_interaction).pack(anchor="e", pady=5)

    def open_add_contact_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Contact")
        dialog.geometry("300x250")
        
        ttk.Label(dialog, text="Company Name:").pack(anchor="w", padx=10, pady=(10, 2))
        ent_comp = ttk.Entry(dialog, width=30)
        ent_comp.pack(padx=10)

        ttk.Label(dialog, text="Contact Person:").pack(anchor="w", padx=10, pady=(5, 2))
        ent_person = ttk.Entry(dialog, width=30)
        ent_person.pack(padx=10)

        ttk.Label(dialog, text="Email:").pack(anchor="w", padx=10, pady=(5, 2))
        ent_email = ttk.Entry(dialog, width=30)
        ent_email.pack(padx=10)

        def save():
            if ent_comp.get().strip():
                crm_engine.add_contact(ent_comp.get().strip(), ent_person.get().strip(), ent_email.get().strip(), "")
                self.refresh_data()
                dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).pack(pady=15)

    def open_selected_company(self):
        selected_item = self.contact_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a company/contact from the list first.", parent=self)
            return
        
        item_data = self.contact_tree.item(selected_item, "values")
        contact_id = item_data[0]
        company_name = item_data[1]
        
        messagebox.showinfo("Company Data", f"Opening details for ID: {contact_id} — {company_name}", parent=self)

    def save_interaction(self):
        cid = self.ent_cid.get().strip()
        summary = self.ent_summary.get().strip()
        itype = self.cmb_type.get()

        if cid.isdigit() and summary:
            crm_engine.log_interaction(int(cid), itype, summary)
            messagebox.showinfo("Success", "Interaction logged.", parent=self)
            self.ent_summary.delete(0, tk.END)

    def refresh_data(self):
        metrics = crm_engine.fetch_pipeline_metrics()
        self.val_label.config(text=f"Pipeline Value: ${metrics['total_pipeline_value']:,.2f}")
        self.leads_label.config(text=f"Active Leads: {metrics['active_leads']}")

        for item in self.contact_tree.get_children():
            self.contact_tree.delete(item)

        for row in crm_engine.fetch_all_contacts():
            self.contact_tree.insert("", "end", values=(row["id"], row["company_name"], row["primary_contact"], row["email"], row["phone"], row["status"]))