"""Example usage of bmlab-toolkit - Python API."""

from bmlab_toolkit import JLinkProgrammer


def example_flash_simple():
    """Example: Flash device with minimal code."""
    firmware_file = "path/to/firmware.hex"
    
    # Flash with auto-detected JLink (first available)
    prog = JLinkProgrammer()
    prog.flash(firmware_file)


def example_flash_with_serial():
    """Example: Flash with specific JLink serial number."""
    firmware_file = "path/to/firmware.hex"
    serial_number = 123456789
    
    prog = JLinkProgrammer(serial=serial_number)
    prog.flash(firmware_file)


def example_flash_with_mcu():
    """Example: Flash with specific MCU specified."""
    firmware_file = "path/to/firmware.hex"
    
    prog = JLinkProgrammer()
    prog.flash(firmware_file, mcu="STM32F765ZG")


def example_flash_no_reset():
    """Example: Flash without reset after programming."""
    firmware_file = "path/to/firmware.hex"
    
    prog = JLinkProgrammer()
    prog.flash(firmware_file, reset=False)


def example_flash_via_network():
    """Example: Flash device via network (JLink Remote Server)."""
    firmware_file = "path/to/firmware.hex"
    ip_address = "192.168.1.100"
    
    # Connect via IP - no serial needed, MCU auto-detected
    prog = JLinkProgrammer(ip_addr=ip_address)
    prog.flash(firmware_file)


def example_detect_device():
    """Example: Detect connected MCU device."""
    prog = JLinkProgrammer()
    
    # Detect device (requires connection to programmer)
    if prog.probe():
        detected = prog.detect_target()
        if detected:
            print(f"Detected device: {detected}")
        else:
            print("Could not detect device")


def example_reset_device():
    """Example: Reset device after flashing."""
    firmware_file = "path/to/firmware.hex"
    
    prog = JLinkProgrammer()
    
    # Flash without auto-reset
    if prog.flash(firmware_file, reset=False):
        print("Flash successful, performing custom reset...")
        # Do something else here
        prog.reset(halt=False)


def example_erase_device():
    """Example: Erase device flash memory."""
    prog = JLinkProgrammer(serial=123456)
    
    # Erase flash
    prog.erase(mcu="STM32F103RE")
    print("Flash erased")


def example_read_memory():
    """Example: Read memory from device."""
    prog = JLinkProgrammer()
    
    # Note: Need to connect manually for memory operations
    # (flash() handles connection automatically)
    if hasattr(prog, '_connect_target'):
        prog.connect_target()
        data = prog.read_target_memory(0x08000000, 16)
        if data:
            hex_str = " ".join([f"{b:02X}" for b in data])
            print(f"Memory at 0x08000000: {hex_str}")
        prog.disconnect_target()

if __name__ == "__main__":
    print("bmlab-toolkit Python API Examples")
    print("="*60)
    print("Uncomment the example you want to run\n")
    
    # Uncomment to run examples:
    # example_flash_simple()
    # example_flash_with_serial()
    # example_flash_with_mcu()
    # example_flash_no_reset()
    # example_flash_via_network()
    # example_detect_device()
    # example_reset_device()
    # example_erase_device()
    # example_read_memory()
    
    print("No example selected. Edit the file to uncomment examples.")
    
    # Advanced: Read memory
    # example_read_memory()
