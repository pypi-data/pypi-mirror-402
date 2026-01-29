# bmlab-toolkit

Toolkit for flashing and testing embedded devices.

## Features

- Flash embedded devices (currently supports JLink)
- List and detect connected programmers
- Automatic STM32 device detection (F1/F4/F7/G0 series)
- Support for multiple firmware formats (.hex, .bin)
- **Real-Time Transfer (RTT) support** - Connect to device RTT for real-time communication
- Single unified command-line interface
- Extensible architecture for supporting additional programmers

## Installation

```bash
pip install bmlab-toolkit
```

## Usage

### Command Line

List connected programmers:
```bash
bmlab-flash
# or specify programmer type
bmlab-flash --programmer jlink
```

Flash a device with auto-detected programmer (uses first available JLink):
```bash
bmlab-flash <firmware_file>
```

Flash with specific serial number:
```bash
bmlab-flash <firmware_file> --serial <serial_number>
```

Flash with specific MCU:
```bash
bmlab-flash <firmware_file> --mcu STM32F765ZG
```

Flash multiple devices via IP addresses (parallel):
```bash
bmlab-flash firmware.bin --ip 192.168.1.100 192.168.1.101 192.168.1.102 --mcu STM32F765ZG
```

Flash multiple devices via USB serial (sequential due to USB driver limitations):
```bash
bmlab-flash firmware.bin --serial 123456 789012 345678 --mcu STM32F103RE
```

Specify programmer explicitly:
```bash
bmlab-flash <firmware_file> --programmer jlink --serial 123456
```

Get help:
```bash
bmlab-flash --help
```

### RTT (Real-Time Transfer)

Connect to RTT for real-time communication with the target device:

```bash
# Connect with auto-detection and read for 10 seconds
bmlab-rtt

# Specify programmer serial number
bmlab-rtt --serial 123456789

# Connect via IP address (no MCU needed)
bmlab-rtt --ip 192.168.1.100

# Specify MCU explicitly
bmlab-rtt --mcu STM32F765ZG

# Read indefinitely until Ctrl+C
bmlab-rtt -t 0

# Send message after connection
bmlab-rtt --msg "hello\n"

# Send message after custom delay
bmlab-rtt --msg "test" --msg-timeout 2.0

# Connect without resetting target
bmlab-rtt --no-reset

# Verbose output
bmlab-rtt -v

# Specify programmer explicitly (default: jlink)
bmlab-rtt --programmer jlink --serial 123456

# Monitor multiple devices via IP (parallel, saves logs to files)
bmlab-rtt --ip 192.168.1.100 192.168.1.101 192.168.1.102 --output-dir rtt_logs --timeout 10

# Monitor multiple devices via USB (sequential, saves logs to files)
bmlab-rtt --serial 123456 789012 --mcu STM32F103RE --output-dir rtt_logs --timeout 10
```

**Note:** Multiple devices require `--output-dir`. Logs are saved as `rtt_192_168_1_100.log` or `rtt_serial_123456.log`.

Get RTT help:
```bash
bmlab-rtt --help
```

### Erasing Flash Memory

Erase flash memory on a device:

```bash
# Erase with auto-detected device
bmlab-erase --mcu STM32F103RE

# Erase specific device by serial
bmlab-erase --serial 123456 --mcu STM32F103RE

# Erase device via IP
bmlab-erase --ip 192.168.1.100 --mcu STM32F765ZG

# Erase multiple devices via IP (parallel)
bmlab-erase --ip 192.168.1.100 192.168.1.101 192.168.1.102 --mcu STM32F103RE

# Erase multiple devices via USB (sequential)
bmlab-erase --serial 123456 789012 345678 --mcu STM32F103RE
```

### Scanning for Devices

Scan for USB-connected JLink devices:
```bash
bmlab-scan
```

Scan network for JLink Remote Servers:
```bash
# Scan entire network
bmlab-scan --network 192.168.1.0/24

# Scan specific IP range (last octet)
bmlab-scan --network 192.168.1.0/24 --start-ip 100 --end-ip 150

# With debug output
bmlab-scan --network 192.168.1.0/24 --log-level DEBUG
```

### Python API

#### Flashing

```python
from bmlab_toolkit import JLinkProgrammer

# Create programmer instance (auto-detect serial)
prog = JLinkProgrammer()

# Or specify serial number
prog = JLinkProgrammer(serial=123456789)

# Flash firmware (auto-detect MCU)
prog.flash("firmware.hex")

# Flash with specific MCU
prog.flash("firmware.hex", mcu="STM32F765ZG")

# Flash without reset
prog.flash("firmware.hex", reset=False)
```

#### RTT Communication

```python
from bmlab_toolkit import JLinkProgrammer
import time

# Create programmer
prog = JLinkProgrammer(serial=123456789)

try:
    # Reset device (optional)
    prog.reset(halt=False)
    time.sleep(0.5)
    
    # Start RTT
    prog.start_rtt(delay=1.0)
    
    # Send data
    prog.rtt_write(b"Hello, device!\n")
    
    # Read data
    data = prog.rtt_read(max_bytes=4096)
    if data:
        print(data.decode('utf-8', errors='replace'))
    
    # Stop RTT
    prog.stop_rtt()
    
finally:
    # Disconnect
    prog._disconnect_target()
```

## Development

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Currently Supported

### Programmers
- JLink (via pylink-square)

### Devices
- STM32F1 series (Low/Medium/High/XL density, Connectivity line)
- STM32F4 series (F405/407/415/417, F427/429/437/439)
- STM32F7 series (F74x/75x, F76x/77x)
- STM32G0 series (G0x0, G0x1, G0Bx/G0Cx)

## Roadmap

### Planned Features
  
- **Device Testing** - Automated testing capabilities
  - Run tests on connected devices
  - Collect and analyze test results via RTT
  - Generate test reports
  
- **Additional Programmers**
  - ST-Link support
  - OpenOCD support
  - Custom programmer interfaces

## Extending with New Programmers

The library is organized into functional modules:

- `constants.py` - Programmer type constants
- `list_devices.py` - Device detection and listing functionality
- `flashing.py` - Flashing operations
- `jlink_device_detector.py` - STM32-specific device detection

To add support for a new programmer:

1. Add the programmer constant to `src/bmlab_toolkit/constants.py`:
```python
PROGRAMMER_STLINK = "stlink"
SUPPORTED_PROGRAMMERS = [PROGRAMMER_JLINK, PROGRAMMER_STLINK]
```

2. Implement device listing in `src/bmlab_toolkit/list_devices.py`:
```python
def _get_stlink_devices() -> List[Dict[str, Any]]:
    # Implementation here
    pass

# Update get_connected_devices() function to handle new programmer
```

3. Implement flashing function in `src/bmlab_toolkit/flashing.py`:
```python
def _flash_with_stlink(serial: int, fw_file: str, mcu: str = None) -> None:
    # Implementation here
    pass

# Add case in flash_device_by_usb()
elif programmer_lower == PROGRAMMER_STLINK:
    _flash_with_stlink(serial, fw_file, mcu)
```

4. Update documentation and tests

## License

MIT
