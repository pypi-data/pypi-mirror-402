import os
import time
import pyautogui

code = "C02E-A617"
url = "https://github.com/login/device"

print(f"Opening {url}...")
os.system(f'start chrome "{url}"')

print("Waiting for page load...")
time.sleep(5) 

print(f"Typing code: {code}")
pyautogui.write(code, interval=0.1)

print("Submitting...")
time.sleep(1)
pyautogui.press('enter')

print("Waiting for Authorize screen...")
time.sleep(3)
# Usually need to click "Authorize github"
# Tab navigation is safer than coordinates
pyautogui.press('tab')
pyautogui.press('tab') # Often needs a few tabs to reach button
# Blind Enter might work if focus is right
pyautogui.press('enter')

print("Done.")
