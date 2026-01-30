import sys
import os
import json

# Ensure we can import the local package
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../src"))
sys.path.append(PROJECT_ROOT)

from miracle import Miracle

def smoke_test_athletes():
    print("🏃‍♂️ Starting Smoke Test: Athlete Domain...")
    
    client = Miracle()
    
    # Test Case: Male Athlete, 15 hours/week of sports, checking LVEDV
    # We expect some reference range output
    try:
        result = client.athlete_reference_values(
            parameter="LVEDV",
            gender="Male",
            sport_act_hrs=15.0
        )
        
        print("\n✅ API Call Successful!")
        print("Response:")
        print(json.dumps(result, indent=2))
        
        if "error" in result:
             print("\n⚠️ API returned an error payload.")
             sys.exit(1)
             
    except Exception as e:
        print(f"\n❌ API Call Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    smoke_test_athletes()
