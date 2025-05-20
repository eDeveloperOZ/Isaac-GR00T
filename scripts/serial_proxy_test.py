#!/usr/bin/env python3
"""
Serial Proxy Test Script

This script tests direct communication with Feetech servo motors via physical ports.
It can be used to verify the bidirectional communication flow between physical servos
and the Docker container by providing a way to test the physical connection
independently of the web interface.

Usage:
  python3 serial_proxy_test.py [--port PORT] [--verbose] [--interval INTERVAL]

Options:
  --port PORT       Specify which physical port to test:
                    1 = /dev/tty.usbmodem58CD1768061
                    2 = /dev/tty.usbmodem59700725941
                    all = both ports (default)
  --verbose         Enable detailed packet logging
  --interval INTERVAL  Time between polling iterations in seconds (default: 1.0)
"""

import os
import sys
import time
import argparse
import threading
from queue import Queue
import binascii

# Import Feetech Servo SDK
# We're using the same import approach as in ping.py, which works in the Docker environment
SDK_IMPORT_SUCCESS = False
try:
    from scservo_sdk import *  # This works when running inside the Docker container
    SDK_IMPORT_SUCCESS = True
except ImportError:
    print("WARNING: Cannot import Feetech Servo SDK.")
    print("This script is designed to run in the same environment as the other scripts.")
    print("Make sure to run it using the Docker container where PYTHONPATH is properly set.")
    
    # Define minimal SDK classes needed for the script to work
    # These fallback definitions will allow the script to run with limited functionality
    print("Using fallback definitions for SDK components...")
    
    # Define Protocol Packet Handler class similar to the actual SDK
    class PacketHandler:
        def __init__(self, protocol_end):
            self.protocol_end = protocol_end
        
        def ping(self, port, servo_id):
            print(f"FALLBACK: Ping servo ID {servo_id}")
            return 0, 0, 0  # model_number, comm_result, error
            
        def read2ByteTxRx(self, port, servo_id, address):
            print(f"FALLBACK: Reading address {address} from servo ID {servo_id}")
            return 0, 0, 0  # position, comm_result, error
            
        def getTxRxResult(self, result):
            return f"Communication Result: {result}"
            
        def getRxPacketError(self, error):
            return f"Packet Error: {error}"
            
        def txRxPacket(self, port, txpacket):
            print(f"FALLBACK: Sending packet: {txpacket}")
            return 0, [], 0  # comm_result, rxpacket, error
    
    # Define Port Handler class similar to the actual SDK
    class PortHandler:
        def __init__(self, port_path):
            self.port_path = port_path
            self.is_open = False
            
        def openPort(self):
            print(f"FALLBACK: Opening port {self.port_path}")
            self.is_open = True
            return True
            
        def closePort(self):
            print(f"FALLBACK: Closing port {self.port_path}")
            self.is_open = False
            
        def setBaudRate(self, baudrate):
            print(f"FALLBACK: Setting baudrate to {baudrate}")
            return True

# Default settings
PORTS = {
    '1': '/dev/tty.usbmodem58CD1768061',
    '2': '/dev/tty.usbmodem59700725941'
}
BAUDRATE = 1000000  # 1M baud
PROTOCOL_END = 1    # SCS protocol end=1
SERVO_IDS = range(1, 13)  # Test servo IDs 1-12
PRESENT_POSITION = 0x38  # Register for present position

# Define constants needed for the script to work
# These are usually imported from the SDK, but defined here for robustness
COMM_SUCCESS = 0  # SDK defines this as 0 for successful communication

# Global variables
verbose_mode = False
packet_queue = Queue()  # For logging packets
stop_event = threading.Event()  # To signal threads to stop

def log_packet(direction, port_id, packet_bytes, packet_type="HEX"):
    """
    Log packet data in a structured format
    """
    if not verbose_mode and packet_type != "ERROR":
        return
    
    timestamp = time.strftime("%H:%M:%S")
    hex_data = ' '.join([f"0x{b:02X}" for b in packet_bytes])
    
    # Format similar to ping.py output
    if packet_type == "TX":
        log_str = f"[{timestamp}] [{port_id}] TX: [{hex_data}]"
    elif packet_type == "RX":
        log_str = f"[{timestamp}] [{port_id}] RX: [{hex_data}]"
    elif packet_type == "ERROR":
        log_str = f"[{timestamp}] [{port_id}] ERROR: {direction}"
    else:
        log_str = f"[{timestamp}] [{port_id}] {direction}: [{hex_data}]"
    
    packet_queue.put(log_str)

def logger_thread():
    """
    Thread to output logs from the queue
    """
    while not stop_event.is_set() or not packet_queue.empty():
        try:
            message = packet_queue.get(timeout=0.1)
            print(message)
            packet_queue.task_done()
        except:
            pass

def test_servo_port(port_id, port_path, interval=1.0):
    """
    Test communication with servos on a specific port
    """
    # Output heading
    print(f"\n{'='*80}")
    print(f"TESTING PORT {port_id}: {port_path}")
    print(f"{'='*80}")

    # Initialize the port handler
    port_handler = PortHandler(port_path)
    
    # Try to open the port
    if not port_handler.openPort():
        error_msg = f"Failed to open port: {port_path}"
        log_packet("Failed to open port", port_id, [], "ERROR")
        print(error_msg)
        return False
    
    print(f"Successfully opened port: {port_path}")
    
    # Set baudrate
    if not port_handler.setBaudRate(BAUDRATE):
        error_msg = f"Failed to set baudrate: {BAUDRATE}"
        log_packet(error_msg, port_id, [], "ERROR")
        port_handler.closePort()
        return False
    
    print(f"Successfully set baudrate: {BAUDRATE}")
    
    # Initialize packet handler for SCS protocol
    packet_handler = PacketHandler(PROTOCOL_END)
    
    # Monkey patch to log all packets
    original_txRxPacket = packet_handler.txRxPacket
    
    def debug_txRxPacket(port, txpacket):
        # Log transmitted packet
        log_packet("Sending packet", port_id, txpacket, "TX")
        
        # Call original function
        response = original_txRxPacket(port, txpacket)
        
        # Process response
        if isinstance(response, tuple) and len(response) >= 3:
            result, rxpacket, error = response
            if isinstance(rxpacket, (bytes, bytearray, list)):
                # Log received packet
                log_packet("Received packet", port_id, rxpacket, "RX")
            else:
                log_packet(f"Received non-iterable: {rxpacket}", port_id, [], "ERROR")
            return result, rxpacket, error
        else:
            log_packet(f"Unexpected response: {response}", port_id, [], "ERROR")
            return response
    
    # Apply the monkey patch
    packet_handler.txRxPacket = debug_txRxPacket
    
    # Test loop - continue until stopped
    try:
        iteration = 1
        while not stop_event.is_set():
            print(f"\n--- Port {port_id} - Iteration {iteration} ---")
            
            # Ping each servo ID
            for servo_id in SERVO_IDS:
                print(f"\nTesting Servo ID: {servo_id}")
                
                # Ping the servo
                scs_model_number, scs_comm_result, scs_error = packet_handler.ping(port_handler, servo_id)
                
                if scs_comm_result != COMM_SUCCESS:
                    print(f"[ID:{servo_id:03d}] Ping failed: {packet_handler.getTxRxResult(scs_comm_result)}")
                    continue
                elif scs_error != 0:
                    print(f"[ID:{servo_id:03d}] Ping error: {packet_handler.getRxPacketError(scs_error)}")
                    continue
                else:
                    print(f"[ID:{servo_id:03d}] Ping succeeded. SCServo model number: {scs_model_number}")
                    
                    # Read Present Position
                    position, result, error = packet_handler.read2ByteTxRx(port_handler, servo_id, PRESENT_POSITION)
                    
                    if result != COMM_SUCCESS:
                        print(f"[ID:{servo_id:03d}] Read failed: {packet_handler.getTxRxResult(result)}")
                    elif error != 0:
                        print(f"[ID:{servo_id:03d}] Read error: {packet_handler.getRxPacketError(error)}")
                    else:
                        print(f"[ID:{servo_id:03d}] Present Position: {position}")
            
            iteration += 1
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"\nTest for port {port_id} terminated by user")
    except Exception as e:
        print(f"\nError testing port {port_id}: {str(e)}")
    finally:
        # Close the port
        port_handler.closePort()
        print(f"Closed port: {port_path}")
    
    return True

def main():
    global verbose_mode
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Feetech servo communication via physical ports')
    parser.add_argument('--port', choices=['1', '2', 'all'], default='all',
                        help='Which physical port to test (default: all)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable detailed packet logging')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='Time between polling iterations in seconds (default: 1.0)')
    args = parser.parse_args()
    
    # Set global verbose mode
    verbose_mode = args.verbose
    
    # Start logger thread
    logger_t = threading.Thread(target=logger_thread, daemon=True)
    logger_t.start()
    
    try:
        # Determine which ports to test
        ports_to_test = []
        if args.port == 'all':
            ports_to_test = list(PORTS.items())
        else:
            if args.port in PORTS:
                ports_to_test = [(args.port, PORTS[args.port])]
            else:
                print(f"Error: Invalid port specified: {args.port}")
                return
        
        # Print test header
        print("\n" + "="*80)
        print(f"SERIAL PROXY TEST - Testing {len(ports_to_test)} port(s)")
        print(f"Verbose mode: {'ON' if verbose_mode else 'OFF'}")
        print(f"Poll interval: {args.interval} seconds")
        print("="*80 + "\n")
        
        # Test selected ports sequentially
        for port_id, port_path in ports_to_test:
            test_servo_port(port_id, port_path, args.interval)
            
    except KeyboardInterrupt:
        print("\nTest terminated by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        # Signal threads to stop
        stop_event.set()
        # Wait for logger to finish
        if logger_t.is_alive():
            logger_t.join(timeout=1.0)

if __name__ == "__main__":
    main()