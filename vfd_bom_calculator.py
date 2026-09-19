"""
Multi-Pump VFD Control Panel Sizing and Bill of Materials (BOM) Calculator

This module provides calculation functions for determining electrical components,
wiring specifications, and material requirements for VFD-based pump control panels.
"""


class VFDBOMCalculator:
    """Calculator for Multi-Pump VFD Control Panel BOM and sizing."""
    
    def __init__(self, pump_make, pump_type, hp, kw, num_pumps, num_vfds, 
                 multi_vfd_contactor, panel_size_level, olr_req, indicator_light_req):
        """
        Initialize calculator with input parameters.
        
        Args:
            pump_make (str): Pump manufacturer (e.g., "texmo")
            pump_type (str): Pump type (e.g., "Vertical inline pump")
            hp (float): Pump Horsepower
            kw (float): Pump Kilowatts
            num_pumps (int): Number of pumps
            num_vfds (int): Number of VFDs
            multi_vfd_contactor (str): "YES" or "NO" for multi-VFD contactor
            panel_size_level (int): Panel size tier level (1-5)
            olr_req (int): Overload relay required (1 or 0)
            indicator_light_req (int): Indicator light required (1 or 0)
        """
        self.pump_make = pump_make
        self.pump_type = pump_type
        self.hp = hp
        self.kw = kw
        self.num_pumps = num_pumps
        self.num_vfds = num_vfds
        self.multi_vfd_contactor = multi_vfd_contactor
        self.panel_size_level = panel_size_level
        self.olr_req = olr_req
        self.indicator_light_req = indicator_light_req
        
        # Calculate all values
        self.results = self.calculate_all()
    
    def calculate_all(self):
        """Calculate all BOM parameters and return results dictionary."""
        results = {
            'model_no': self.calculate_model_no(),
            'controller_type': self.calculate_controller_type(),
            'fan_filter': self.calculate_fan_filter(),
            'starter_type': self.calculate_starter_type(),
            'normal_current': self.calculate_normal_current(),
            'full_load_current': self.calculate_full_load_current(),
            'total_current_conn': self.calculate_total_current_conn(),
            'breaker_info': self.calculate_breaker_info(),
            'breaker_size': self.calculate_breaker_size(),
            'input_wire': self.calculate_input_wire(),
            'output_wire': self.calculate_output_wire(),
            'timer_req': self.calculate_timer_req(),
            'contactor': self.calculate_contactor(),
            'lugs': self.calculate_lugs(),
            'cts': self.calculate_cts(),
            'endlock_qty': self.calculate_endlock_qty(),
            'cable_tray': self.calculate_cable_tray(),
            'din_rail': self.calculate_din_rail(),
            'selector_switch': self.calculate_selector_switch(),
            'indicator_qty': self.calculate_indicator_qty(),
            'indicator_plate': self.calculate_indicator_plate(),
            'ct_coil': self.calculate_ct_coil(),
            'ferrule': self.calculate_ferrule(),
            'labor_cost': self.calculate_labor_cost()
        }
        return results
    
    def calculate_model_no(self):
        """Calculate model number."""
        return f"{self.hp}{self.num_pumps}{self.num_vfds}{self.panel_size_level}{self.indicator_light_req}"
    
    def calculate_controller_type(self):
        """Calculate controller type."""
        return "AIPCU OR HMI" if self.num_vfds > 0 else "DLC"
    
    def calculate_fan_filter(self):
        """Calculate fan and filter requirements."""
        if self.num_vfds > 0:
            fan_qty = 2 if self.num_vfds > 1 else 1
            filter_qty = 4 if self.num_vfds > 1 else 2
            return f"FAN={fan_qty}, FILTER={filter_qty}"
        return "O"
    
    def calculate_starter_type(self):
        """Calculate starter type."""
        return "S/D" if self.hp > 7.5 else "DOL"
    
    def calculate_normal_current(self):
        """Calculate single pump normal current."""
        return self.hp * 1.5
    
    def calculate_full_load_current(self):
        """Calculate single pump full load current."""
        return self.hp * 2.0
    
    def calculate_total_current_conn(self):
        """Calculate total panel current and input connection."""
        total_current = self.hp * self.num_pumps * 2
        input_conn = "BUS BAR" if total_current > 40 else "CTS"
        return f"Total Panel current = {total_current}Amp\n{input_conn}"
    
    def calculate_breaker_info(self):
        """Calculate MCB/MCCB requirement and quantity."""
        breaker_type = "MCCB" if (self.hp * 2.7) > 63 else "MCB"
        breaker_qty = self.num_vfds if self.num_vfds > 1 else (self.num_pumps + self.num_vfds)
        return f"{breaker_type} , {breaker_qty}"
    
    def calculate_breaker_size(self):
        """Calculate MCB/MCCB rating size."""
        if (self.hp * 2.7) < 63:
            return self.hp * 3
        return f"MCCB = {self.hp * 3}"
    
    def calculate_input_wire(self):
        """Calculate input wire specification."""
        total_current = self.hp * self.num_pumps * 2
        wire_sq = self.hp * 2 / 5
        
        if total_current > 40:
            wire_len = self.panel_size_level * 1.5
            return f"BUSBAR & individual wire ={wire_len} meter\n Wire ={wire_sq}Sq Abouv"
        else:
            wire_len = self.panel_size_level * 3
            return f"Total wire required={wire_len}meter\n Wire ={wire_sq}Sq Abouv"
    
    def calculate_output_wire(self):
        """Calculate output wire specification."""
        if self.hp > 7.5 and self.num_vfds < 2:
            wire_len = self.panel_size_level * self.num_pumps * 3
            wire_sq = self.hp / 5
            return f"S/D & individual wire ={wire_len} meter\n Wire ={wire_sq}Sq Abouv"
        else:
            wire_len = (self.panel_size_level * 2 * self.num_pumps) if self.num_vfds > 1 else (self.panel_size_level * 3 * self.num_pumps)
            wire_sq = self.hp * 2 / 5
            return f"Dol wire required={wire_len}meter\n Wire ={wire_sq}Sq Abouv"
    
    def calculate_timer_req(self):
        """Calculate timer requirement."""
        if self.hp > 7.5:
            if self.num_vfds > 1:
                return "Not Required"
            return f"Required={self.num_pumps}"
        return "Not Required"
    
    def calculate_contactor(self):
        """Calculate contactor details."""
        if self.num_vfds > 1:
            return "Contoctor Not Required"
        elif self.hp > 7.5:
            delta_amp = self.hp * 1.5
            delta_qty = (self.num_pumps * 2) + (self.num_vfds * 2 * self.num_pumps)
            star_amp = self.hp
            star_qty = self.num_pumps
            return f"S/D Contoctor\n DELTA={delta_amp}Amp Qty={delta_qty}\n STAR={star_amp}Amp Qty={star_qty}"
        else:
            dol_amp = self.hp * 2.2
            dol_qty = self.num_pumps * 2
            return f"DOL Contactor={dol_amp}Amp Qty={dol_qty}"
    
    def calculate_lugs(self):
        """Calculate lugs specification."""
        lug_type = "U OR O LUGH FOR HEAVY LOAD" if (self.hp * 2) > 63 else "PIN TYPE WIRE"
        size_1 = self.hp * 2 / 5
        qty_1 = (self.num_pumps + self.num_vfds) * 8
        
        if self.hp > 7.5:
            size_2 = self.hp / 5
            qty_2 = ((self.num_pumps * 2) + (self.num_vfds * 2 * self.num_pumps) + self.num_pumps) * 8
        else:
            size_2 = self.hp * 2 / 5
            qty_2 = self.num_pumps * 2 * 8
        
        return f"{lug_type}\nsize {size_1}->{qty_1} Qty\nSize {size_2}->{qty_2} Qty"
    
    def calculate_cts(self):
        """Calculate CTS terminal blocks."""
        input_line = "BUSBAR & " if (self.hp * self.num_pumps * 2) > 40 else f"Input CTS ={(self.hp * self.num_pumps * 2 / 5) * 2}"
        
        output_cts_rating = (self.hp / 5 * 2) if (self.hp > 7.5 and self.num_vfds < 2) else (self.hp * 2 / 5 * 2)
        output_cts_qty = self.num_pumps * 6 if (self.hp > 7.5 and self.num_vfds < 2) else self.num_pumps * 3
        
        earth_cts = self.num_pumps
        control_cts4u = (self.num_pumps * 2) + 4
        bms_cts4u = 3
        
        return {
            'input_line': input_line,
            'output_cts_rating': output_cts_rating,
            'output_cts_qty': output_cts_qty,
            'earth_cts': earth_cts,
            'control_cts4u': control_cts4u,
            'bms_cts4u': bms_cts4u
        }
    
    def calculate_endlock_qty(self):
        """Calculate endlock end plate quantity."""
        return 2 + (self.num_pumps * 2) + self.num_pumps + 4
    
    def calculate_cable_tray(self):
        """Calculate cable tray quantity."""
        return self.num_pumps * 2 if self.hp > 7.5 else self.num_pumps
    
    def calculate_din_rail(self):
        """Calculate DIN rail quantity."""
        return self.num_pumps if self.hp > 7.5 else self.num_pumps / 2
    
    def calculate_selector_switch(self):
        """Calculate 3P selector switch + NO + NC."""
        return f"{self.num_pumps}, {self.num_pumps * 2}, {self.num_pumps if self.num_vfds > 0 else 0}"
    
    def calculate_indicator_qty(self):
        """Calculate indicator lights quantity."""
        base_qty = 3
        pump_addition = 0 if self.num_vfds > 1 else self.num_pumps
        olr_addition = self.num_pumps * self.olr_req
        vfd_addition = self.num_vfds * self.num_pumps
        vfd_base = self.num_vfds
        
        return self.indicator_light_req * (base_qty + pump_addition + olr_addition + vfd_addition + vfd_base)
    
    def calculate_indicator_plate(self):
        """Calculate aluminium indicator plate quantity."""
        indicator_qty = self.calculate_indicator_qty()
        return indicator_qty + self.num_pumps
    
    def calculate_ct_coil(self):
        """Calculate CT coil specification."""
        prefix = "3hole=" if self.num_vfds > 0 else "2hole="
        return f"{prefix}{self.num_pumps}"
    
    def calculate_ferrule(self):
        """Calculate ferrule quantity."""
        return self.num_pumps * 2 if self.hp > 7.5 else self.num_pumps
    
    def calculate_labor_cost(self):
        """Calculate labor cost."""
        if self.hp > 7.5:
            return ((self.num_pumps * 5) * 400) + (self.num_vfds * 600)
        return ((self.num_pumps * 2) * 400) + (self.num_vfds * 600)
    
    def get_results(self):
        """Return all calculation results."""
        return self.results
    
    def get_summary(self):
        """Return a formatted summary of key results."""
        return f"""
VFD BOM Calculator Results:
==========================
Model Number: {self.results['model_no']}
Controller Type: {self.results['controller_type']}
Starter Type: {self.results['starter_type']}
Total Current: {self.results['total_current_conn']}
Breaker Info: {self.results['breaker_info']}
Breaker Size: {self.results['breaker_size']}
Input Wire: {self.results['input_wire']}
Output Wire: {self.results['output_wire']}
Timer: {self.results['timer_req']}
Contactor: {self.results['contactor']}
Labor Cost: {self.results['labor_cost']}
"""


def calculate_vfd_bom(pump_make, pump_type, hp, kw, num_pumps, num_vfds, 
                     multi_vfd_contactor, panel_size_level, olr_req, indicator_light_req):
    """
    Convenience function to calculate VFD BOM without creating class instance.
    
    Args:
        pump_make (str): Pump manufacturer
        pump_type (str): Pump type
        hp (float): Pump Horsepower
        kw (float): Pump Kilowatts
        num_pumps (int): Number of pumps
        num_vfds (int): Number of VFDs
        multi_vfd_contactor (str): Multi-VFD contactor ("YES" or "NO")
        panel_size_level (int): Panel size level (1-5)
        olr_req (int): Overload relay required (1 or 0)
        indicator_light_req (int): Indicator light required (1 or 0)
    
    Returns:
        dict: Dictionary containing all calculated BOM parameters
    """
    calculator = VFDBOMCalculator(
        pump_make, pump_type, hp, kw, num_pumps, num_vfds,
        multi_vfd_contactor, panel_size_level, olr_req, indicator_light_req
    )
    return calculator.get_results()