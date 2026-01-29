import uiautomation as auto
import json
import time

def dump_node(control, depth=0):
    if depth > 5: return None
    try:
        data = {
            "Name": control.Name,
            "ControlType": control.ControlTypeName,
            "Rect": f"{control.BoundingRectangle}",
            "Children": []
        }
        for child in control.GetChildren():
            child_data = dump_node(child, depth + 1)
            if child_data:
                data["Children"].append(child_data)
        return data
    except:
        return None

# Find Chrome
print("Looking for Chrome...")
chrome_window = auto.WindowControl(searchDepth=1, ClassName="Chrome_WidgetWin_1")
if not chrome_window.Exists(3, 1):
    print("Chrome not found")
    exit(1)

print(f"Found Chrome: {chrome_window.Name}")
chrome_window.SetFocus()

# Try to find the "Rulesets" or "Settings" content
# Web content is usually in a "Document" control
doc = chrome_window.DocumentControl()
if doc.Exists(3, 1):
    print("Found Document, scanning content (this fails if accessibility disabled)...")
    # Quick scan for keywords
    rules = doc.CustomControl(Name="Rules", subdir=True) # Heuristic
    # Just list top level text
    text = []
    for item in doc.GetChildren():
        text.append(item.Name)
    print("Top level content:", text)

else:
    print("Document control not accessible via UIA.")
