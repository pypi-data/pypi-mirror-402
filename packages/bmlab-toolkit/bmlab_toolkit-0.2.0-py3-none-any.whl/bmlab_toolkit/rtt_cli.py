"""
RTT CLI

Command-line interface for connecting to RTT and reading/writing data.
Supports multiple programmers (JLink by default).
"""

import sys
import time
import argparse
import logging
from pathlib import Path
from typing import Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from .constants import SUPPORTED_PROGRAMMERS, DEFAULT_PROGRAMMER, PROGRAMMER_JLINK
from .programmer import Programmer
from .jlink_programmer import JLinkProgrammer


def main():
    """Main entry point for bmlab-rtt command."""
    parser = argparse.ArgumentParser(
        description='Connect to RTT for real-time data transfer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect with auto-detect and read for 10 seconds
  bmlab-rtt

  # Specify JLink serial number
  bmlab-rtt --serial 123456789

  # Connect via IP address (MCU not needed)
  bmlab-rtt --ip 192.168.1.100

  # Connect to multiple devices in parallel (writes to files)
  bmlab-rtt --ip 192.168.1.100 192.168.1.101 192.168.1.102 --output-dir ./rtt_logs

  # Specify MCU explicitly
  bmlab-rtt --mcu STM32F765ZG

  # Read indefinitely until Ctrl+C
  bmlab-rtt -t 0

  # Send message after connection
  bmlab-rtt --msg "hello\\n"

  # Send message after 2 seconds delay
  bmlab-rtt --msg "test" --msg-timeout 2.0

  # No reset on connection
  bmlab-rtt --no-reset
  
  # Specify programmer explicitly (default: jlink)
  bmlab-rtt --programmer jlink --serial 123456
        """
    )
    
    parser.add_argument('--serial', '-s', type=int, nargs='+', default=None,
                       help='Programmer serial number(s) (auto-detect if not provided)')
    
    parser.add_argument('--programmer', '-p', type=str, default=DEFAULT_PROGRAMMER,
                       choices=SUPPORTED_PROGRAMMERS,
                       help=f'Programmer type (default: {DEFAULT_PROGRAMMER})')
    
    parser.add_argument('--ip', type=str, nargs='+', default=None,
                       help='JLink IP address(es) for network connection (can specify multiple)')
    
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory for RTT logs (required for multiple devices)')
    
    parser.add_argument('--mcu', '-m', type=str, default=None,
                       help='MCU name (e.g., STM32F765ZG). Auto-detects if not provided. Not used with --ip.')
    
    parser.add_argument('--reset', dest='reset', action='store_true', default=True,
                       help='Reset target after connection (default: True)')
    
    parser.add_argument('--no-reset', dest='reset', action='store_false',
                       help='Do not reset target after connection')
    
    parser.add_argument('--timeout', '-t', type=float, default=10.0,
                       help='Read timeout in seconds. 0 means read until interrupted (default: 10.0)')
    
    parser.add_argument('--msg', type=str, default=None,
                       help='Message to send via RTT after connection')
    
    parser.add_argument('--msg-timeout', type=float, default=0.5,
                       help='Delay in seconds before sending message (default: 0.5)')
    
    parser.add_argument('--msg-retries', type=int, default=10,
                       help='Number of retries for sending message (default: 10)')
    
    parser.add_argument('--log-level', '-l', type=str, default='WARNING',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level (default: WARNING)')
    
    args = parser.parse_args()
    
    # Validate that --serial and --ip are mutually exclusive
    if args.serial and args.ip:
        print("Error: Cannot specify both --serial and --ip")
        sys.exit(1)
    
    # Check if multiple devices specified
    ip_list = args.ip if args.ip else None
    serial_list = args.serial if args.serial else None
    
    # Build device list
    devices = []
    if ip_list:
        devices = [{'serial': None, 'ip': ip} for ip in ip_list]
    elif serial_list and isinstance(serial_list, list):
        devices = [{'serial': s, 'ip': None} for s in serial_list]
    else:
        devices = [{'serial': serial_list, 'ip': None}]
    
    # For multiple devices, require output directory
    if len(devices) > 1 and not args.output_dir:
        print("Error: --output-dir is required when using multiple devices")
        sys.exit(1)
    
    # Convert log level string to logging constant
    log_level = getattr(logging, args.log_level.upper())
    
    try:
        if len(devices) == 1:
            # Single device - output to stdout
            dev = devices[0]
            rtt_single_device(
                serial=dev['serial'],
                ip_addr=dev['ip'],
                mcu=args.mcu,
                programmer_type=args.programmer,
                reset=args.reset,
                timeout=args.timeout,
                msg=args.msg,
                msg_timeout=args.msg_timeout,
                msg_retries=args.msg_retries,
                log_level=log_level,
                output_file=None
            )
        else:
            # Multiple devices - parallel threads
            rtt_multiple_devices(
                devices=devices,
                output_dir=args.output_dir,
                mcu=args.mcu,
                programmer_type=args.programmer,
                reset=args.reset,
                timeout=args.timeout,
                msg=args.msg,
                msg_timeout=args.msg_timeout,
                msg_retries=args.msg_retries,
                log_level=log_level
            )
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def rtt_single_device(serial, ip_addr, mcu, programmer_type, reset, timeout, msg, msg_timeout, msg_retries, log_level, output_file):
    """RTT for single device."""
    # Create programmer instance
    if programmer_type.lower() == PROGRAMMER_JLINK:
        prog = JLinkProgrammer(serial=serial, ip_addr=ip_addr, log_level=log_level)
    else:
        raise NotImplementedError(f"Programmer '{programmer_type}' is not yet implemented")
    
    # Start RTT
    mcu_to_use = None if ip_addr else mcu
    
    if not prog.start_rtt(mcu=mcu_to_use, reset=reset, delay=1.0):
        print("Error: Failed to start RTT")
        sys.exit(1)
    
    device_id = ip_addr or serial or "auto-detected"
    print(f"RTT connected to {device_id}. Reading data...")
    if timeout == 0:
        print("(Press Ctrl+C to stop)")
    else:
        print(f"(Reading for {timeout} seconds)")
    
    # Send message if provided
    if msg:
        time.sleep(msg_timeout)
        msg_bytes = msg.encode('utf-8').decode('unicode_escape').encode('utf-8')
        
        for attempt in range(msg_retries):
            bytes_written = prog.rtt_write(msg_bytes)
            if bytes_written > 0:
                break
            if attempt < msg_retries - 1:
                time.sleep(1.0)
        else:
            print(f"Warning: Failed to write message after {msg_retries} attempts")
    
    # Open output file if specified
    file_handle = None
    if output_file:
        file_handle = open(output_file, 'wb')
    
    # Read data
    start_time = time.time()
    try:
        while True:
            if timeout > 0:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    break
            
            try:
                data = prog.rtt_read(max_bytes=4096)
            except Exception as e:
                print(f"\nRTT connection lost: {e}")
                break
            
            if data:
                if file_handle:
                    file_handle.write(data)
                    file_handle.flush()
                else:
                    try:
                        text = data.decode('utf-8', errors='replace')
                        print(text, end='', flush=True)
                    except Exception:
                        print(data, flush=True)
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        if file_handle:
            file_handle.close()
        prog.stop_rtt()
        prog.disconnect_target()
        # Give JLink Remote Server time to release connection
        time.sleep(0.5)
    
    if not output_file:
        print("\nDone.")


def rtt_device_task(device, output_dir, mcu, programmer_type, reset, timeout, msg, msg_timeout, msg_retries, log_level):
    """RTT task for a single device in parallel execution."""
    serial = device['serial']
    ip_addr = device['ip']
    device_id = ip_addr or f"serial_{serial}" or "auto"
    
    # Create output file path
    output_file = Path(output_dir) / f"rtt_{device_id.replace('.', '_')}.log"
    
    try:
        rtt_single_device(
            serial=serial,
            ip_addr=ip_addr,
            mcu=mcu,
            programmer_type=programmer_type,
            reset=reset,
            timeout=timeout,
            msg=msg,
            msg_timeout=msg_timeout,
            msg_retries=msg_retries,
            log_level=log_level,
            output_file=str(output_file)
        )
        return {'device': device_id, 'success': True, 'file': str(output_file)}
    except Exception as e:
        return {'device': device_id, 'success': False, 'error': str(e)}


def rtt_multiple_devices(devices, output_dir, mcu, programmer_type, reset, timeout, msg, msg_timeout, msg_retries, log_level):
    """RTT for multiple devices - parallel for IPs, sequential for serials."""
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Check if we have IP or serial devices
    has_ip = any(dev['ip'] for dev in devices)
    
    print(f"Starting RTT for {len(devices)} device(s)")
    print(f"Output directory: {output_dir}")
    if timeout == 0:
        print("(Press Ctrl+C to stop all)")
    else:
        print(f"(Reading for {timeout} seconds)\n")
    
    results = []
    
    if has_ip:
        # Parallel execution for IP devices using processes (thread-safe issues with pylink)
        with ProcessPoolExecutor(max_workers=len(devices)) as executor:
            futures = [
                executor.submit(
                    rtt_device_task,
                    dev,
                    output_dir,
                    mcu,
                    programmer_type,
                    reset,
                    timeout,
                    msg,
                    msg_timeout,
                    msg_retries,
                    log_level
                )
                for dev in devices
            ]
            
            for dev in devices:
                device_id = dev['ip'] or f"serial {dev['serial']}" or "auto"
                print(f"✓ Started RTT for {device_id}")
            
            # Collect results as they complete
            try:
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Terminating processes...")
                executor.shutdown(wait=False, cancel_futures=True)
                raise
    else:
        # Sequential execution for serial devices (USB driver limitations)
        print("Note: Serial devices are processed sequentially due to USB driver limitations\n")
        
        for dev in devices:
            device_id = f"serial {dev['serial']}" if dev['serial'] else "auto"
            print(f"✓ Processing RTT for {device_id}...")
            
            result = rtt_device_task(dev, output_dir, mcu, programmer_type, reset, timeout, msg, msg_timeout, msg_retries, log_level)
            results.append(result)
            
            if result['success']:
                print(f"  → Completed: {result['file']}\n")
            else:
                print(f"  → Failed: {result.get('error', 'Unknown error')}\n")
    
    # Summary
    print(f"{'='*60}")
    print(f"RTT completed for {len(devices)} device(s)")
    print(f"{'='*60}\n")
    
    for r in results:
        if r['success']:
            print(f"✓ {r['device']}: {r['file']}")
        else:
            print(f"✗ {r['device']}: {r.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
