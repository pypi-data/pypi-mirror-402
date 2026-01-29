import pyautogui
import time

print("Focusing Chrome (clicking center screen)...")
# Click to ensure focus
width, height = pyautogui.size()
pyautogui.click(width/2, height/2)

print("Navigating to Authorize...")
# Try different tab sequences
for i in range(5):
    pyautogui.press('tab')
    
pyautogui.press('enter')
time.sleep(1)
pyautogui.press('enter')
