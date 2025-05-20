#!/usr/bin/env python3
"""
Test script to specifically read Present Position from Feetech servos.
This script is designed to run inside the Docker container and will
actively poll the servos for their positions to verify communication.
"""

import os
import sys
import time
import binascii

# Add the Feetech-Servo-SDK to the Python path
sys.path.insert(0, "/workspace/Feetech-Servo-SDK")

from scservo_sdk import *

# Configuration
SERVO_IDS = list(range(1, 14))  # Test IDs 1-13
BAUDRATE = 1000000            # 1M baud for Feetech servos
PROTOCOL_END = 0              # STS/SMS=0, SCS=1
MAX_ATTEMPTS = 3              # Retry attempts
RETRY_DELAY = 0.5             # Delay between retries (seconds)
POLLING_DELAY = 1.0           # Delay between polling cycles (seconds)

# Get available virtual ports inside Docker
def get_pty_ports():
    """Find available PTY ports in the Docker container"""
    pts_dir = "/dev/pts/"
    ports = []
    
    try:
        # List all files in /dev/pts
        for filename in os.listdir(pts_dir):
            if filename.isdigit() and int(filename) > 0:
                port_path = os.path.join(pts_dir, filename)
                ports.append(port_path)
        return sorted(ports)
    except Exception as e:
        print(f"Error finding PTY ports: {e}")
        return []

def print_packet(packet, prefix=""):
    """Print a packet in hex format"""
    if isinstance(packet, (bytes, bytearray)):
        hex_str = binascii.hexlify(packet).decode('utf-8')
        formatted = ' '.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])
        print(f"{prefix}: {formatted}")
    elif isinstance(packet, list):
        formatted = ' '.join([f"{b:02X}" for b in packet])
        print(f"{prefix}: {formatted}")
    else:
        print(f"{prefix}: {packet}")

def read_present_position(port_handler, packet_handler, servo_id):
    """Read Present Position from a servo"""
    print(f"\nReading Present Position from servo ID {servo_id}...")
    
    # Address for Present Position register (may vary by servo model)
    ADDR_PRESENT_POSITION = 0x38
    
    # Try multiple attempts
    for attempt in range(MAX_ATTEMPTS):
        print(f"Attempt {attempt+1}/{MAX_ATTEMPTS}")
        
        # Create the read position packet manually for logging
        read_packet = [0xFF, 0xFF, servo_id, 0x04, 0x02, ADDR_PRESENT_POSITION, 0x02]
        # Calculate checksum
        checksum = 0
        for i in range(2, len(read_packet)):
            checksum += read_packet[i]
        read_packet.append((~checksum) & 0xFF)
        
        print_packet(read_packet, "Sending READ_POSITION packet")
        
        # Send the read command
        position, result, error = packet_handler.read2ByteTxRx(
            port_handler, 
            servo_id, 
            ADDR_PRESENT_POSITION
        )
        
        if result != COMM_SUCCESS:
            print(f"Failed to read position: {packet_handler.getTxRxResult(result)}")
            time.sleep(RETRY_DELAY)
            continue
            
        if error != 0:
            print(f"Error from servo: {packet_handler.getRxPacketError(error)}")
            time.sleep(RETRY_DELAY)
            continue
            
        print(f"SUCCESS: Servo ID {servo_id} Present Position = {position}")
        return position
    
    print(f"Failed to read position after {MAX_ATTEMPTS} attempts")
    return None

def main():
    """Main function to poll servos for their positions"""
    print("===== Feetech Servo Present Position Test =====")
    
    # Get available ports
    ports = get_pty_ports()
    if not ports:
        print("No PTY ports found. Exiting.")
        return 1
    
    print(f"Found PTY ports: {', '.join(ports)}")
    
    # Try each port
    for port_path in ports:
        print(f"\n==== Testing port: {port_path} ====")
        
        # Initialize handlers
        port_handler = PortHandler(port_path)
        packet_handler = PacketHandler(PROTOCOL_END)
        
        # Open port
        try:
            if not port_handler.openPort():
                print(f"Failed to open port {port_path}")
                continue
                
            # Set baudrate
            if not port_handler.setBaudRate(BAUDRATE):
                print(f"Failed to set baudrate for {port_path}")
                port_handler.closePort()
                continue
                
            print(f"Successfully opened {port_path} at {BAUDRATE} baud")
            
            # Enter polling loop
            print("\nStarting position polling loop (Ctrl+C to exit)...")
            
            try:
                poll_count = 0
                while True:
                    poll_count += 1
                    print(f"\n--- Polling cycle {poll_count} ---")
                    
                    # Test each servo ID
                    for servo_id in SERVO_IDS:
                        read_present_position(port_handler, packet_handler, servo_id)
                    
                    # Delay between polling cycles
                    time.sleep(POLLING_DELAY)
            except KeyboardInterrupt:
                print("\nPolling interrupted by user")
            
            # Close port
            port_handler.closePort()
            print(f"Closed port {port_path}")
            
        except Exception as e:
            print(f"Error testing port {port_path}: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())