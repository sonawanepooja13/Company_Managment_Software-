"""
Test script for Company Maintenance Module
Tests the instantiation and basic functionality of all components.
"""

import tkinter as tk
from maintenance import (
    MaintenanceView,
    AssetHierarchyTab,
    WorkOrderManagementTab,
    PreventiveMaintenanceTab,
    SparePartsInventoryTab,
    ComplianceSafetyTab,
    MaintenanceVendorsTab,
    IoTIntegrationTab
)

def test_module_instantiation():
    """Test that all components can be instantiated."""
    print("Testing Company Maintenance Module...")
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Test main view
        print("[OK] Testing MaintenanceView...")
        main_view = MaintenanceView(root)
        print("[OK] MaintenanceView instantiated successfully")
        
        # Test individual tabs
        print("[OK] Testing AssetHierarchyTab...")
        asset_tab = AssetHierarchyTab(root)
        print("[OK] AssetHierarchyTab instantiated successfully")
        
        print("[OK] Testing WorkOrderManagementTab...")
        work_order_tab = WorkOrderManagementTab(root)
        print("[OK] WorkOrderManagementTab instantiated successfully")
        
        print("[OK] Testing PreventiveMaintenanceTab...")
        preventive_tab = PreventiveMaintenanceTab(root)
        print("[OK] PreventiveMaintenanceTab instantiated successfully")
        
        print("[OK] Testing SparePartsInventoryTab...")
        inventory_tab = SparePartsInventoryTab(root)
        print("[OK] SparePartsInventoryTab instantiated successfully")
        
        print("[OK] Testing ComplianceSafetyTab...")
        compliance_tab = ComplianceSafetyTab(root)
        print("[OK] ComplianceSafetyTab instantiated successfully")
        
        print("[OK] Testing MaintenanceVendorsTab...")
        vendors_tab = MaintenanceVendorsTab(root)
        print("[OK] MaintenanceVendorsTab instantiated successfully")
        
        print("[OK] Testing IoTIntegrationTab...")
        iot_tab = IoTIntegrationTab(root)
        print("[OK] IoTIntegrationTab instantiated successfully")
        
        print("\n[SUCCESS] All components instantiated successfully!")
        print("[SUCCESS] Company Maintenance Module is ready for use.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_module_instantiation()
    exit(0 if success else 1)