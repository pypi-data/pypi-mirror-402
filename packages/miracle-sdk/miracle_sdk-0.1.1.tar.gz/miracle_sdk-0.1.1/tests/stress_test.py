import sys
import os
import time
import pandas as pd

# Ensure we can import the local package
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../src"))
sys.path.append(PROJECT_ROOT)

try:
    from miracle import MiracleBatch
except ImportError:
    print("Could not import miracle. Make sure you are running from the project root.")
    sys.exit(1)

def run_stress_test():
    print("🚀 Starting Stress Test: 16 Requests to Pediatric_Ventricle...")
    
    # Initialize Batch Processor with 5 workers to be polite but fast
    processor = MiracleBatch(max_workers=5)
    
    mapping = {
        "gender": "gender",
        "ht_cm": "height_cm",
        "wt_kg": "weight_kg",
        "measured": "lvedv",
        "age": "age",
        "parameter": "parameter" # Mapping for the injected column
    }
    
    # Path to test data (now in same dir as script)
    input_csv = os.path.join(SCRIPT_DIR, "test_data.csv")
    
    # Pre-load CSV to inject the required argument 'parameter'
    df = pd.read_csv(input_csv)
    df['parameter'] = 'LVEDV'
    
    # Save temporary input file
    temp_input = os.path.join(SCRIPT_DIR, "temp_data_with_param.csv")
    df.to_csv(temp_input, index=False)
    
    start_time = time.time()
    
    result_df = processor.process_csv(
        file_path=temp_input,
        domain="Pediatric_Ventricle",
        mapping=mapping
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Clean up temp file
    if os.path.exists(temp_input):
        os.remove(temp_input)
    
    print(f"\n✅ Finished processing in {duration:.2f} seconds.")
    
    # Save results to CSV (What the user asked for)
    output_csv = os.path.join(SCRIPT_DIR, "stress_test_results.csv")
    result_df.to_csv(output_csv, index=False)
    print(f"\n💾 Results saved to: {output_csv}")
    
    print("\n📊 Results Preview:")
    # Show patient_id and select result columns
    cols_to_show = ['patient_id', 'miracle_calculated_sds', 'miracle_percentile', 'miracle_error']
    available_cols = [c for c in cols_to_show if c in result_df.columns]
    print(result_df[available_cols].to_string())

    # Check for errors
    if 'miracle_error' in result_df.columns:
        error_count = result_df['miracle_error'].notna().sum()
        if error_count > 0:
            print(f"\n⚠️ WARNING: {error_count} requests failed!")
            print(result_df[result_df['miracle_error'].notna()][['patient_id', 'miracle_error']])
        else:
            print("\n🎉 SUCCESS: 0 Failures. Cloudflare Proxy handled the load perfectly.")
    else:
        print("\n🎉 SUCCESS: No errors column generated (All good).")

if __name__ == "__main__":
    run_stress_test()
