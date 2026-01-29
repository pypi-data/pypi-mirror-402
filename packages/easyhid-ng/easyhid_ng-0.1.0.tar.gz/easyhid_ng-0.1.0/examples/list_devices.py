#!/usr/bin/env python3
"""
Example: List all connected HID devices and their information.
"""

from easyhid import Enumeration


def main():
    # Create an enumeration of all connected USB HID devices
    print("Scanning for HID devices...\n")
    en = Enumeration()

    if not en.device_list:
        print("No HID devices found.")
        return

    print(f"Found {len(en.device_list)} HID device(s):\n")
    print("=" * 80)

    for i, device in enumerate(en.device_list, 1):
        print(f"\n[Device {i}]")
        print(f"  Path:              {device.path}")
        print(f"  Vendor ID:         0x{device.vendor_id:04X}")
        print(f"  Product ID:        0x{device.product_id:04X}")
        print(f"  Manufacturer:      {device.manufacturer_string or 'N/A'}")
        print(f"  Product:           {device.product_string or 'N/A'}")
        print(f"  Serial Number:     {device.serial_number or 'N/A'}")
        print(f"  Release Number:    {device.release_number}")
        print(f"  Interface Number:  {device.interface_number}")
        print(f"  Usage Page:        0x{device.usage_page:04X}")
        print(f"  Usage:             0x{device.usage:04X}")
        print("-" * 80)


if __name__ == "__main__":
    main()
