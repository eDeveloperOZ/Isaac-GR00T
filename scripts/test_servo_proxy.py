#!/usr/bin/env python
#
# Direct test for serial proxy communication with Feetech servos
#

import os
import sys
import time
import binascii

# Add the Feetech-Servo-SDK directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sdk_dir = os.path.join(parent_dir, 'Feetech-Servo-SDK')
sys.path.append(sdk_dir)

from scservo_sdk import *

# Default settings
SERVO_IDS_TO_TEST = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]  # Try a range of IDs
BAUDRATE = 1000000                # 1M baud rate for Feetech servos
PROTOCOL_END = 0                 # STS/SMS=0, SCS=1
MAX_ATTEMPTS = 3                 # Number of retry attempts per port

# Use the ports created by the proxy
VIRTUAL_PORTS = [
    "/dev/pts/3",  # First virtual port created by the proxy (check Docker logs for actual path)
    "/dev/pts/4"   # Second virtual port created by the proxy (check Docker logs for actual path)
]

# For external testing of physical ports
PHYSICAL_PORTS = [
    "/dev/tty.usbmodem58CD1768061",  # Physical port for the servo
    "/dev/tty.usbmodem59700725941"   # Another physical port (from user's description)
]

# Uncomment to test physical ports directly
# VIRTUAL_PORTS = PHYSICAL_PORTS

def print_packet(packet, prefix=""):
    """Print a packet in hex format"""
    if isinstance(packet, (bytes, bytearray)):
        hex_str = binascii.hexlify(packet).decode('utf-8')
        formatted = ' '.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])
        print(f"{prefix}: {formatted}")
    else:
        print(f"{prefix}: {packet}")

def test_port(port_path):
    """Test a specific port by pinging servos and reading positions"""
    print(f"\n==== Testing port: {port_path} ====")
    
    try:
        # Initialize handlers
        port_handler = PortHandler(port_path)
        packet_handler = PacketHandler(PROTOCOL_END)
        
        # Open port
        if not port_handler.openPort():
            print(f"Failed to open port {port_path}")
            return False
            
        # Set baudrate
        if not port_handler.setBaudRate(BAUDRATE):
            print(f"Failed to set baudrate for {port_path}")
            port_handler.closePort()
            return False
            
        print(f"Successfully opened {port_path} at {BAUDRATE} baud")
        
        # Test each servo ID
        for servo_id in SERVO_IDS_TO_TEST:
            for attempt in range(MAX_ATTEMPTS):
                print(f"\nTesting Servo ID {servo_id} (attempt {attempt+1}/{MAX_ATTEMPTS})...")
                
                # 1. Ping the servo
                print(f"Pinging servo ID {servo_id}...")
                ping_packet = [0xFF, 0xFF, servo_id, 0x02, 0x01]  # Header, ID, Len, PING, Checksum
                
                # Calculate checksum
                checksum = 0
                for i in range(2, len(ping_packet)):
                    checksum += ping_packet[i]
                ping_packet.append((~checksum) & 0xFF)
                
                print_packet(bytes(ping_packet), "Sending PING")
                
                # Send ping command
                model_number, comm_result, error = packet_handler.ping(port_handler, servo_id)
                
                if comm_result != COMM_SUCCESS:
                    print(f"Ping failed: {packet_handler.getTxRxResult(comm_result)}")
                    continue
                
                if error != 0:
                    print(f"Ping error: {packet_handler.getRxPacketError(error)}")
                    continue
                    
                print(f"Ping success! Servo ID {servo_id} model number: {model_number}")
                
                # 2. Read Present Position
                ADDR_PRESENT_POSITION = 0x38  # Address for Present Position register
                LEN_PRESENT_POSITION = 2      # Data length (2 bytes for position)
                
                print(f"Reading Present Position from servo ID {servo_id}...")
                position, result, error = packet_handler.read2ByteTxRx(port_handler, servo_id, ADDR_PRESENT_POSITION)
                
                if result != COMM_SUCCESS:
                    print(f"Position read failed: {packet_handler.getTxRxResult(result)}")
                    continue
                
                if error != 0:
                    print(f"Position read error: {packet_handler.getRxPacketError(error)}")
                    continue
                
                print(f"SUCCESS: Servo ID {servo_id} Present Position = {position}")
                break  # Success, no need for more attempts
            
        # Close port
        port_handler.closePort()
        print(f"Closed port {port_path}")
        return True
        
    except Exception as e:
        print(f"Error testing port {port_path}: {str(e)}")
        return False

def main():
    """Test all ports for servo communication"""
    print("===== Servo Communication Test Script =====")
    print(f"Using ports: {', '.join(VIRTUAL_PORTS)}")
    print(f"Testing servo IDs: {SERVO_IDS_TO_TEST}")
    print(f"Baudrate: {BAUDRATE}")
    print("=========================================\n")
    
    success = False
    for port in VIRTUAL_PORTS:
        port_success = test_port(port)
        success = success or port_success
        # Small pause between port tests
        time.sleep(1)
    
    if not success:
        print("\nFAILED: Could not communicate with any servos.")
        print("Check physical connections and ensure the proxy server is running.")
    else:
        print("\nSUCCESS: Successfully communicated with at least one servo.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())