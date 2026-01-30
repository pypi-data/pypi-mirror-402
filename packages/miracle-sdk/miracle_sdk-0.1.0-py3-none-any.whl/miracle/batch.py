import pandas as pd
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from .client import Miracle
import time

class MiracleBatch:
    def __init__(self, max_workers: int = 10):
        self.client = Miracle()
        self.max_workers = max_workers

    def process_csv(self, 
                    file_path: str, 
                    domain: str, 
                    mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Reads a CSV file and processes each row against the MIRACLE API in parallel.
        
        Args:
            file_path: Path to the input CSV file.
            domain: The API domain to query (e.g., 'Pediatric_Ventricle').
            mapping: A dictionary mapping API parameter names to CSV column names.
                     Example: {'ht_cm': 'Height_cm', 'wt_kg': 'Weight_kg'}
                     If None, assumes CSV headers match API parameters exactly.
                     
        Returns:
            pd.DataFrame: Original DataFrame with new 'miracle_results' columns.
        """
        df = pd.read_csv(file_path)
        
        # Validate that mapped columns exist
        mapping = mapping or {}
        
        # Helper to process a single row
        def process_row(index: int, row: pd.Series) -> Dict[str, Any]:
            params = {'domain': domain}
            
            # Construct API params from row
            for api_key, csv_col in mapping.items():
                if csv_col in row:
                    params[api_key] = row[csv_col]
            
            # Also include any columns that match API keys directly if not in mapping
            # This is a bit loose but helpful. Ideally user provides mapping.
            # For strictness we could rely only on mapping + direct matches.
            for col in df.columns:
                if col not in mapping.values(): # It's an unmapped column
                     # If the column name happens to be a valid param (like 'gender'), pass it
                     # But we don't know validity easily here without checking generated client schema
                     # Let's just pass everything that looks like a keyword? 
                     # Better: Pass mapping + fallback to column name == api name
                     params[col] = row[col]

            # Clean params (remove NaNs)
            clean_params = {k: v for k, v in params.items() if pd.notna(v)}
            
            try:
                # We access the private method to bypass strict method signatures for flexibility
                # This allows 'MiracleBatch' to support future / unknown domains dynamically
                result = self.client._make_request(clean_params)
                return {**result, '__index__': index}
            except Exception as e:
                return {'error': str(e), '__index__': index}

        results_list = []
        
        print(f"Processing {len(df)} rows with {self.max_workers} threads...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create a list of futures
            futures = [executor.submit(process_row, i, row) for i, row in df.iterrows()]
            
            for future in as_completed(futures):
                res = future.result()
                results_list.append(res)
        
        # Sort results back to original order
        results_list.sort(key=lambda x: x['__index__'])
        
        # Convert results to DataFrame and merge
        results_df = pd.DataFrame(results_list)
        results_df.drop(columns=['__index__'], inplace=True, errors='ignore')
        
        # Prefix result columns to avoid collision
        results_df = results_df.add_prefix('miracle_')
        
        return pd.concat([df, results_df], axis=1)
