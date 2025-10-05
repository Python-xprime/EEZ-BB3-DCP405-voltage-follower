#!/usr/bin/env python3
"""
DMM6500 Screenshot Tool - Selenium Method
Captures screenshots from DMM6500 via web interface using browser automation

Requirements:
    pip install selenium

Also requires a WebDriver (one of):
    - Chrome/Chromium + chromedriver
    - Firefox + geckodriver
    - Edge + msedgedriver
"""

import sys
import time
import base64
from datetime import datetime
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("ERROR: Selenium not installed")
    print("Please install it with: pip install selenium")
    print("\nAlso install a WebDriver:")
    print("  Chrome:   https://chromedriver.chromium.org/")
    print("  Firefox:  https://github.com/mozilla/geckodriver/releases")
    print("  Edge:     https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
    sys.exit(1)

DMM6500_IP = "192.168.0.1"
USERNAME = "<your username (default admin, thank you Keithley for taking security seriously)>"
PASSWORD = "<your password (default admin, thank you Keithley for taking security seriously)>"

# Default browser based on platform
import platform
DEFAULT_BROWSER = 'edge' if platform.system() == 'Windows' else 'chrome'

def create_driver(headless=True, browser=DEFAULT_BROWSER):
    """Create and configure WebDriver"""

    try:
        if browser.lower() == 'chrome':
            options = ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)

        elif browser.lower() == 'firefox':
            options = FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)

        elif browser.lower() == 'edge':
            options = EdgeOptions()
            if headless:
                options.add_argument('--headless')
            driver = webdriver.Edge(options=options)

        else:
            raise ValueError(f"Unsupported browser: {browser}")

        return driver

    except WebDriverException as e:
        print(f"ERROR: Could not create {browser} WebDriver")
        print(f"Details: {e}")
        print("\nMake sure you have the WebDriver installed:")
        print("  Chrome:   chromedriver in PATH")
        print("  Firefox:  geckodriver in PATH")
        print("  Edge:     msedgedriver in PATH")
        return None

def take_screenshot(filename=None, ip=DMM6500_IP, username=USERNAME, password=PASSWORD,
                   headless=True, browser='chrome', wait_time=3, fullpage=True):
    """Capture screenshot from DMM6500 web interface using Selenium"""

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dmm6500_screenshot_{timestamp}.png"

    print(f"Connecting to DMM6500 at {ip}...")

    driver = None
    try:
        # Create WebDriver
        driver = create_driver(headless=headless, browser=browser)
        if driver is None:
            return False

        # Navigate to front panel page with authentication
        # Build URL with embedded credentials
        auth_url = f"http://{username}:{password}@{ip}/front_panel.html"

        print("Loading web interface...")
        driver.get(auth_url)

        # Wait for canvas to be present and loaded
        print("Waiting for display canvas to load...")
        wait = WebDriverWait(driver, 10)
        canvas = wait.until(
            EC.presence_of_element_located((By.ID, "DisplayCanvas"))
        )

        # Wait a bit for the image to be drawn on canvas
        time.sleep(wait_time)

        # Get screenshot
        print("Capturing screenshot...")

        if fullpage:
            # Capture the virtual front panel only (not the entire webpage)
            # The "bumper" div contains left, center, and right sections
            try:
                front_panel = driver.find_element(By.ID, "bumper")
            except:
                # Fallback to contentWrapper if bumper not found
                try:
                    front_panel = driver.find_element(By.ID, "contentWrapper")
                except:
                    # Last resort - capture full page
                    image_data = driver.get_screenshot_as_png()
                    return True

            # Make sure browser window is wide enough to show all panels
            driver.set_window_size(1920, 1080)
            time.sleep(0.5)  # Wait for resize

            # Screenshot the specific element
            image_data = front_panel.screenshot_as_png
        else:
            # Capture only the canvas content (display screen only)
            canvas_data_url = driver.execute_script("""
                var canvas = document.getElementById('DisplayCanvas');
                return canvas.toDataURL('image/png');
            """)

            # Extract base64 data from data URL
            if not canvas_data_url.startswith('data:image/png;base64,'):
                print("ERROR: Could not extract image data from canvas")
                return False

            base64_data = canvas_data_url.split(',', 1)[1]
            image_data = base64.b64decode(base64_data)

        # Save to file
        with open(filename, 'wb') as f:
            f.write(image_data)

        print(f"Screenshot saved to: {filename}")
        print(f"Image size: {len(image_data)} bytes")
        print(f"Format: PNG")
        print(f"Mode: {'Full page' if fullpage else 'Canvas only'}")
        return True

    except TimeoutException:
        print("ERROR: Timeout waiting for page elements")
        print("The web interface may not be responding correctly")
        return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Capture screenshot from DMM6500 web interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python take_screenshot_dmm6500.py
  python take_screenshot_dmm6500.py my_screenshot.png
  python take_screenshot_dmm6500.py --browser firefox --no-headless
  python take_screenshot_dmm6500.py --wait 5
        """
    )

    parser.add_argument('filename', nargs='?',
                       help='Output filename (default: auto-generated .png file)')
    parser.add_argument('--ip', default=DMM6500_IP,
                       help=f'DMM6500 IP address (default: {DMM6500_IP})')
    parser.add_argument('--user', default=USERNAME,
                       help=f'Username (default: {USERNAME})')
    parser.add_argument('--password', default=PASSWORD,
                       help=f'Password (default: {PASSWORD})')
    parser.add_argument('--browser', default=DEFAULT_BROWSER,
                       choices=['chrome', 'firefox', 'edge'],
                       help=f'Browser to use (default: {DEFAULT_BROWSER})')
    parser.add_argument('--no-headless', action='store_true',
                       help='Show browser window (default: run headless)')
    parser.add_argument('--wait', type=float, default=3.0,
                       help='Wait time in seconds for display to load (default: 3)')
    parser.add_argument('--canvas-only', action='store_true',
                       help='Capture only the front panel canvas (default: full page)')

    args = parser.parse_args()

    success = take_screenshot(
        filename=args.filename,
        ip=args.ip,
        username=args.user,
        password=args.password,
        headless=not args.no_headless,
        browser=args.browser,
        wait_time=args.wait,
        fullpage=not args.canvas_only
    )

    sys.exit(0 if success else 1)
