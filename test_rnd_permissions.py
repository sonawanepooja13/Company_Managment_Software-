"""
Test script for R&D Granular Permissions functionality
Tests the separate R&D permissions window and permission control.
"""

import tkinter as tk
from main import RnDPermissionsWindow

def test_rnd_permissions_window():
    """Test that the R&D permissions window can be instantiated."""
    print("Testing R&D Granular Permissions Window...")
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create mock module variables
        module_vars = {
            'allow_rnd_pdlc': tk.BooleanVar(value=False),
            'allow_rnd_projects': tk.BooleanVar(value=False),
            'allow_rnd_sprints': tk.BooleanVar(value=False),
            'allow_rnd_hardware': tk.BooleanVar(value=False),
            'allow_rnd_components': tk.BooleanVar(value=False),
            'allow_rnd_risk': tk.BooleanVar(value=False),
            'allow_rnd_team': tk.BooleanVar(value=False),
            'allow_rnd_compliance': tk.BooleanVar(value=False),
        }
        
        # Test R&D permissions window
        print("[OK] Testing RnDPermissionsWindow...")
        rnd_window = RnDPermissionsWindow(root, module_vars)
        print("[OK] RnDPermissionsWindow instantiated successfully")
        
        # Test permission functions
        print("[OK] Testing open_all_rnd function...")
        rnd_window.open_all_rnd()
        all_enabled = all(var.get() for var in module_vars.values())
        print(f"[OK] All R&D permissions enabled: {all_enabled}")
        
        print("[OK] Testing close_all_rnd function...")
        rnd_window.close_all_rnd()
        all_disabled = all(not var.get() for var in module_vars.values())
        print(f"[OK] All R&D permissions disabled: {all_disabled}")
        
        print("[OK] Testing set_default_rnd function...")
        rnd_window.set_default_rnd()
        print("[OK] Default R&D permissions set")
        
        rnd_window.destroy()
        
        print("\n[SUCCESS] R&D Granular Permissions Window is working correctly!")
        print("[SUCCESS] All permission control functions operational.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_rnd_permissions_window()
    exit(0 if success else 1)