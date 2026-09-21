import tkinter as tk
from tkinter import ttk, messagebox
import accounts_finance
from outward_window import OutwardWindow
from vendor_registration import VendorRegistrationWindow

class AccountsFinanceWindow:
    """Router for Accounts & Finance module views."""
    def __init__(self, main_app):
        self.main_app = main_app

    def show_accounts_finance_view(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Accounts & Finance.", parent=self.main_app.root)
            return
        try:
            self.main_app._accounts_return_view = self.show_accounts_finance_view
            self.main_app.clear_workspace()
            self.main_app.create_back_header("Accounts & Finance Module", self.main_app.build_main_dashboard, "⬅ Back to Dashboard")
            accounts_finance.AccountsFinanceView(
                self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
            ).pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Error Loading View", f"Could not load Accounts & Finance module:\n{e}")

    def show_purchase_procurement_view(self):
        if not (self.main_app.user_has_permission("allow_purchase", False) or self.main_app.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open Purchase / Procurement.", parent=self.main_app.root)
            return
        try:
            self.main_app._accounts_return_view = self.show_purchase_procurement_view
            self.main_app.clear_workspace()
            self.main_app.create_back_header("Purchase / Procurement Module", self.main_app.build_main_dashboard, "⬅ Back to Dashboard")
            accounts_finance.PurchaseProcurementView(
                self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
            ).pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Error Loading View", f"Could not load Purchase / Procurement module:\n{e}")

    def show_inward_entry_page(self):
        if not (self.main_app.user_has_permission("allow_inward_entry", False) or self.main_app.user_has_permission("allow_purchase", False) or self.main_app.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open the New Inward Invoice window.", parent=self.main_app.root)
            return
        parent_view = getattr(self.main_app, "_accounts_return_view", self.show_accounts_finance_view)
        self.main_app.clear_workspace()
        self.main_app.create_back_header("New Inward Invoice", parent_view, "⬅ Back to Accounts & Finance")
        accounts_finance.InwardEntryDialog(self.main_app.content_frame, parent_view,
                                            parent_view,
                                            lambda: self.show_vendor_registration_page(self.show_inward_entry_page)).pack(fill="both", expand=True, padx=12, pady=12)

    def show_outward_document_page(self):
        if not (self.main_app.user_has_permission("allow_outward_document", False) or self.main_app.user_has_permission("allow_purchase", False) or self.main_app.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open the New Outward Document window.", parent=self.main_app.root)
            return
        parent_view = getattr(self.main_app, "_accounts_return_view", self.show_accounts_finance_view)
        self.main_app.clear_workspace()
        self.main_app.create_back_header("New Outward Document", parent_view, "⬅ Back to Accounts & Finance")
        OutwardWindow(self.main_app.content_frame, on_complete=parent_view).pack(fill="both", expand=True, padx=12, pady=12)

    def show_vendor_registration_page(self, return_to=None):
        if not (self.main_app.user_has_permission("allow_vendor_registration", False) or self.main_app.user_has_permission("allow_purchase", False) or self.main_app.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open Vendor Registration.", parent=self.main_app.root)
            return
        parent_view = getattr(self.main_app, "_accounts_return_view", self.show_accounts_finance_view)
        return_to = return_to or parent_view
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Vendor Registration", return_to, "⬅ Back to Previous Page")
        VendorRegistrationWindow(self.main_app.content_frame, on_complete=return_to).pack(fill="both", expand=True, padx=12, pady=12)

    def show_cheque_details_page(self):
        if not (self.main_app.user_has_permission("allow_cheque_details", False) or self.main_app.user_has_permission("allow_purchase", False) or self.main_app.user_has_permission("allow_accounts", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open Cheque Details.", parent=self.main_app.root)
            return
        parent_view = getattr(self.main_app, "_accounts_return_view", self.show_accounts_finance_view)
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Cheque Details", parent_view, "⬅ Back to Accounts & Finance")
        accounts_finance.ChequeDetailsWindow(self.main_app.content_frame, on_complete=parent_view).pack(fill="both", expand=True, padx=12, pady=12)

    def show_sales_income_page(self):
        if not (self.main_app.user_has_permission("allow_accounts", False) or self.main_app.user_has_permission("allow_sales", False)):
            messagebox.showwarning("Access Denied", "You do not have permission to open Sales / Income.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Sales / Income", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.SalesIncomeView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)

    def show_expenses_page(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Expenses.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Expenses", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.ExpensesView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)

    def show_bank_cash_page(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Bank & Cash.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Bank & Cash", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.BankCashView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)

    def show_accounts_receivable_page(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Accounts Receivable.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Accounts Receivable", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.AccountsReceivableView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)

    def show_accounts_payable_page(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Accounts Payable.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Accounts Payable", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.AccountsPayableView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)

    def show_inventory_page(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Inventory / Stock.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Inventory / Stock", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.InventoryStockView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)

    def show_employee_salary_page(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Employee Salary.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Employee Salary", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.EmployeeSalaryView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)

    def show_gst_tax_page(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open GST & Tax.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("GST & Tax", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.GSTTaxView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)

    def show_financial_reports_page(self):
        if not self.main_app.user_has_permission("allow_accounts", False):
            messagebox.showwarning("Access Denied", "You do not have permission to open Financial Reports.", parent=self.main_app.root)
            return
        self.main_app.clear_workspace()
        self.main_app.create_back_header("Financial Reports", self.show_accounts_finance_view, "⬅ Back to Accounts & Finance")
        accounts_finance.FinancialReportsView(
            self.main_app.content_frame, user_data=self.main_app.user_data, navigator=self.main_app
        ).pack(fill="both", expand=True)
