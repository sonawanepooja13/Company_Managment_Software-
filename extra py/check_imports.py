import sys

print("Testing imports one by one...")

try:
    print("1. Importing auth_manager...", end="")
    import auth_manager
    print(" OK")

    print("2. Importing bom_engine...", end="")
    import bom_engine
    print(" OK")

    print("3. Importing tabs.admin_tab...", end="")
    from tabs.admin_tab import AdminTab
    print(" OK")

    print("4. Importing tabs.crm_tab...", end="")
    from tabs.crm_tab import CrmTab
    print(" OK")

    print("5. Importing tabs.material_tab...", end="")
    from tabs.material_tab import MaterialTab
    print(" OK")

    print("6. Importing tabs.price_tab...", end="")
    from tabs.price_tab import PriceTab
    print(" OK")

    print("\nAll imports passed successfully!")

except Exception as e:
    print(f"\n❌ CRASH/ERROR DETECTED: {e}")