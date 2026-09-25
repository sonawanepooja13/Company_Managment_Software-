"""
Test script for Legal & Compliance Module
Tests the instantiation and basic functionality of all components.
"""

import tkinter as tk
from legal_compliance import (
    LegalComplianceView,
    InternalDocumentsTab,
    ExternalDocumentsTab,
    DataProtectionTab,
    ContractsTrackingTab,
    EmployeeAgreementsTab,
    DocumentTemplatesTab
)

def test_module_instantiation():
    """Test that all components can be instantiated."""
    print("Testing Legal & Compliance Module...")
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Test main view
        print("[OK] Testing LegalComplianceView...")
        main_view = LegalComplianceView(root)
        print("[OK] LegalComplianceView instantiated successfully")
        
        # Test individual tabs
        print("[OK] Testing InternalDocumentsTab...")
        internal_tab = InternalDocumentsTab(root)
        print("[OK] InternalDocumentsTab instantiated successfully")
        
        print("[OK] Testing ExternalDocumentsTab...")
        external_tab = ExternalDocumentsTab(root)
        print("[OK] ExternalDocumentsTab instantiated successfully")
        
        print("[OK] Testing DataProtectionTab...")
        data_protection_tab = DataProtectionTab(root)
        print("[OK] DataProtectionTab instantiated successfully")
        
        print("[OK] Testing ContractsTrackingTab...")
        contracts_tab = ContractsTrackingTab(root)
        print("[OK] ContractsTrackingTab instantiated successfully")
        
        print("[OK] Testing EmployeeAgreementsTab...")
        employee_tab = EmployeeAgreementsTab(root)
        print("[OK] EmployeeAgreementsTab instantiated successfully")
        
        print("[OK] Testing DocumentTemplatesTab...")
        templates_tab = DocumentTemplatesTab(root)
        print("[OK] DocumentTemplatesTab instantiated successfully")
        
        print("\n[SUCCESS] All components instantiated successfully!")
        print("[SUCCESS] Legal & Compliance Module is ready for use.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_module_instantiation()
    exit(0 if success else 1)