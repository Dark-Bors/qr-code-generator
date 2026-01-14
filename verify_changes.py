
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from algorithms import mod_11_10, calc_check_digit

def test_sn_checksum():
    sn = "123456"
    check = mod_11_10(sn)
    print(f"SN: {sn} -> Check: {check}")
    assert len(check) == 1, "SN Checksum should be 1 char"

def test_ble_checksum():
    # Test with mixed case to match GUI logic (gui converts to lower first)
    ble_val = "ABCDEF"
    # GUI logic: calc_check_digit(val.lower())
    check = calc_check_digit(ble_val.lower())
    print(f"BLE (lower): {ble_val.lower()} -> Check: {check} -> Upper: {check.upper()}")
    assert len(check) == 1, "BLE Checksum should be 1 char"

def verify_gui_import():
    try:
        import gui
        print("✅ gui.py imported successfully")
    except ImportError as e:
        if "customtkinter" in str(e):
             print("⚠️  Skipping full GUI import check (customtkinter not installed in this env), but syntax likely ok.")
        else:
            print(f"❌ Import failed: {e}")
            raise

if __name__ == "__main__":
    print("--- Verifying Algorithms ---")
    test_sn_checksum()
    test_ble_checksum()
    print("--- Verifying GUI Import ---")
    verify_gui_import()
    print("\n✅ Verification Complete")
