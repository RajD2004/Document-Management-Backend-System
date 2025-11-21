import os
import subprocess

SOURCE_DIR = "released-cases"  # change this to your target folder

for filename in os.listdir(SOURCE_DIR):
    if filename.endswith(".py") and filename != os.path.basename(__file__):
        path = os.path.join(SOURCE_DIR, filename)
        print(f"\n=== Running: {filename} ===")
        result = subprocess.run(["python3", path], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:\n", result.stderr)
