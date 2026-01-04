import pandas as pd
import hashlib
import io
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class DatasetMetadata:
    """
    Immutable data structure to hold dataset metadata.
    NO RAW DATA is stored here.
    """
    column_names: List[str]
    data_types: Dict[str, str]
    row_count: int
    null_counts: Dict[str, int]
    unique_counts: Dict[str, int]
    numeric_stats: Dict[str, Dict[str, float]] # min, max, mean
    timestamp_metrics: Dict[str, Dict[str, Any]] # min_time, max_time
    semantic_hints: Dict[str, str] = field(default_factory=dict) # inferred types e.g. 'ID', 'AMOUNT'
    signals: Dict[str, bool] = field(default_factory=dict) # High-level dataset signals
    audit_hash: str = ""

def load_dataset(source: str) -> pd.DataFrame:
    """
    Loads a dataset from a CSV source.
    
    Args:
        source (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: Loaded dataframe.
        
    Raises:
        ValueError: If file format is not supported or file is empty.
    """
    if not source.endswith('.csv'):
        raise ValueError("Only CSV format is supported in this version.")
    
    try:
        df = pd.read_csv(source)
    except Exception as e:
        raise ValueError(f"Failed to load CSV: {e}")
        
    if df.empty:
        raise ValueError("Dataset is empty.")
        
    return df

def _infer_semantic_hint(col_name: str, dtype: str) -> str:
    """
    Simple heuristic to infer column semantic type.
    In the full system, this would be augmented by GenAI.
    """
    col_lower = col_name.lower()
    
    if 'id' in col_lower or 'code' in col_lower or 'number' in col_lower:
        return 'ID'
    if 'amount' in col_lower or 'price' in col_lower or 'balance' in col_lower or 'fee' in col_lower:
        return 'MONEY'
    if 'date' in col_lower or 'time' in col_lower or 'created' in col_lower:
        return 'TIMESTAMP'
    if 'status' in col_lower or 'state' in col_lower or 'type' in col_lower:
        return 'CATEGORY'
    
    return 'UNKNOWN'

def extract_metadata(df: pd.DataFrame) -> DatasetMetadata:
    """
    Extracts statistical metadata from the dataframe.
    Calculates SHA-256 hash of the metadata for audit.
    
    Args:
        df (pd.DataFrame): The input dataframe.
        
    Returns:
        DatasetMetadata: The extracted metadata object.
    """
    column_names = list(df.columns)
    data_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
    row_count = len(df)
    
    null_counts = df.isnull().sum().to_dict()
    unique_counts = df.nunique().to_dict()
    
    numeric_stats = {}
    timestamp_metrics = {}
    semantic_hints = {}
    
    for col in df.columns:
        # Semantic Inference
        semantic_hints[col] = _infer_semantic_hint(col, data_types[col])
        
        # Numeric Stats
        if pd.api.types.is_numeric_dtype(df[col]):
            desc = df[col].describe()
            numeric_stats[col] = {
                'min': float(desc['min']) if not pd.isna(desc['min']) else 0.0,
                'max': float(desc['max']) if not pd.isna(desc['max']) else 0.0,
                'mean': float(desc['mean']) if not pd.isna(desc['mean']) else 0.0
            }
            
        # Timestamp metrics (attempt conversion if object/string looks like date)
        # Note: In a real robust system, we would attempt pd.to_datetime inside a try-block
        if 'date' in col.lower() or 'time' in col.lower() or pd.api.types.is_datetime64_any_dtype(df[col]):
            try:
                # Create temporary series for calculation
                ts_series = pd.to_datetime(df[col], errors='coerce')
                valid_ts = ts_series.dropna()
                if not valid_ts.empty:
                    timestamp_metrics[col] = {
                        'min_time': valid_ts.min(),
                        'max_time': valid_ts.max(),
                        'range_seconds': (valid_ts.max() - valid_ts.min()).total_seconds()
                    }
                    semantic_hints[col] = 'TIMESTAMP' # Force update constraint
            except Exception:
                pass # Ignore if conversion fails

    # Calculate Signals
    hints = semantic_hints.values()
    cols_lower = [c.lower() for c in column_names]
    
    has_transaction_id = 'ID' in hints
    has_amount = 'MONEY' in hints
    has_timestamp = 'TIMESTAMP' in hints
    
    # KYC heuristics
    kyc_terms = ['user', 'customer', 'email', 'address', 'ip', 'phone', 'kyc', 'name']
    has_kyc = any(any(term in col for term in kyc_terms) for col in cols_lower)
    
    # Text Heavy heuristic
    text_cols = [col for col, dtype in data_types.items() if 'object' in str(dtype) or 'string' in str(dtype)]
    # Filter out semantic columns
    plain_text_cols = [c for c in text_cols if semantic_hints[c] not in ['ID', 'TIMESTAMP', 'MONEY']]
    is_text_heavy = (len(plain_text_cols) / len(column_names) > 0.5) if column_names else False
    
    signals = {
        'has_transaction_id': has_transaction_id,
        'has_amount': has_amount,
        'has_timestamp': has_timestamp,
        'has_kyc': has_kyc,
        'is_text_heavy': is_text_heavy
    }

    # Create Audit Hash (hashing the string representation of core stats)
    audit_payload = f"{column_names}{row_count}{null_counts}{unique_counts}{signals}"
    audit_hash = hashlib.sha256(audit_payload.encode()).hexdigest()
    
    metadata = DatasetMetadata(
        column_names=column_names,
        data_types=data_types,
        row_count=row_count,
        null_counts=null_counts,
        unique_counts=unique_counts,
        numeric_stats=numeric_stats,
        timestamp_metrics=timestamp_metrics,
        semantic_hints=semantic_hints,
        signals=signals,
        audit_hash=audit_hash
    )
    
    return metadata

if __name__ == "__main__":
    # Example usage
    import pandas as pd
    try:
        # Create dummy data for test
        data = {
            'transaction_id': ['TX1', 'TX2', 'TX3', 'TX1'], # Duplicate ID
            'amount': [100.50, -50.00, 200.00, 100.50],     # Negative amount
            'timestamp': ['2023-01-01', '2023-01-02', None, '2023-01-01'], # Missing time
            'status': ['SUCCESS', 'FAIL', 'PENDING', 'SUCCESS']
        }
        df_dummy = pd.DataFrame(data)
        
        # In a real run, we would load from file:
        # df = load_dataset('payments.csv')
        
        meta = extract_metadata(df_dummy)
        print("Metadata Extracted Successfully:")
        print(f"Columns: {meta.column_names}")
        print(f"Row Count: {meta.row_count}")
        print(f"Audit Hash: {meta.audit_hash}")
        print(f"Semantic Hints: {meta.semantic_hints}")
        print(f"Numeric Stats: {meta.numeric_stats}")
        
    except Exception as e:
        print(f"Error: {e}")
