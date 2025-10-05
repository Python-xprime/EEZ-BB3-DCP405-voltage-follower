"""
DCP405 Voltage Follower Script
================================

Description:
    This script implements a voltage follower with adjustable offset.
    Channel 2 output follows Channel 1 input: Ch2 = Ch1 + offset

Required Hardware Configuration:
    - EEZ BB3 chassis
    - Slot 1: DCP405 module (used as input/measurement channel)
    - Slot 2: DCP405 module (used as output channel)

Features:
    - Real-time voltage following with configurable offset
    - Adjustable output current limit
    - Dynamic offset range based on input voltage
    - Automatic OVP (Over-Voltage Protection) disable on Ch2
    - Module compatibility check on startup

Usage:
    1. Connect input voltage source to Ch1
    2. Connect load to Ch2
    3. Run this script on BB3
    4. Click offset value to adjust (range: -Ch1 to +(40V-Ch1))
    5. Click current setting to adjust output current limit
    6. Press START to begin voltage following

Author: Claude AI Assistant
Date: 2025-10-05
Version: 1.0
"""

from utime import sleep_ms, ticks_ms, ticks_diff, ticks_add
from eez import scpi, setU, getU, getI

print("=== DCP405 VOLTAGE FOLLOWER START ===")

# Configuration variables
running = False
voltage_offset = 0.0
current_limit = 0.1
target_voltage_set = 0.0

def check_dcp405_modules():
    """Check if both Ch1 and Ch2 are DCP405 modules"""
    try:
        # Check Ch1
        scpi("INST:NSEL 1")
        ch1_model = scpi("SYST:CHAN:MODel?")

        # Check Ch2
        scpi("INST:NSEL 2")
        ch2_model = scpi("SYST:CHAN:MODel?")

        print("Ch1 model:", ch1_model)
        print("Ch2 model:", ch2_model)

        # Check if both are DCP405
        if ch1_model and "DCP405" in str(ch1_model) and ch2_model and "DCP405" in str(ch2_model):
            print("Module check: PASSED - Both channels are DCP405")
            return True
        else:
            print("Module check: FAILED")
            print("This script requires DCP405 modules in both Ch1 and Ch2")
            print("Ch1: " + str(ch1_model))
            print("Ch2: " + str(ch2_model))
            return False
    except Exception as e:
        print("Module check ERROR:", e)
        return False

def updateDisplay():
    """Update GUI with current measurements"""
    global voltage_offset, current_limit
    try:
        # Read real voltage from Channel 1 (input/source)
        scpi("INST:NSEL 1")
        ch1_voltage = getU(1)
        ch1_current = getI(1)

        # Read real voltage from Channel 2 (output)
        scpi("INST:NSEL 2")
        ch2_voltage = getU(2)
        ch2_current = getI(2)

        # Update GUI with REAL measured values
        scpi('DISP:DIAL:DATA "source_voltage",FLOAT,VOLT,' + str(ch1_voltage))
        scpi('DISP:DIAL:DATA "target_voltage",FLOAT,VOLT,' + str(ch2_voltage))
        scpi('DISP:DIAL:DATA "target_current",FLOAT,AMPER,' + str(ch2_current))

        # Update voltage offset display (3 decimals)
        offset_formatted = "{:.3f}".format(voltage_offset)
        scpi('DISP:DIAL:DATA "voltage_offset",FLOAT,VOLT,' + offset_formatted)

        # Update current limit display (3 decimals)
        current_formatted = "{:.3f}".format(current_limit)
        scpi('DISP:DIAL:DATA "current_limit",FLOAT,AMPER,' + current_formatted)

        return ch1_voltage, ch2_voltage, ch2_current
    except Exception as e:
        print("Display update ERROR:", e)
        return 0, 0, 0

def startControl():
    """Start voltage control"""
    global running
    print("START button pressed")
    running = True
    scpi('DISP:DIAL:DATA "status",STRING,"RUNNING"')

    # Enable output on Ch2
    scpi("INST:NSEL 2")
    scpi("CURR " + str(current_limit))
    scpi("OUTP 1")
    print("Output enabled")

def stopControl():
    """Stop voltage control"""
    global running
    print("STOP button pressed")
    running = False
    scpi('DISP:DIAL:DATA "status",STRING,"STOPPED"')

    # Disable output on Ch2
    scpi("INST:NSEL 2")
    scpi("OUTP 0")
    print("Output disabled")

def configVoltageOffset():
    """Configure voltage offset with dynamic range"""
    global voltage_offset
    print("Config Voltage Offset")

    # Get current source voltage to calculate valid range
    try:
        ch1_v = getU(1)

        # Calculate dynamic limits
        # Negative limit: -(source voltage) to reach 0V output
        # Positive limit: (40V - source voltage) to reach 40V output
        min_offset = -ch1_v
        max_offset = 40.0 - ch1_v

        value = scpi('DISP:INPUT? "Voltage Offset",NUMBER,VOLT,' +
                     str(min_offset) + ',' + str(max_offset) + ',' + str(voltage_offset))

        if value != None:
            voltage_offset = float(value)
            print("Offset: {:+.3f} V (Range: {:.3f} to {:.3f} V)".format(
                voltage_offset, min_offset, max_offset))
    except Exception as e:
        print("Offset config ERROR:", e)

def configCurrentLimit():
    """Configure current limit"""
    global current_limit
    print("Config Current Limit")
    value = scpi('DISP:INPUT? "Current Limit",NUMBER,AMPER,0.05,5,' + str(current_limit))
    if value != None:
        current_limit = float(value)
        scpi("INST:NSEL 2")
        scpi("CURR " + str(current_limit))
        print("Current limit set to:", current_limit)

# Check if both channels are DCP405 modules
if not check_dcp405_modules():
    print("ERROR: Module check failed. Exiting.")
    print("=== DCP405 VOLTAGE FOLLOWER END ===")
    exit()

# Disable OVP (Over-Voltage Protection) on Ch2
print("Disabling OVP on Ch2...")
try:
    scpi("INST:NSEL 2")
    scpi("VOLT:PROT:STAT 0")
    print("OVP disabled")
except Exception as e:
    print("OVP disable ERROR:", e)

# Open dialog
print("Opening dialog...")
try:
    scpi('DISP:DIAL:OPEN "/Scripts/DCP405_voltage_follower.res"')
    print("Dialog opened")
except Exception as e:
    print("Dialog open ERROR:", e)

# Initial display update
scpi('DISP:DIAL:DATA "status",STRING,"STOPPED"')
scpi('DISP:DIAL:DATA "voltage_offset",FLOAT,VOLT,0.000')
scpi('DISP:DIAL:DATA "current_limit",FLOAT,AMPER,' + "{:.3f}".format(current_limit))
updateDisplay()

# Main loop - handles button actions and updates display
print("Waiting for user actions...")
print("Voltage Follower Mode: Output = Input + Offset")

loop_count = 0
t = ticks_ms()

while True:
    try:
        # Calculate timeout until next update (like CapReform.py pattern)
        t_next = ticks_add(t, 500)
        timeout_ms = max(10, ticks_diff(t_next, ticks_ms()))  # At least 10ms

        # Check for button actions with CALCULATED timeout
        action = scpi("DISP:DIALog:ACTIon? " + str(timeout_ms) + "ms")

        if action == "start_control":
            startControl()
        elif action == "stop_control":
            stopControl()
        elif action == "config_voltage_offset":
            configVoltageOffset()
        elif action == "config_current_limit":
            configCurrentLimit()
        elif action == "close_dialog":
            print("Close requested by user")
            break

        # Update display with real values
        ch1_v, ch2_v, ch2_i = updateDisplay()

        if running:
            # Voltage follower mode: output = input + offset
            target_voltage_set = ch1_v + voltage_offset

            # Clamp to device limits (0-40V)
            if target_voltage_set < 0.0:
                target_voltage_set = 0.0
            elif target_voltage_set > 40.0:
                target_voltage_set = 40.0

            # Set output voltage
            scpi("INST:NSEL 2")
            setU(2, target_voltage_set)

        # Print status every 10 loops
        loop_count += 1
        if loop_count >= 10:
            status = "RUNNING" if running else "READY"
            print("{} | Offset: {:+.3f}V | Ch1: {:.3f}V | Ch2: {:.3f}V {:.3f}A".format(
                status, voltage_offset, ch1_v, ch2_v, ch2_i))
            loop_count = 0

        # Set next loop time
        t = t_next

    except Exception as e:
        print("Loop ERROR:", e)
        break

# Cleanup: stop output and close dialog
print("Cleaning up...")
try:
    scpi("INST:NSEL 2")
    scpi("OUTP 0")
    scpi("DISP:DIALog:CLOSe")
    print("Dialog closed, output disabled")
except Exception as e:
    print("Cleanup ERROR:", e)

print("=== DCP405 VOLTAGE FOLLOWER END ===")
