import tkinter as tk
from tkinter import ttk

HELP_LIBRARY = {
    "General": {
        "how_to_use": [
            "Use the dashboard to open the module related to your work.",
            "Complete the required fields and save your changes before leaving the screen.",
            "If you are unsure, use the Help button for the current mode for task-specific guidance.",
        ],
        "inside_window": [
            "Main workspace dashboard and module access buttons.",
            "User role and permission-controlled navigation.",
            "Back button to return to the menu screen.",
        ],
    },
    "Dashboard": {
        "how_to_use": [
            "Select the module that matches your current task.",
            "Only your permitted modules will be available.",
            "Use the back button to return to the home dashboard anytime.",
        ],
        "inside_window": [
            "Welcome text and user information.",
            "Module tiles for allowed departments and workflows.",
            "Admin and user access controls.",
        ],
    },
    "Production Process": {
        "how_to_use": [
            "Open the Production Process module to track process records and production work.",
            "Enter or update production details, quantities, and process status in the form.",
            "Save the record after updating the stage or operation before moving to the next step.",
        ],
        "inside_window": [
            "Production record form and process data.",
            "Production stages and operational status tracking.",
            "Output and process updates relevant to the selected production run.",
        ],
    },
    "Sales & Marketing": {
        "how_to_use": [
            "Use Sales & Marketing to manage pricing, material details, and customer records.",
            "Open the relevant tab for price list, material estimates, or CRM activity.",
            "Keep customer and quotation information updated for better sales follow-up.",
        ],
        "inside_window": [
            "Price list search and quotation data.",
            "Material and labor estimate tools.",
            "Customer CRM and lead management section.",
        ],
    },
    "R&D / Engineering": {
        "how_to_use": [
            "Use this area for product development, engineering records, tasks, and sprint planning.",
            "Create product development entries, assign tasks, and track progress through the lifecycle.",
            "Use the date selectors and task controls to keep engineering work current and traceable.",
        ],
        "inside_window": [
            "Product development and engineering records.",
            "Task and sprint tracking sections.",
            "Prototype, BOM, ECO, and technical development controls.",
        ],
    },
    "Quality Control (QC) / Quality Assurance (QA)": {
        "how_to_use": [
            "Create inspection lots after goods receipt to start quality checks.",
            "Upload or record CoA details and compare them with the technical specification.",
            "Raise an NCR when a lot fails inspection and select the correct disposition.",
            "Only accepted or approved lots should be released to inventory or paid for.",
        ],
        "inside_window": [
            "Inspection lot creation and status tracking.",
            "CoA capture and verification logic.",
            "NCR reporting and disposition workflow.",
            "Supplier quality scorecard summary.",
        ],
    },
    "User Account & Tab Access Control": {
        "how_to_use": [
            "Select the user account to update from the dropdown list.",
            "Fill in the user profile and assign required modules or tab access.",
            "Use Open All, Close All, or Default to quickly configure permissions.",
            "Save the record to apply permissions permanently.",
        ],
        "inside_window": [
            "Selected user account details.",
            "Role and password controls.",
            "Module and tab access checklist.",
            "Save, delete, and permission reset actions.",
        ],
    },
    "Purchase / Procurement": {
        "how_to_use": [
            "Create requisitions and purchase orders based on business needs.",
            "Track approvals, warehouse receiving, and invoice matching in the procurement flow.",
            "Use the goods receipt and invoice stages together to complete three-way matching.",
        ],
        "inside_window": [
            "Vendor and supplier records.",
            "Requisition, purchase order, and approvals.",
            "Goods receipt, matching, and invoice review controls.",
        ],
    },
    "Maintenance": {
        "how_to_use": [
            "Create assets, log work orders, and schedule preventive maintenance.",
            "Track equipment status, maintenance history, and service vendors.",
            "Use the maintenance dashboard to keep critical assets operational.",
        ],
        "inside_window": [
            "Asset hierarchy and maintenance records.",
            "Work order and preventive maintenance schedule.",
            "Spare parts, vendor, and compliance tracking.",
        ],
    },
    "HR (Human Resources)": {
        "how_to_use": [
            "Use HR to manage employee details, attendance, and related workplace records.",
            "Enter employee information and related HR actions in the main form.",
            "Review and update employee information on a regular basis.",
        ],
        "inside_window": [
            "Employee master data.",
            "HR form and employee records.",
            "Role-based employee management tasks.",
        ],
    },
    "IT": {
        "how_to_use": [
            "Use IT workspace to manage provisioning, security, helpdesk, assets, and IAM.",
            "Create and track IT support requests and system access changes.",
            "Review security or asset information as part of daily IT operations.",
        ],
        "inside_window": [
            "Provisioning and access management tools.",
            "Security, helpdesk, assets, and IAM modules.",
            "Operational overview for enterprise IT support.",
        ],
    },
    "Customer Service": {
        "how_to_use": [
            "Log customer issues, service events, and required material work.",
            "Track the actual problem and the service action taken for each customer.",
            "Save or update service records to keep support activity visible.",
        ],
        "inside_window": [
            "Customer support record entry.",
            "Service type, problem details, and material action data.",
            "Customer service history and reporting view.",
        ],
    },
    "Legal & Compliance": {
        "how_to_use": [
            "Use this module to record legal documents, compliance work, and checklists.",
            "Update formal records and review critical compliance actions on time.",
            "Keep all governance documents organized and traceable.",
        ],
        "inside_window": [
            "Compliance and legal documentation records.",
            "Document management and policy tracking.",
            "Governance related tasks and review tracking.",
        ],
    },
    "Administration": {
        "how_to_use": [
            "Use Administration to manage system settings and core operational controls.",
            "Review and apply access and configuration settings from the administration pages.",
            "Use this area to manage company-level operational defaults.",
        ],
        "inside_window": [
            "Admin configuration area.",
            "System settings and department controls.",
            "Operational management and user setup screens.",
        ],
    },
    "Supply Chain / Logistics": {
        "how_to_use": [
            "Manage supply chain movement, shipments, inventory flow, and logistics records.",
            "Monitor stock movement and track incoming or outgoing logistics actions.",
            "Use the module to keep the supply chain flow visible and organized.",
        ],
        "inside_window": [
            "Logistics tracking views.",
            "Inventory movement and supply chain records.",
            "Operational shipping and warehouse flow data.",
        ],
    },
    "Project Management / Professional Services": {
        "how_to_use": [
            "Track client projects, internal initiatives, and professional service work items.",
            "Create project records and update their delivery status as work progresses.",
            "Keep billable and time-based work organized and reviewable.",
        ],
        "inside_window": [
            "Project work list and progress details.",
            "Service and client delivery tracking.",
            "Project task and milestone information.",
        ],
    },
    "Asset Management / Fixed Assets": {
        "how_to_use": [
            "Use this area to record machines, vehicles, tools, and fixed assets.",
            "Track asset assignment, service history, depreciation, and usage lifecycle.",
            "Keep asset-related records current for operations and finance reporting.",
        ],
        "inside_window": [
            "Asset registry and asset lifecycle records.",
            "Service, maintenance, and depreciation tracking.",
            "Hardware and capital asset details.",
        ],
    },
    "Environment, Health, and Safety (EHS) / Risk Management": {
        "how_to_use": [
            "Use EHS/Risk Management to log hazards, incidents, and required safety actions.",
            "Track control measures, reporting requirements, and risk mitigation responses.",
            "Review safety logs and compliance-related information regularly.",
        ],
        "inside_window": [
            "Safety and risk tracking information.",
            "Incident, hazard, and compliance data.",
            "Mitigation and corrective action records.",
        ],
    },
    "Point of Sale (POS) / E-Commerce": {
        "how_to_use": [
            "Use this module to manage direct selling and online sales activities.",
            "Review sales records, channel performance, and transaction data.",
            "Keep point of sale and e-commerce activities aligned with current operations.",
        ],
        "inside_window": [
            "Sales channel and POS transaction records.",
            "E-commerce and retail operational information.",
            "Sales activity and channel reporting data.",
        ],
    },
}

TOPIC_ALIASES = {
    "Production Module": "Production Process",
    "Sales & Marketing Module": "Sales & Marketing",
    "Human Resources": "HR (Human Resources)",
    "Human Resources Module": "HR (Human Resources)",
    "Customer Service Module": "Customer Service",
    "Administration Settings & Access Controls": "User Account & Tab Access Control",
    "User Account & Module Access Control Panel": "User Account & Tab Access Control",
    "Module & Tab Access Permissions": "User Account & Tab Access Control",
    "Purchase / Procurement Module": "Purchase / Procurement",
    "Maintenance Module": "Maintenance",
    "Quality Control (QC) / Quality Assurance (QA) Module": "Quality Control (QC) / Quality Assurance (QA)",
    "Project Management / Professional Services Module": "Project Management / Professional Services",
    "Asset Management / Fixed Assets Module": "Asset Management / Fixed Assets",
    "Environment, Health, and Safety (EHS) / Risk Management Module": "Environment, Health, and Safety (EHS) / Risk Management",
    "Point of Sale (POS) / E-Commerce Module": "Point of Sale (POS) / E-Commerce",
    "IT Module": "IT",
    "Information Technology": "IT",
    "Legal & Compliance Module": "Legal & Compliance",
    "Administration Module": "Administration",
    "Supply Chain / Logistics Module": "Supply Chain / Logistics",
    "R&D / Engineering Module": "R&D / Engineering",
    "Quality Control (QC) / Quality Assurance (QA)": "Quality Control (QC) / Quality Assurance (QA)",
    "Project Management / Professional Services": "Project Management / Professional Services",
    "Asset Management / Fixed Assets": "Asset Management / Fixed Assets",
    "Environment, Health, and Safety (EHS) / Risk Management": "Environment, Health, and Safety (EHS) / Risk Management",
    "Point of Sale (POS) / E-Commerce": "Point of Sale (POS) / E-Commerce",
}


def normalize_topic(topic_name):
    topic = (topic_name or "General").strip()
    if not topic:
        return "General"
    return TOPIC_ALIASES.get(topic, topic)


def get_help_content(topic_name):
    topic = normalize_topic(topic_name)
    return HELP_LIBRARY.get(topic, HELP_LIBRARY["General"])


class HelpWindow(tk.Toplevel):
    def __init__(self, parent, topic_name="General"):
        topic = normalize_topic(topic_name)
        super().__init__(parent)
        self.title(f"Help - {topic}")
        self.geometry("700x520")
        self.minsize(620, 420)
        self.transient(parent)
        self.grab_set()

        content = get_help_content(topic)

        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text=f"{topic} Help",
            font=("Helvetica", 14, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        how_to_use = ttk.LabelFrame(main, text=" 1. How to Use ", padding=10)
        how_to_use.pack(fill="x", pady=(0, 10))

        for text in content["how_to_use"]:
            ttk.Label(how_to_use, text="• " + text, justify="left", wraplength=620).pack(anchor="w", pady=3)

        inside_window = ttk.LabelFrame(main, text=" 2. What Is Inside This Window ", padding=10)
        inside_window.pack(fill="both", expand=True)

        for text in content["inside_window"]:
            ttk.Label(inside_window, text="• " + text, justify="left", wraplength=620).pack(anchor="w", pady=3)

        ttk.Button(main, text="Close", command=self.destroy).pack(anchor="e", pady=(12, 0))


def open_help_window(parent, topic_name="General"):
    return HelpWindow(parent, topic_name)
