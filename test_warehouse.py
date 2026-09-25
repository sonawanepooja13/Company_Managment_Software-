"""
Test script for Warehouse Management Module
Tests the instantiation and basic functionality of all components.
"""

import tkinter as tk
from warehouse_management import (
    WarehouseManagementView,
    ItemMasterTab,
    SerialBatchTab,
    WarehouseLocationTab,
    InboundOutboundTab,
    StockAuditTab
)

def test_module_instantiation():
    """Test that all components can be instantiated."""
    print("Testing Warehouse Management Module...")
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Test main view
        print("[OK] Testing WarehouseManagementView...")
        main_view = WarehouseManagementView(root)
        print("[OK] WarehouseManagementView instantiated successfully")
        
        # Test individual tabs
        print("[OK] Testing ItemMasterTab...")
        item_tab = ItemMasterTab(root)
        print("[OK] ItemMasterTab instantiated successfully")
        
        print("[OK] Testing SerialBatchTab...")
        serial_tab = SerialBatchTab(root)
        print("[OK] SerialBatchTab instantiated successfully")
        
        print("[OK] Testing WarehouseLocationTab...")
        location_tab = WarehouseLocationTab(root)
        print("[OK] WarehouseLocationTab instantiated successfully")
        
        print("[OK] Testing InboundOutboundTab...")
        inbound_tab = InboundOutboundTab(root)
        print("[OK] InboundOutboundTab instantiated successfully")
        
        print("[OK] Testing StockAuditTab...")
        audit_tab = StockAuditTab(root)
        print("[OK] StockAuditTab instantiated successfully")
        
        print("\n[SUCCESS] All components instantiated successfully!")
        print("[SUCCESS] Warehouse Management Module is ready for use.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_module_instantiation()
    exit(0 if success else 1)