"""
Test script for R&D/Engineering Module
Tests the instantiation and basic functionality of all components.
"""

import tkinter as tk
from rnd_engineering import (
    RnDEngineeringView,
    ProductDevelopmentTab,
    ProjectsTasksTab,
    SprintManagementTab,
    HardwarePrototypeTab,
    ComponentsTab,
    RiskManagementTab,
    TeamResourceTab,
    ComplianceCertificationTab
)

def test_module_instantiation():
    """Test that all components can be instantiated."""
    print("Testing R&D/Engineering Module...")
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Test main view
        print("[OK] Testing RnDEngineeringView...")
        main_view = RnDEngineeringView(root)
        print("[OK] RnDEngineeringView instantiated successfully")
        
        # Test individual tabs
        print("[OK] Testing ProductDevelopmentTab...")
        pdlc_tab = ProductDevelopmentTab(root)
        print("[OK] ProductDevelopmentTab instantiated successfully")
        
        print("[OK] Testing ProjectsTasksTab...")
        projects_tab = ProjectsTasksTab(root)
        print("[OK] ProjectsTasksTab instantiated successfully")
        
        print("[OK] Testing SprintManagementTab...")
        sprint_tab = SprintManagementTab(root)
        print("[OK] SprintManagementTab instantiated successfully")
        
        print("[OK] Testing HardwarePrototypeTab...")
        hardware_tab = HardwarePrototypeTab(root)
        print("[OK] HardwarePrototypeTab instantiated successfully")
        
        print("[OK] Testing ComponentsTab...")
        components_tab = ComponentsTab(root)
        print("[OK] ComponentsTab instantiated successfully")
        
        print("[OK] Testing RiskManagementTab...")
        risk_tab = RiskManagementTab(root)
        print("[OK] RiskManagementTab instantiated successfully")
        
        print("[OK] Testing TeamResourceTab...")
        team_tab = TeamResourceTab(root)
        print("[OK] TeamResourceTab instantiated successfully")
        
        print("[OK] Testing ComplianceCertificationTab...")
        compliance_tab = ComplianceCertificationTab(root)
        print("[OK] ComplianceCertificationTab instantiated successfully")
        
        print("\n[SUCCESS] All components instantiated successfully!")
        print("[SUCCESS] R&D/Engineering Module is ready for use.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_module_instantiation()
    exit(0 if success else 1)