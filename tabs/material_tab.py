import csv
import os

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import bom_engine
import config


class MaterialTab(ttk.Frame):
    def __init__(self, parent, price_tab_data=None):
        super().__init__(parent)
        self.current_bom = []
        self.current_labor_cost = 0.0
        self.current_grand_total = 0.0
        self.price_tab_data = price_tab_data or {}

        self.build_ui()
        
        # If data received from Price List, populate the fields after UI is ready
        if self.price_tab_data:
            self.after(50, self.populate_from_price_list)
    
    def update_price_tab_data(self, data):
        """Update price tab data and refresh fields."""
        self.price_tab_data = data
        self.populate_from_price_list()

    def build_ui(self):
        title = ttk.Label(self, text="Material & Labor Calculator", font=("Helvetica", 14, "bold"))
        title.pack(pady=10)

        # Create scrollable frame
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Material Company Selection Section
        company_frame = ttk.LabelFrame(scrollable_frame, text=" Material Company Selection ", padding="10")
        company_frame.pack(fill="x", padx=15, pady=5)
        
        company_row = ttk.Frame(company_frame)
        company_row.pack(fill="x")
        
        ttk.Label(company_row, text="Select Material Company:").pack(side="left", padx=(0, 5))
        self.company_combo = ttk.Combobox(company_row, width=25, state="readonly")
        self.company_combo.pack(side="left", padx=(0, 5))
        
        add_company_btn = ttk.Button(company_row, text="+ Add Company", command=self.add_material_company)
        add_company_btn.pack(side="left", padx=(0, 5))
        
        remove_company_btn = ttk.Button(company_row, text="- Remove Company", command=self.remove_material_company)
        remove_company_btn.pack(side="left", padx=(0, 5))
        
        # Load companies from CSV
        self.load_material_companies()

        form_frame = ttk.LabelFrame(scrollable_frame, text=" Inputs (Yellow Section) ", padding="10")
        form_frame.pack(fill="x", padx=15, pady=5)

        row = 0

        ttk.Label(form_frame, text="Pump Type:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_pump_type_combo = ttk.Combobox(form_frame, values=["3 Phase", "1 Phase"], width=18, state="readonly")
        self.m_pump_type_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_pump_type_combo.set("3 Phase")
        row += 1

        ttk.Label(form_frame, text="Pump Current (A):").grid(row=row, column=0, sticky="w", pady=4)
        self.m_current_entry = ttk.Entry(form_frame, width=20)
        self.m_current_entry.grid(row=row, column=1, sticky="e", pady=4)
        self.m_current_entry.insert(0, "15")
        row += 1

        ttk.Label(form_frame, text="Number of Pumps:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_pumps_combo = ttk.Combobox(form_frame, values=["1", "2", "3", "4", "5"], width=18, state="readonly")
        self.m_pumps_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_pumps_combo.set("3")
        row += 1

        ttk.Label(form_frame, text="Number of VFD:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_vfd_combo = ttk.Combobox(form_frame, values=["0", "1", "2", "3", "4"], width=18, state="readonly")
        self.m_vfd_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_vfd_combo.set("1")
        row += 1

        ttk.Label(form_frame, text="Main Incomer Required:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_incomer_combo = ttk.Combobox(form_frame, values=["1 - Yes", "0 - No"], width=18, state="readonly")
        self.m_incomer_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_incomer_combo.set("1 - Yes")
        row += 1

        ttk.Label(form_frame, text="3-Pole Door Mount Switch:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_door_mount_combo = ttk.Combobox(form_frame, values=["1 - Yes", "0 - No"], width=18, state="readonly")
        self.m_door_mount_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_door_mount_combo.set("1 - Yes")
        row += 1

        ttk.Label(form_frame, text="Panel Size Level (1-5):").grid(row=row, column=0, sticky="w", pady=4)
        self.m_panel_size_combo = ttk.Combobox(form_frame, values=["1", "2", "3", "4", "5"], width=18, state="readonly")
        self.m_panel_size_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_panel_size_combo.set("4")
        row += 1

        ttk.Label(form_frame, text="Bypass:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_bypass_combo = ttk.Combobox(form_frame, values=["With Bypass", "Without Bypass"], width=18, state="readonly")
        self.m_bypass_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_bypass_combo.set("With Bypass")
        row += 1

        ttk.Label(form_frame, text="Panel Type:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_panel_type_combo = ttk.Combobox(form_frame, values=["Indoor", "Outdoor"], width=18, state="readonly")
        self.m_panel_type_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_panel_type_combo.set("Indoor")
        row += 1

        ttk.Label(form_frame, text="Panel Class:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_panel_class_combo = ttk.Combobox(form_frame, values=["Industrial", "Domestic"], width=18, state="readonly")
        self.m_panel_class_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_panel_class_combo.set("Industrial")
        row += 1

        ttk.Label(form_frame, text="OLR Requirement:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_olr_combo = ttk.Combobox(form_frame, values=["0 - No", "1 - Yes"], width=18, state="readonly")
        self.m_olr_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_olr_combo.set("0 - No")
        row += 1

        ttk.Label(form_frame, text="Indicator Light Required:").grid(row=row, column=0, sticky="w", pady=4)
        self.m_light_combo = ttk.Combobox(form_frame, values=["0 - No", "1 - Yes"], width=18, state="readonly")
        self.m_light_combo.grid(row=row, column=1, sticky="e", pady=4)
        self.m_light_combo.set("0 - No")
        row += 1

        action_frame = ttk.Frame(scrollable_frame)
        action_frame.pack(pady=5)

        calc_btn = ttk.Button(action_frame, text="Calculate Material List & BOM", command=self.calculate_materials)
        calc_btn.pack(side="left", padx=5)

        export_btn = ttk.Button(action_frame, text="💾 Export BOM to CSV", command=self.export_bom_to_csv)
        export_btn.pack(side="left", padx=5)

        output_frame = ttk.LabelFrame(scrollable_frame, text=" Material Breakdown & BOM ", padding="10")
        output_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.output_text = tk.Text(output_frame, wrap="none", width=85, height=22, font=("Consolas", 9))

        vsb = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        hsb = ttk.Scrollbar(output_frame, orient="horizontal", command=self.output_text.xview)
        self.output_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.output_text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

    def populate_from_price_list(self):
        """Populate fields from Price List Search data."""
        if not self.price_tab_data:
            return
        
        # Clear existing data first
        self.output_text.delete("1.0", tk.END)
        
        # Copy Pump Type
        if 'pump_type' in self.price_tab_data:
            self.m_pump_type_combo.set(self.price_tab_data['pump_type'])
        
        # Copy Pump Current
        if 'pump_current' in self.price_tab_data:
            self.m_current_entry.delete(0, tk.END)
            self.m_current_entry.insert(0, str(self.price_tab_data['pump_current']))
        
        # Copy Number of Pumps
        if 'num_pumps' in self.price_tab_data:
            self.m_pumps_combo.set(self.price_tab_data['num_pumps'])
        
        # Copy Number of VFD
        if 'num_vfd' in self.price_tab_data:
            self.m_vfd_combo.set(self.price_tab_data['num_vfd'])
        
        # Copy Main Incomer (convert from Yes/No to 1 - Yes/0 - No)
        if 'main_incomer' in self.price_tab_data:
            incomer_value = self.price_tab_data['main_incomer']
            if incomer_value in ['Yes', 'yes', 'With Bypass', 'with bypass']:
                self.m_incomer_combo.set("1 - Yes")
            else:
                self.m_incomer_combo.set("0 - No")
        
        # Copy OLR Requirement (convert from Yes/No to 1 - Yes/0 - No)
        if 'olr_required' in self.price_tab_data:
            olr_value = self.price_tab_data['olr_required']
            if olr_value in ['Yes', 'yes']:
                self.m_olr_combo.set("1 - Yes")
            else:
                self.m_olr_combo.set("0 - No")
        
        # Copy Indicator Light (convert from Yes/No to 1 - Yes/0 - No)
        if 'indicator_light' in self.price_tab_data:
            light_value = self.price_tab_data['indicator_light']
            if light_value in ['Yes', 'yes']:
                self.m_light_combo.set("1 - Yes")
            else:
                self.m_light_combo.set("0 - No")
        
        # Copy Panel Size (convert from dimensions to level)
        if 'panel_size' in self.price_tab_data:
            size_mapping = {
                '400x300': '1',
                '600x400': '2', 
                '800x600': '3',
                '1000x800': '4',
                '1200x800': '5'
            }
            size_value = self.price_tab_data['panel_size']
            if size_value in size_mapping:
                self.m_panel_size_combo.set(size_mapping[size_value])
            else:
                self.m_panel_size_combo.set('4')  # Default
        
        # Copy Bypass
        if 'bypass' in self.price_tab_data:
            self.m_bypass_combo.set(self.price_tab_data['bypass'])
        
        # Copy Panel Type
        if 'panel_type' in self.price_tab_data:
            self.m_panel_type_combo.set(self.price_tab_data['panel_type'])
        
        # Copy Panel Class
        if 'panel_class' in self.price_tab_data:
            self.m_panel_class_combo.set(self.price_tab_data['panel_class'])
        
        # Show message that data has been copied
        self.output_text.insert(tk.END, "✓ Data copied from Price List Search\n")
        self.output_text.insert(tk.END, "✓ Click 'Calculate Material List & BOM' to get the cost breakdown\n")
        self.output_text.insert(tk.END, "✓ Then return to Price List Search to add the calculated price\n")

    def calculate_materials(self):
        try:
            pump_type = self.m_pump_type_combo.get()
            pump_current = float(self.m_current_entry.get().strip())
            num_pumps = int(self.m_pumps_combo.get().strip())
            num_vfd = int(self.m_vfd_combo.get().strip())
            incomer_req = 1 if "1" in self.m_incomer_combo.get() else 0
            door_mount_req = 1 if "1" in self.m_door_mount_combo.get() else 0
            panel_size_lvl = int(self.m_panel_size_combo.get().strip())
            olr_req = 1 if "1" in self.m_olr_combo.get() else 0
            light_req = 1 if "1" in self.m_light_combo.get() else 0
            bypass = self.m_bypass_combo.get()
            panel_type = self.m_panel_type_combo.get()
            panel_class = self.m_panel_class_combo.get()
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all numerical input fields contain valid values.")
            return

        pump_hp = (pump_current * 1.732 * 415 * 0.85) / 746
        total_panel_current = pump_current * num_pumps
        controller_type = "AIPCU OR HMI" if num_vfd > 0 else "DOL/STAR-DELTA"
        mcb_mccb_type = "MCCB" if total_panel_current > 63 else "MCB"
        breaker_qty = 1
        raw_breaker_rating = total_panel_current * 1.25

        fan_qty = 2 if num_vfd > 1 else (1 if num_vfd == 1 else 0)
        filter_qty = fan_qty
        endlock_qty = 4

        self.current_bom = bom_engine.generate_bom(
            controller_type, num_pumps, num_vfd, pump_hp, olr_req, light_req,
            fan_qty, filter_qty, endlock_qty, mcb_mccb_type, breaker_qty,
            raw_breaker_rating, incomer_req, door_mount_req, total_panel_current
        )

        total_material_dp = sum(item["Qty"] * item["DP"] for item in self.current_bom)
        self.current_labor_cost = 500.0 + (num_pumps * 250.0) + (panel_size_lvl * 150.0)
        self.current_grand_total = total_material_dp + self.current_labor_cost

        self.output_text.delete("1.0", tk.END)
        out = []
        
        # Display input parameters
        out.append("=" * 80)
        out.append("INPUT PARAMETERS:")
        out.append(f"  Material Company: {self.company_combo.get()}")
        out.append(f"  Pump Type: {pump_type}")
        out.append(f"  Pump Current: {pump_current} A")
        out.append(f"  Number of Pumps: {num_pumps}")
        out.append(f"  Number of VFD: {num_vfd}")
        out.append(f"  Bypass: {bypass}")
        out.append(f"  Panel Type: {panel_type}")
        out.append(f"  Panel Size Level: {panel_size_lvl}")
        out.append(f"  Panel Class: {panel_class}")
        out.append(f"  Main Incomer: {'Yes' if incomer_req else 'No'}")
        out.append(f"  OLR Requirement: {'Yes' if olr_req else 'No'}")
        out.append(f"  Indicator Light: {'Yes' if light_req else 'No'}")
        out.append("=" * 80)
        out.append("")
        
        out.append(f"{'ITEM NAME':<42} | {'QTY':<4} | {'UNIT DP (Rs.)':<13} | {'TOTAL DP (Rs.)':<13}")
        out.append("-" * 80)

        for item in self.current_bom:
            tot_dp = item["Qty"] * item["DP"]
            out.append(f"{item['Item_Name'][:40]:<42} | {item['Qty']:<4} | {item['DP']:<13,.2f} | {tot_dp:<13,.2f}")

        out.append("-" * 80)
        out.append(f"{'TOTAL MATERIAL COST (DP):':<62} Rs.{total_material_dp:,.2f}")
        out.append(f"{'LABOR & ASSEMBLY COST:':<62} Rs.{self.current_labor_cost:,.2f}")
        out.append(f"{'GRAND TOTAL ESTIMATED COST:':<62} Rs.{self.current_grand_total:,.2f}")

        self.output_text.insert(tk.END, "\n".join(out))

    def export_bom_to_csv(self):
        if not self.current_bom:
            messagebox.showwarning("Export Warning", "No BOM generated to export. Please calculate first.")
            return

        export_file = config.BOM_EXPORT_CSV
        try:
            with open(export_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Item_Name", "Category", "SUB Category", "Capacity", "Qty", "DP"])
                writer.writeheader()
                for item in self.current_bom:
                    writer.writerow(item)
            messagebox.showinfo("Export Success", f"BOM export saved successfully to:\n{export_file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export BOM CSV: {e}")
    
    def load_material_companies(self):
        """Load material companies from CSV file."""
        companies_csv = config.MATERIAL_COMPANIES_CSV
        companies = []
        
        if os.path.exists(companies_csv):
            try:
                with open(companies_csv, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    for row in reader:
                        if row and row[0].strip():
                            companies.append(row[0].strip())
            except Exception as e:
                print(f"Error loading companies: {e}")
        
        # Add default companies if none exist
        if not companies:
            companies = ["Default", "Company A", "Company B", "Company C"]
            self.save_material_companies()
        
        self.company_combo["values"] = companies
        if companies:
            self.company_combo.current(0)
    
    def save_material_companies(self):
        """Save material companies to CSV file."""
        companies_csv = config.MATERIAL_COMPANIES_CSV
        try:
            with open(companies_csv, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["company_name"])
                for company in self.company_combo["values"]:
                    writer.writerow([company])
        except Exception as e:
            messagebox.showerror("Error", f"Could not save companies: {e}")
    
    def add_material_company(self):
        """Add a new material company."""
        new_company = simpledialog.askstring(
            "Add Material Company",
            "Enter company name:",
            parent=self.winfo_toplevel()
        )
        
        if new_company and new_company.strip():
            new_company = new_company.strip()
            current_companies = list(self.company_combo["values"])
            
            if new_company in current_companies:
                messagebox.showwarning("Duplicate", "Company already exists!")
                return
            
            current_companies.append(new_company)
            self.company_combo["values"] = current_companies
            self.company_combo.set(new_company)
            self.save_material_companies()
            messagebox.showinfo("Success", f"Company '{new_company}' added successfully!")
    
    def remove_material_company(self):
        """Remove selected material company."""
        selected_company = self.company_combo.get()
        if not selected_company:
            messagebox.showwarning("Selection Required", "Please select a company to remove.")
            return
        
        if messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove '{selected_company}'?",
            parent=self.winfo_toplevel()
        ):
            current_companies = list(self.company_combo["values"])
            if selected_company in current_companies:
                current_companies.remove(selected_company)
                self.company_combo["values"] = current_companies
                
                if current_companies:
                    self.company_combo.current(0)
                else:
                    self.company_combo.set("")
                
                self.save_material_companies()
                messagebox.showinfo("Success", f"Company '{selected_company}' removed successfully!")