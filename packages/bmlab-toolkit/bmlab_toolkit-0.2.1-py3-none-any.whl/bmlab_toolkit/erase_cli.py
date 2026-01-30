"""
Device Erase CLI

Command-line interface for erasing flash memory of embedded devices.
"""

import sys
import time
import argparse
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from .jlink_programmer import JLinkProgrammer


def main():
    """Main entry point for bmlab-erase command."""
    parser = argparse.ArgumentParser(
        description='Erase flash memory of embedded devices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Erase with auto-detected programmer and MCU
  bmlab-erase

  # Specify JLink serial number
  bmlab-erase --serial 123456789

  # Erase multiple devices by serial
  bmlab-erase --serial 123456 789012 345678

  # Specify MCU explicitly
  bmlab-erase --mcu STM32F765ZG

  # Use IP address for network JLink
  bmlab-erase --ip 192.168.1.100

  # Erase multiple devices in parallel by IP
  bmlab-erase --ip 192.168.1.100 192.168.1.101 192.168.1.102
        """
    )
    
    parser.add_argument('--serial', '-s', type=int, nargs='+', default=None,
                       help='JLink serial number(s) (can specify multiple for sequential erase, or leave empty for auto-detect)')
    
    parser.add_argument('--mcu', '-m', type=str, default=None,
                       help='MCU name (e.g., STM32F765ZG). Auto-detects if not provided.')
    
    parser.add_argument('--ip', type=str, nargs='+', default=None,
                       help='JLink IP address(es) for network connection (can specify multiple for parallel erase)')
    
    parser.add_argument('--log-level', '-l', type=str, default='WARNING',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level (default: WARNING)')
    
    args = parser.parse_args()
    
    # Validate that --serial and --ip are mutually exclusive
    if args.serial and args.ip:
        print("Error: Cannot specify both --serial and --ip")
        sys.exit(1)
    
    try:
        # Convert log level string to logging constant
        log_level = getattr(logging, args.log_level.upper())
        
        # Handle IP addresses and serials
        ip_list = args.ip if args.ip else None
        serial_list = args.serial if args.serial else None
        
        erase_devices(serial_list, ip_list, args.mcu, log_level)
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


def erase_device_task(serial, ip_addr, mcu, log_level):
    """Erase a single device (used in parallel execution)."""
    try:
        prog = JLinkProgrammer(serial=serial, ip_addr=ip_addr, log_level=log_level)
        
        if not prog.erase(mcu=mcu):
            device_id = ip_addr or serial
            return {'device': device_id, 'success': False, 'error': 'Erase operation failed'}
        
        # Small delay to ensure device is properly released
        time.sleep(0.5)
        
        device_id = ip_addr or serial
        return {'device': device_id, 'success': True, 'error': None}
    except Exception as e:
        device_id = ip_addr or serial
        return {'device': device_id, 'success': False, 'error': str(e)}


def erase_devices(serial, ip_list, mcu, log_level):
    """Erase one or multiple devices."""
    # Build device list
    devices = []
    if ip_list:
        devices = [{'serial': None, 'ip': ip} for ip in ip_list]
    elif serial and isinstance(serial, list):
        devices = [{'serial': s, 'ip': None} for s in serial]
    else:
        devices = [{'serial': serial, 'ip': None}]
    
    # Print header
    device_names = []
    for d in devices:
        if d['ip']:
            device_names.append(str(d['ip']))
        elif d['serial'] is not None:
            device_names.append(f"serial {d['serial']}")
        else:
            device_names.append("auto-detected")
    print(f"Erasing {len(devices)} device(s): {', '.join(device_names)}\n")
    
    results = []
    if ip_list:
        # Parallel erase for IPs
        with ProcessPoolExecutor(max_workers=len(devices)) as executor:
            future_to_device = {
                executor.submit(erase_device_task, dev['serial'], dev['ip'], mcu, log_level): dev
                for dev in devices
            }
            for future in as_completed(future_to_device):
                dev = future_to_device[future]
                try:
                    result = future.result(timeout=300)
                    results.append(result)
                    if result['success']:
                        print(f"✓ {result['device']}: Success")
                    else:
                        print(f"✗ {result['device']}: {result['error']}")
                except Exception as e:
                    device_id = dev['ip'] or dev['serial']
                    results.append({'device': device_id, 'success': False, 'error': str(e)})
                    print(f"✗ {device_id}: {e}")
    else:
        # Sequential erase for serials
        for dev in devices:
            result = erase_device_task(dev['serial'], dev['ip'], mcu, log_level)
            results.append(result)
            if result['success']:
                print(f"✓ {result['device']}: Success")
            else:
                print(f"✗ {result['device']}: {result['error']}")
    
    # Summary
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    
    if len(devices) > 1:
        print(f"\n{'='*60}")
        print(f"Erase completed: {success_count} successful, {fail_count} failed")
        print(f"{'='*60}")
    
    if fail_count > 0:
        if len(devices) > 1:
            print("\nFailed devices:")
            for r in results:
                if not r['success']:
                    print(f"  - {r['device']}: {r['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
