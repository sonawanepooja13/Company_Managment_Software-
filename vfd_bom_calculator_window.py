"""
VFD BOM Calculator Window

This module provides a GUI window for the Multi-Pump VFD Control Panel 
sizing and Bill of Materials calculator.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from vfd_bom_calculator import VFDBOMCalculator, calculate_vfd_bom


class VFDBOMCalculatorWindow(tk.Toplevel):
    """Window for VFD BOM Calculator with input form and results display."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Auto Calculator2 - VFD BOM Calculator")
        self.geometry("900x700")
        self.resizable(True, True)
        
        # Initialize variables
        self.pump_make_var = tk.StringVar(value="texmo")
        self.pump_type_var = tk.StringVar(value="Vertical inline pump")
        self.hp_var = tk.DoubleVar(value=20.0)
        self.kw_var = tk.DoubleVar(value=15.0)
        self.num_pumps_var = tk.IntVar(value=2)
        self.num_vfds_var = tk.IntVar(value=1)
        self.multi_vfd_contactor_var = tk.StringVar(value="NO")
        self.panel_size_level_var = tk.IntVar(value=4)
        self.olr_req_var = tk.IntVar(value=0)
        self.indicator_light_req_var = tk.IntVar(value=0)
        
        self.current_results = None
        
        self.build_ui()
        self.center_window()
    
    def center_window(self):
        """Center the window on the parent window."""
        self.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        width = 900
        height = 700
        
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def build_ui(self):
        """Build the user interface."""
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
        
        # Title
        title_frame = ttk.Frame(scrollable_frame)
        title_frame.pack(fill="x", padx=15, pady=10)
        
        title = ttk.Label(title_frame, text="Multi-Pump VFD Control Panel BOM Calculator", 
                         font=("Helvetica", 14, "bold"))
        title.pack(side="left")
        
        # Input form
        input_frame = ttk.LabelFrame(scrollable_frame, text=" Input Parameters ", padding="15")
        input_frame.pack(fill="x", padx=15, pady=5)
        
        row = 0
        
        # Pump Make
        ttk.Label(input_frame, text="Pump Make:").grid(row=row, column=0, sticky="w", pady=5)
        pump_make_combo = ttk.Combobox(input_frame, textvariable=self.pump_make_var,
                                      values=["texmo", "kribs", "grundfos", "crompton", "kirloskar"],
                                      width=20, state="readonly")
        pump_make_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Pump Type
        ttk.Label(input_frame, text="Pump Type:").grid(row=row, column=0, sticky="w", pady=5)
        pump_type_combo = ttk.Combobox(input_frame, textvariable=self.pump_type_var,
                                     values=["Vertical inline pump", "Horizontal pump", "Submersible pump"],
                                     width=20, state="readonly")
        pump_type_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # HP
        ttk.Label(input_frame, text="Pump Horsepower (HP):").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.hp_var, width=20).grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # KW
        ttk.Label(input_frame, text="Pump Kilowatts (KW):").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.kw_var, width=20).grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Number of Pumps
        ttk.Label(input_frame, text="Number of Pumps:").grid(row=row, column=0, sticky="w", pady=5)
        pumps_combo = ttk.Combobox(input_frame, textvariable=self.num_pumps_var,
                                  values=[1, 2, 3, 4, 5], width=20, state="readonly")
        pumps_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Number of VFDs
        ttk.Label(input_frame, text="Number of VFDs:").grid(row=row, column=0, sticky="w", pady=5)
        vfd_combo = ttk.Combobox(input_frame, textvariable=self.num_vfds_var,
                                values=[0, 1, 2, 3, 4], width=20, state="readonly")
        vfd_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Multi-VFD Contactor
        ttk.Label(input_frame, text="Multi-VFD Contactor:").grid(row=row, column=0, sticky="w", pady=5)
        contactor_combo = ttk.Combobox(input_frame, textvariable=self.multi_vfd_contactor_var,
                                      values=["YES", "NO"], width=20, state="readonly")
        contactor_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Panel Size Level
        ttk.Label(input_frame, text="Panel Size Level (1-5):").grid(row=row, column=0, sticky="w", pady=5)
        panel_size_combo = ttk.Combobox(input_frame, textvariable=self.panel_size_level_var,
                                      values=[1, 2, 3, 4, 5], width=20, state="readonly")
        panel_size_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # OLR Requirement
        ttk.Label(input_frame, text="OLR Required:").grid(row=row, column=0, sticky="w", pady=5)
        olr_combo = ttk.Combobox(input_frame, textvariable=self.olr_req_var,
                               values=[0, 1], width=20, state="readonly")
        olr_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Indicator Light Required
        ttk.Label(input_frame, text="Indicator Light Required:").grid(row=row, column=0, sticky="w", pady=5)
        light_combo = ttk.Combobox(input_frame, textvariable=self.indicator_light_req_var,
                                 values=[0, 1], width=20, state="readonly")
        light_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Action buttons
        action_frame = ttk.Frame(scrollable_frame)
        action_frame.pack(pady=10)
        
        calculate_btn = ttk.Button(action_frame, text="Calculate BOM", command=self.calculate_bom)
        calculate_btn.pack(side="left", padx=5)
        
        clear_btn = ttk.Button(action_frame, text="Clear Results", command=self.clear_results)
        clear_btn.pack(side="left", padx=5)
        
        close_btn = ttk.Button(action_frame, text="Close", command=self.destroy)
        close_btn.pack(side="left", padx=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(scrollable_frame, text=" Calculation Results ", padding="15")
        results_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Results text area
        self.results_text = tk.Text(results_frame, wrap="word", width=80, height=25, 
                                   font=("Consolas", 10))
        
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_text.xview)
        self.results_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.results_text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
    
    def calculate_bom(self):
        """Calculate BOM using the calculator module."""
        try:
            # Get input values
            pump_make = self.pump_make_var.get().strip()
            pump_type = self.pump_type_var.get().strip()
            hp = self.hp_var.get()
            kw = self.kw_var.get()
            num_pumps = self.num_pumps_var.get()
            num_vfds = self.num_vfds_var.get()
            multi_vfd_contactor = self.multi_vfd_contactor_var.get().strip()
            panel_size_level = self.panel_size_level_var.get()
            olr_req = self.olr_req_var.get()
            indicator_light_req = self.indicator_light_req_var.get()
            
            # Validate inputs
            if hp <= 0 or kw <= 0:
                messagebox.showerror("Input Error", "HP and KW must be positive values.")
                return
            
            if num_pumps < 1:
                messagebox.showerror("Input Error", "Number of pumps must be at least 1.")
                return
            
            if panel_size_level < 1 or panel_size_level > 5:
                messagebox.showerror("Input Error", "Panel size level must be between 1 and 5.")
                return
            
            # Calculate using the calculator module
            calculator = VFDBOMCalculator(
                pump_make, pump_type, hp, kw, num_pumps, num_vfds,
                multi_vfd_contactor, panel_size_level, olr_req, indicator_light_req
            )
            
            self.current_results = calculator.get_results()
            
            # Display results
            self.display_results()
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error during calculation: {e}")
    
    def display_results(self):
        """Display the calculation results in the text area."""
        if not self.current_results:
            return
        
        self.results_text.delete("1.0", tk.END)
        
        results = self.current_results
        
        # Format the output
        output = """
=============================================
   MULTI-PUMP VFD CONTROL PANEL BOM RESULTS
=============================================

INPUT PARAMETERS:
----------------
Pump Make: {pump_make}
Pump Type: {pump_type}
Horsepower: {hp} HP
Kilowatts: {kw} KW
Number of Pumps: {num_pumps}
Number of VFDs: {num_vfds}
Multi-VFD Contactor: {multi_vfd_contactor}
Panel Size Level: {panel_size_level}
OLR Required: {olr_req}
Indicator Light Required: {indicator_light_req}

CALCULATION RESULTS:
-------------------
Model Number: {model_no}
Controller Type: {controller_type}
Fan & Filter: {fan_filter}
Starter Type: {starter_type}

CURRENT CALCULATIONS:
---------------------
Single Pump Normal Current: {normal_current:.2f} Amps
Single Pump Full Load Current: {full_load_current:.2f} Amps
{total_current_conn}

PROTECTION & BREAKERS:
----------------------
Breaker Info: {breaker_info}
Breaker Size: {breaker_size}

WIRING SPECIFICATIONS:
---------------------
Input Wire:
{input_wire}

Output Wire:
{output_wire}

CONTROL COMPONENTS:
------------------
Timer Requirement: {timer_req}
Contactor Details:
{contactor}

TERMINALS & CONNECTIONS:
-----------------------
Lugs:
{lugs}

CTS Terminal Blocks:
Input Line: {cts_input_line}
Output CTS Rating: {cts_output_cts_rating} Amps
Output CTS Qty: {cts_output_cts_qty}
Earth CTS: {cts_earth_cts}
Control CTS4U: {cts_control_cts4u}
BMS CTS4U: {cts_bms_cts4u}

MECHANICAL COMPONENTS:
---------------------
Endlock End Plate Qty: {endlock_qty}
Cable Tray: {cable_tray}
DIN Rail: {din_rail}

CONTROL & INDICATION:
---------------------
3P Selector Switch + NO + NC: {selector_switch}
Indicator Lights Qty: {indicator_qty}
Aluminium Indicator Plate: {indicator_plate}
CT Coil: {ct_coil}
Ferrule: {ferrule}

COST ESTIMATION:
---------------
Labor Cost: Rs. {labor_cost:,.2f}

=============================================
        """.format(
            pump_make=self.pump_make_var.get(),
            pump_type=self.pump_type_var.get(),
            hp=self.hp_var.get(),
            kw=self.kw_var.get(),
            num_pumps=self.num_pumps_var.get(),
            num_vfds=self.num_vfds_var.get(),
            multi_vfd_contactor=self.multi_vfd_contactor_var.get(),
            panel_size_level=self.panel_size_level_var.get(),
            olr_req=self.olr_req_var.get(),
            indicator_light_req=self.indicator_light_req_var.get(),
            model_no=results['model_no'],
            controller_type=results['controller_type'],
            fan_filter=results['fan_filter'],
            starter_type=results['starter_type'],
            normal_current=results['normal_current'],
            full_load_current=results['full_load_current'],
            total_current_conn=results['total_current_conn'],
            breaker_info=results['breaker_info'],
            breaker_size=results['breaker_size'],
            input_wire=results['input_wire'],
            output_wire=results['output_wire'],
            timer_req=results['timer_req'],
            contactor=results['contactor'],
            lugs=results['lugs'],
            cts_input_line=results['cts']['input_line'],
            cts_output_cts_rating=results['cts']['output_cts_rating'],
            cts_output_cts_qty=results['cts']['output_cts_qty'],
            cts_earth_cts=results['cts']['earth_cts'],
            cts_control_cts4u=results['cts']['control_cts4u'],
            cts_bms_cts4u=results['cts']['bms_cts4u'],
            endlock_qty=results['endlock_qty'],
            cable_tray=results['cable_tray'],
            din_rail=results['din_rail'],
            selector_switch=results['selector_switch'],
            indicator_qty=results['indicator_qty'],
            indicator_plate=results['indicator_plate'],
            ct_coil=results['ct_coil'],
            ferrule=results['ferrule'],
            labor_cost=results['labor_cost']
        )
        
        self.results_text.insert("1.0", output)
    
    def clear_results(self):
        """Clear the results text area."""
        self.results_text.delete("1.0", tk.END)
        self.current_results = None