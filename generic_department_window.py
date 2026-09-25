import tkinter as tk
from tkinter import ttk, messagebox
import rnd_engineering
import supply_chain_logistics
import qc_qa
import legal_compliance
import maintenance
import it_workspace
import warehouse_management
import accounts_finance

class GenericDepartmentWindow:
    """Handler for generic department views and placeholders."""
    def __init__(self, main_app):
        self.main_app = main_app

    def show_generic_department_view(self, dept_name):
        permission_map = {
            "Purchase / Procurement": "allow_purchase",
            "Maintenance": "allow_maintenance",
            "R&D / Engineering": "allow_rnd",
            "IT": "allow_it",
            "Information Technology": "allow_it",
            "Legal & Compliance": "allow_legal",
            "Administration": "allow_admin_dept",
            "Supply Chain / Logistics": "allow_supply_chain",
            "Customer Service": "allow_customer_service",
            "Project Management / Professional Services": "allow_project_management",
            "Quality Control (QC) / Quality Assurance (QA)": "allow_qc_qa",
            "Asset Management / Fixed Assets": "allow_asset_management",
            "Environment, Health, and Safety (EHS) / Risk Management": "allow_ehs",
            "EHS / Risk Management": "allow_ehs",
            "Point of Sale (POS) / E-Commerce": "allow_pos_ecommerce",
            "POS / E-Commerce": "allow_pos_ecommerce",
        }
        required_permission = permission_map.get(dept_name)
        if required_permission and not self.main_app.user_has_permission(required_permission, False):
            messagebox.showwarning("Access Denied", f"You do not have permission to open the {dept_name} module.", parent=self.main_app.root)
            return

        try:
            self.main_app.clear_workspace()
            self.main_app.create_back_header(f"{dept_name} Module", self.main_app.build_main_dashboard)

            if "Purchase" in dept_name or "Procurement" in dept_name:
                accounts_panel = accounts_finance.AccountsFinanceView(
                    self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
                )
                accounts_panel.pack(fill="both", expand=True)

            elif "Project Management" in dept_name or "Professional Services" in dept_name:
                try:
                    import project_management
                    pm_panel = project_management.ProjectManagementView(self.main_app.content_frame, user_data=self.main_app.user_data)
                    pm_panel.pack(fill="both", expand=True)
                except Exception as pm_e:
                    messagebox.showerror("Error Loading Module", f"Could not load Project Management:\n{pm_e}", parent=self.main_app.root)

            elif "R&D" in dept_name or "Engineering" in dept_name:
                rnd_panel = rnd_engineering.RnDEngineeringView(
                    self.main_app.content_frame, user_data=self.main_app.user_data
                )
                rnd_panel.pack(fill="both", expand=True, padx=0, pady=0)

            elif "Supply Chain" in dept_name:
                supply_chain_panel = supply_chain_logistics.SupplyChainLogisticsView(
                    self.main_app.content_frame, user_data=self.main_app.user_data
                )
                supply_chain_panel.pack(fill="both", expand=True)
            elif "Quality Control" in dept_name or "Quality Assurance" in dept_name:
                quality_panel = qc_qa.QCQAView(self.main_app.content_frame, user_data=self.main_app.user_data)
                quality_panel.pack(fill="both", expand=True)
            elif "Legal" in dept_name:
                legal_panel = legal_compliance.LegalComplianceView(
                    self.main_app.content_frame, user_data=self.main_app.user_data
                )
                legal_panel.pack(fill="both", expand=True)
            elif "Maintenance" in dept_name:
                maintenance_panel = maintenance.MaintenanceView(
                    self.main_app.content_frame, user_data=self.main_app.user_data
                )
                maintenance_panel.pack(fill="both", expand=True)
            elif "IT" in dept_name or "Information Technology" in dept_name:
                it_panel = it_workspace.ITWorkspaceView(
                    self.main_app.content_frame, user_data=self.main_app.user_data
                )
                it_panel.pack(fill="both", expand=True)
            elif "Stores" in dept_name or "Warehouse" in dept_name:
                warehouse_panel = warehouse_management.WarehouseManagementView(
                    self.main_app.content_frame, user_data=self.main_app.user_data
                )
                warehouse_panel.pack(fill="both", expand=True)
            else:
                dept_frame = ttk.Frame(self.main_app.content_frame, padding=30)
                dept_frame.pack(fill="both", expand=True)

                ttk.Label(
                    dept_frame,
                    text=f"{dept_name} Workspace",
                    font=("Helvetica", 14, "bold"),
                ).pack(pady=(0, 15))

                ttk.Label(
                    dept_frame,
                    text=f"Welcome to the {dept_name} dashboard management system.",
                    font=("Helvetica", 11),
                ).pack(pady=(0, 20))

                info_box = ttk.LabelFrame(dept_frame, text=" Department Status ", padding=15)
                info_box.pack(fill="x", padx=10, pady=10)

                ttk.Label(info_box, text="• Module Active: Yes").pack(anchor="w", pady=2)
                ttk.Label(info_box, text=f"• User Role Access: {self.main_app.user_data.get('role', 'User')}").pack(anchor="w", pady=2)
                ttk.Label(info_box, text=f"• Current Active User: {self.main_app.user_data.get('full_name', self.main_app.user_data.get('username'))}").pack(anchor="w", pady=2)
        except Exception as e:
            messagebox.showerror(
                "Error Loading View",
                f"Could not load {dept_name} module:\n{e}",
            )
