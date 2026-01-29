import sys
import io
import os

# Capture stdout
old_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
    # Try importing server modules to see if they print anything
    import kerykeion
    from kerykeion import AstrologicalSubjectFactory
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")

# Restore stdout
captured = sys.stdout.getvalue()
sys.stdout = old_stdout

if captured.strip():
    print(f"POLLUTION DETECTED:\n{captured}")
else:
    print("No stdout pollution on import.")

# Check stderr too, though MCP tolerates stderr usually
# Kerykeion warning seemed to be logging, which goes to stderr by default.
# But if it uses print, it would be here.
