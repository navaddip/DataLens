import logging
import datetime
from ingestion import DatasetMetadata

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def score_completeness(metadata: DatasetMetadata) -> float:
    """
    Calculates Completeness Score: Percentage of non-null values across all columns.
    Future: Could apply weights to 'critical' columns if defined in semantics.
    """
    total_cells = metadata.row_count * len(metadata.column_names)
    if total_cells == 0:
        return 0.0
    
    total_nulls = sum(metadata.null_counts.values())
    completeness_ratio = (total_cells - total_nulls) / total_cells
    score = completeness_ratio * 100
    logging.info(f"Completeness Score: {score:.2f}")
    return max(0.0, min(100.0, score))

def score_uniqueness(metadata: DatasetMetadata) -> float:
    """
    Calculates Uniqueness Score:
    Focuses on identified 'ID' columns. If no ID columns found, defaults to 100 (benefit of doubt) or heuristic check.
    Penalizes duplicates in ID columns.
    """
    id_cols = [col for col, hint in metadata.semantic_hints.items() if hint == 'ID']
    
    if not id_cols:
        logging.info("Uniqueness: No ID columns found. Defaulting to 100.")
        return 100.0
    
    # Average uniqueness across all ID columns
    total_uniqueness_ratio = 0.0
    for col in id_cols:
        unique_vals = metadata.unique_counts.get(col, 0)
        # Ratio of unique values to total rows. 
        # If perfect, unique_vals == row_count -> raio = 1.0
        ratio = unique_vals / metadata.row_count if metadata.row_count > 0 else 0
        total_uniqueness_ratio += ratio
        
    avg_ratio = total_uniqueness_ratio / len(id_cols)
    score = avg_ratio * 100
    logging.info(f"Uniqueness Score: {score:.2f} (Based on cols: {id_cols})")
    return max(0.0, min(100.0, score))

def score_validity(metadata: DatasetMetadata) -> float:
    """
    Calculates Validity Score:
    - Checks Numeric 'MONEY' columns for negative values (simple validity rule).
    - Future: Domain specific checks (e.g. Country codes).
    """
    money_cols = [col for col, hint in metadata.semantic_hints.items() if hint == 'MONEY']
    
    if not money_cols:
        return 100.0 # No money columns to validate
        
    validity_points = 0
    total_checks = 0
    
    for col in money_cols:
        total_checks += 1
        stats = metadata.numeric_stats.get(col, {})
        min_val = stats.get('min', 0)
        
        # Rule: Transaction amounts should generally be positive. 
        # (Note: Refunds might be negative in some datasets, but usually flagged separately. 
        # For this base scorer, we assume standard +ve amounts or penalize slightly).
        # To be safe and explainable: We only penalize if min is distinctly negative without context.
        # Let's assume for this specific agent: "Payments" -> Amount > 0.
        if min_val >= 0:
            validity_points += 1
        else:
            # Partial penalty if invalid values exist. 
            # Since we don't have row-level validity counts, we penalize the column level heavily if min < 0.
            # In a real system, we'd count invalid rows. Here we have stats.
            validity_points += 0.5 # giving 50% for the column if range is suspicious
            
    score = (validity_points / total_checks) * 100
    logging.info(f"Validity Score: {score:.2f}")
    return score

def score_accuracy(metadata: DatasetMetadata) -> float:
    """
    Calculates Accuracy Score (Proxy):
    - Checks schema adherence.
    - If a column is heuristically 'MONEY' but dtype is 'object' (string), it's a potential accuracy/type error.
    - If 'TIMESTAMP' is not datetime compatible, it's an error.
    """
    total_cols = len(metadata.column_names)
    if total_cols == 0:
        return 0.0
    
    accurate_cols = 0
    
    for col in metadata.column_names:
        hint = metadata.semantic_hints.get(col, 'UNKNOWN')
        dtype = metadata.data_types.get(col, '').lower()
        
        is_accurate = True
        
        if hint == 'MONEY':
            if 'int' not in dtype and 'float' not in dtype:
                is_accurate = False # likely string with currency symbol -> bad raw accuracy
        
        if hint == 'TIMESTAMP':
            # In metadata, we tried to convert. If timestamp_metrics has no entry for this col, it failed valid conversion.
            if col not in metadata.timestamp_metrics:
                is_accurate = False
                
        if is_accurate:
            accurate_cols += 1
            
    score = (accurate_cols / total_cols) * 100
    logging.info(f"Accuracy Score: {score:.2f}")
    return score

def score_consistency(metadata: DatasetMetadata) -> float:
    """
    Calculates Consistency Score:
    - Measures standard deviation / scale consistency is hard without raw data.
    - Proxy: Check if 'CATEGORY' columns have reasonable cardinality (not unique per row, not single value).
    """
    cat_cols = [col for col, hint in metadata.semantic_hints.items() if hint == 'CATEGORY']
    
    if not cat_cols:
        return 100.0
        
    consistent_cols = 0
    for col in cat_cols:
        unique = metadata.unique_counts.get(col, 0)
        total = metadata.row_count
        
        # Rule: Categories should be consistent groups. If unique == total (it's an ID), or unique == 0.
        # We expect cardinality << row_count.
        if 0 < unique < total:
            consistent_cols += 1
        else:
            # If unique == total, it's not a consistent category (it's messy or an ID).
            consistent_cols += 0.5 
            
    score = (consistent_cols / len(cat_cols)) * 100
    logging.info(f"Consistency Score: {score:.2f}")
    return score

def score_timeliness(metadata: DatasetMetadata) -> float:
    """
    Calculates Timeliness Score:
    - Checks gap between max_timestamp in data and 'now'.
    - If gap is huge (> 1 year) -> penalize (Old data).
    - If no timestamps found but expected -> penalize.
    """
    ts_cols = metadata.timestamp_metrics.keys()
    
    if not ts_cols:
        # If we expected timestamps (e.g. inference said so) but extraction failed -> 0.
        # If no timestamp columns existed at all -> Neutral 100? Or N/A?
        # Let's say neutral if no time inferred.
        if 'TIMESTAMP' in metadata.semantic_hints.values():
             return 50.0 # Detected but malformed
        return 100.0

    scores = []
    now = datetime.datetime.now()
    
    for col in ts_cols:
        metrics = metadata.timestamp_metrics[col]
        max_time = metrics['max_time']
        
        # Simple Recency Score
        delta_days = (now - max_time).days
        
        if delta_days < 0:
             # Future date! Data Quality Error.
             scores.append(0.0)
        elif delta_days <= 1:
            scores.append(100.0) # Real-time
        elif delta_days <= 30:
            scores.append(90.0) # Fresh
        elif delta_days <= 365:
            scores.append(70.0) # Historical
        else:
            scores.append(40.0) # Stale / Archival
            
    score = sum(scores) / len(scores)
    logging.info(f"Timeliness Score: {score:.2f}")
    return score

def score_integrity(metadata: DatasetMetadata) -> float:
    """
    Calculates Integrity Score:
    - Checks for orphan records? (Hard without multi-table).
    - Checks logical integrity: If hints 'DEBIT' and 'CREDIT' exist, check sum balance? 
    - For single file: Check nulls in ID columns (Entity Integrity).
    """
    id_cols = [col for col, hint in metadata.semantic_hints.items() if hint == 'ID']
    
    if not id_cols:
        return 100.0
        
    integrity_scores = []
    for col in id_cols:
        nulls = metadata.null_counts.get(col, 0)
        if nulls == 0:
            integrity_scores.append(100.0)
        else:
            # Penalize heavily for null IDs
            integrity_scores.append(max(0, 100 - (nulls / metadata.row_count * 200))) # *200 to punish null IDs harder
    
    score = sum(integrity_scores) / len(integrity_scores)
    logging.info(f"Integrity Score: {score:.2f}")
    return score

def calculate_all_dimensions(metadata: DatasetMetadata) -> dict:
    """Runs all scoring functions and returns a dict of scores."""
    return {
        'accuracy': score_accuracy(metadata),
        'completeness': score_completeness(metadata),
        'consistency': score_consistency(metadata),
        'timeliness': score_timeliness(metadata),
        'uniqueness': score_uniqueness(metadata),
        'validity': score_validity(metadata),
        'integrity': score_integrity(metadata)
    }

if __name__ == "__main__":
    # Test stub
    from ingestion import DatasetMetadata
    
    # Mock metadata for testing
    meta = DatasetMetadata(
        column_names=['id', 'amount', 'date'],
        data_types={'id': 'object', 'amount': 'float64', 'date': 'object'},
        row_count=100,
        null_counts={'id': 0, 'amount': 5, 'date': 0},
        unique_counts={'id': 98, 'amount': 50, 'date': 10}, # 2 dupe IDs
        numeric_stats={'amount': {'min': -10.0, 'max': 500.0, 'mean': 100.0}}, # Negative min -> Validity penalty
        timestamp_metrics={'date': {'max_time': datetime.datetime.now() - datetime.timedelta(days=10)}}, # 10 days old
        semantic_hints={'id': 'ID', 'amount': 'MONEY', 'date': 'TIMESTAMP'}
    )
    
    scores = calculate_all_dimensions(meta)
    print("Dimension Scores:", scores)
