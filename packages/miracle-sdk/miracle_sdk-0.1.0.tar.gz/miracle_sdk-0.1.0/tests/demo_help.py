import sys
import os

# Ensure we can import the local package
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../src"))
sys.path.append(PROJECT_ROOT)

from miracle import Miracle

print("--- RAW DOCSTRING OUTPUT ---")
help(Miracle.pediatric_ventricle_reference_values)
print("--- END DOCSTRING OUTPUT ---")
