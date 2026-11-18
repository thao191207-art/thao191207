import subprocess
import os
import shutil
import tempfile
import time

CHROME_PATH = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
BASE_URL = "http://127.0.0.1:5000"
ARTIFACT_DIR = r"C:\Users\ADMIIN\.gemini\antigravity\brain\858e13ad-90d2-4345-b41b-8b68df6db24e"
OUT_DIR = r"C:\Users\ADMIIN\Downloads\AI301\screenshots"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

targets = [
    ("dashboard_1366", "#/tong-quan", (1366, 900)),
    ("records_1366", "#/ho-so", (1366, 900)),
    ("kanban_1366", "#/kanban", (1366, 900)),
    ("design_system_1366", "#/thiet-ke", (1366, 1100)),
    ("dashboard_768", "#/tong-quan", (768, 1024)),
    ("dashboard_390", "#/tong-quan", (390, 844)),
]

print("Starting clean screenshot capture...")
temp_profile = tempfile.mkdtemp(prefix="chrome_clean_")

for name, route, (w, h) in targets:
    url = f"{BASE_URL}/{route}"
    out_path = os.path.join(OUT_DIR, f"{name}.png")
    art_path = os.path.join(ARTIFACT_DIR, f"{name}.png")
    
    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        f"--user-data-dir={temp_profile}",
        "--disk-cache-size=0",
        f"--window-size={w},{h}",
        f"--screenshot={out_path}",
        "--virtual-time-budget=4000",
        url
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(out_path):
        size = os.path.getsize(out_path)
        print(f"Captured {name} ({w}x{h}): {size} bytes -> {out_path}")
        with open(out_path, "rb") as f_in, open(art_path, "wb") as f_out:
            f_out.write(f_in.read())
    else:
        print(f"Failed {name}: {res.stderr}")

shutil.rmtree(temp_profile, ignore_errors=True)
print("Screenshot capture completed.")
