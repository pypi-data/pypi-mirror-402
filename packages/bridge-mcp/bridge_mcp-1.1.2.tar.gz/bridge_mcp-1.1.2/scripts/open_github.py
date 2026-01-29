import os
import time
import pyautogui

# URL to "Rules" settings (Common place for push blocks)
url = "https://github.com/BarhamAgha1/Bridge-MCP/settings/rules"

print(f"Opening {url}...")
# Use 'start' to open in default browser (User's daily chrome)
os.system(f'start chrome "{url}"')

# Wait for load
time.sleep(3)

# Take initial screenshot to see where we are
screenshot_path = "debug_view.png"
pyautogui.screenshot(screenshot_path)
print(f"Screenshot saved to {screenshot_path}")
