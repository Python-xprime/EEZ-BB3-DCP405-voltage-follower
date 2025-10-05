#!/usr/bin/env python3
"""
BB3 Screenshot Tool
Takes a screenshot from BB3 device and saves it to project folder
"""

import socket
import sys
from datetime import datetime

BB3_IP = "192.168.10.78"
BB3_PORT = 5025

def take_screenshot(filename=None):
    """Take screenshot from BB3 and save to file"""

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bb3_screenshot_{timestamp}.jpg"

    print(f"Connecting to BB3 at {BB3_IP}:{BB3_PORT}...")

    try:
        # Connect to BB3
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((BB3_IP, BB3_PORT))
        print("Connected!")

        # Send screenshot command
        print("Requesting screenshot...")
        sock.sendall(b"DISPlay:DATA?\n")

        # Read response
        print("Reading image data...")
        data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            # Check if we got the complete response (ends with newline)
            if data.endswith(b"\n"):
                break

        sock.close()

        # Parse IEEE 488.2 definite length block format
        # Format: #<length_of_length><length><data>
        if not data.startswith(b"#"):
            print("ERROR: Invalid response format")
            return False

        # Get length of length field
        len_of_len = int(chr(data[1]))
        # Get data length
        data_len = int(data[2:2+len_of_len])
        # Extract image data
        img_data = data[2+len_of_len:2+len_of_len+data_len]

        # Save to file
        with open(filename, "wb") as f:
            f.write(img_data)

        print(f"Screenshot saved to: {filename}")
        print(f"Image size: {len(img_data)} bytes")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    # Use filename from command line if provided
    filename = sys.argv[1] if len(sys.argv) > 1 else None
    take_screenshot(filename)
