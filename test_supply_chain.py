"""
Test script for Supply Chain & Logistics Module
Tests the instantiation and basic functionality of all components.
"""

import tkinter as tk
from supply_chain_logistics import (
    SupplyChainLogisticsView,
    SourcingProcurementTab,
    DemandForecastingTab,
    ProductionManagementTab,
    RiskManagementTab,
    WarehousingTab,
    TransportationTab,
    OrderFulfillmentTab,
    ReverseLogisticsTab
)

def test_module_instantiation():
    """Test that all components can be instantiated."""
    print("Testing Supply Chain & Logistics Module...")
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Test main view
        print("[OK] Testing SupplyChainLogisticsView...")
        main_view = SupplyChainLogisticsView(root)
        print("[OK] SupplyChainLogisticsView instantiated successfully")
        
        # Test individual tabs
        print("[OK] Testing SourcingProcurementTab...")
        sourcing_tab = SourcingProcurementTab(root)
        print("[OK] SourcingProcurementTab instantiated successfully")
        
        print("[OK] Testing DemandForecastingTab...")
        forecasting_tab = DemandForecastingTab(root)
        print("[OK] DemandForecastingTab instantiated successfully")
        
        print("[OK] Testing ProductionManagementTab...")
        production_tab = ProductionManagementTab(root)
        print("[OK] ProductionManagementTab instantiated successfully")
        
        print("[OK] Testing RiskManagementTab...")
        risk_tab = RiskManagementTab(root)
        print("[OK] RiskManagementTab instantiated successfully")
        
        print("[OK] Testing WarehousingTab...")
        warehouse_tab = WarehousingTab(root)
        print("[OK] WarehousingTab instantiated successfully")
        
        print("[OK] Testing TransportationTab...")
        transport_tab = TransportationTab(root)
        print("[OK] TransportationTab instantiated successfully")
        
        print("[OK] Testing OrderFulfillmentTab...")
        order_tab = OrderFulfillmentTab(root)
        print("[OK] OrderFulfillmentTab instantiated successfully")
        
        print("[OK] Testing ReverseLogisticsTab...")
        returns_tab = ReverseLogisticsTab(root)
        print("[OK] ReverseLogisticsTab instantiated successfully")
        
        print("\n[SUCCESS] All components instantiated successfully!")
        print("[SUCCESS] Supply Chain & Logistics Module is ready for use.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_module_instantiation()
    exit(0 if success else 1)