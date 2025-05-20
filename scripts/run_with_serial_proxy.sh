#!/bin/bash

# Run the Docker container with Serial Proxy port exposed

#################################################
# SERIAL PROXY USAGE GUIDE
#################################################
# This script starts a serial proxy server that creates virtual serial ports
# which can be used to communicate with hardware devices like Feetech servos.
#
# CONNECTING TO VIRTUAL PORTS:
# - The proxy creates two virtual serial ports, typically at /dev/pts/1 and /dev/pts/2
# - Connect to these ports using any serial communication library
# - Default baud rate is 1000000 (1M baud) suitable for Feetech servos
#
# EXAMPLE USAGE WITH FEETECH SERVOS:
# 1. Start this script in one terminal
# 2. In another terminal, run:
#    python3 Feetech-Servo-SDK/scsservo_sdk_example/ping.py --port=/dev/pts/1 --baudrate=1000000
#
# TROUBLESHOOTING:
# - Ensure Docker is running
# - Check if ports are being created (check server logs)
# - If "Permission denied" errors occur, try changing port permissions:
#   sudo chmod 666 /dev/pts/1
# - If you can't connect, try the host network mode (Option 2 below)
#################################################

# Option 1: Standard port mapping (recommended for most users)
echo "Starting container with standard port mapping..."
echo "Access the Serial Proxy at: http://localhost:5010"
echo "----------------------------------------------"
# NOTE: Using port 5010 instead of port 5000 because port 5000 is commonly used
# by system services on macOS (Control Center), AirPlay, and other Apple services.
# This helps avoid conflicts with system processes that might already be listening on port 5000.

# Check if port 5010 is already in use
echo "Checking if port 5010 is available..."
if command -v nc &> /dev/null; then
  if nc -z localhost 5010 &> /dev/null; then
    echo "⚠️ WARNING: Port 5010 appears to be already in use!"
    echo "This could be due to:"
    echo "  - Another instance of this script running"
    echo "  - Another application using port 5010"
    echo "  - A macOS service using this port"
    echo ""
    echo "You may continue, but the container might not start correctly."
    echo "Press Ctrl+C to cancel or any other key to continue anyway..."
    read -n 1 -s
  else
    echo "✅ Port 5010 is available"
  fi
else
  echo "⚠️ 'nc' command not found, skipping port availability check"
fi

# Volume bindings explanation:
# - scripts: Mount entire scripts directory to allow immediate reflection of code changes
# - Feetech-Servo-SDK: Mount SDK directory to provide access to servo control libraries
# - PYTHONPATH: Environment variable to ensure the SDK can be imported properly
docker run -it --rm \
  -p 5010:5000 \
  --name isaac-gr00t-serial \
  -v "$(pwd)/scripts:/workspace/scripts" \
  -v "$(pwd)/Feetech-Servo-SDK:/workspace/Feetech-Servo-SDK" \
  -e PYTHONPATH=/workspace \
  isaac_gr00t:latest \
  bash -c "python /workspace/scripts/serial_proxy_server.py"

# Option 2: Host network mode (alternative if option 1 doesn't work)
# Note: This gives the container direct access to the host's network interfaces
# Uncomment the lines below to use this mode instead
#
# echo "Starting container with host network mode..."
# echo "Access the Serial Proxy at: http://localhost:5010"
# echo "----------------------------------------------"
#
# # Volume bindings explanation:
# # - scripts: Mount entire scripts directory to allow immediate reflection of code changes
# # - Feetech-Servo-SDK: Mount SDK directory to provide access to servo control libraries
# # - PYTHONPATH: Environment variable to ensure the SDK can be imported properly
# docker run -it --rm \
#   --network host \
#   --name isaac-gr00t-serial \
#   -v "$(pwd)/scripts:/workspace/scripts" \
#   -v "$(pwd)/Feetech-Servo-SDK:/workspace/Feetech-Servo-SDK" \
#   -e PYTHONPATH=/workspace \
#   isaac_gr00t:latest \
#   bash -c "python /workspace/scripts/serial_proxy_server.py"

# Note: Web Serial API requires a secure context (HTTPS or localhost)
# If accessing via IP address, you may need to enable a Chrome flag:
# chrome://flags/#unsafely-treat-insecure-origin-as-secure

# Additional information about using the serial proxy:
# - The web interface provides controls for configuring and testing virtual ports
# - You can monitor traffic between your application and hardware devices
# - For Feetech servos, you'll need to use the correct protocol settings:
#   * Baud rate: 1000000 (1M baud)
#   * Data bits: 8
#   * Parity: None
#   * Stop bits: 1
#
# For more details, check the documentation in scripts/serial_proxy_server.py