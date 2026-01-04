from typing import Dict

def calculate_base_dqs(dimension_scores: Dict[str, float], weights: Dict[str, float] = None) -> float:
    """
    Calculates the Universal Immutable Base Data Quality Score (DQS).
    Formula: DQS_base = Sum(w_d * S_d)

    Args:
        dimension_scores (dict): Dictionary of dimension scores (0-100).
        weights (dict, optional): Dictionary of weights. Must sum to 1.0. 
                                  If None, equal weights are used.

    Returns:
        float: The composite DQS (0-100), rounded to 2 decimals.
        
    Raises:
        ValueError: If weights do not sum to approx 1.0.
    """
    required_dimensions = [
        'accuracy', 'completeness', 'consistency', 
        'timeliness', 'uniqueness', 'validity', 'integrity'
    ]
    
    # ensure all dimensions are present, default to 0.0 if missing (conservative)
    scores = {dim: dimension_scores.get(dim, 0.0) for dim in required_dimensions}
    
    if weights is None:
        # Default Equal Weights: 1/7
        val = 1.0 / 7.0
        weights = {dim: val for dim in required_dimensions}
    else:
        # Validate Weights
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.001: # float tolerance
            raise ValueError(f"Weights must sum to 1.0. Current sum: {total_weight}")
            
    # Calculate Weighted Sum
    dqs_base = sum(scores[dim] * weights.get(dim, 0.0) for dim in required_dimensions)
    
    return round(dqs_base, 2)

if __name__ == "__main__":
    # Example Usage
    sample_scores = {
        'accuracy': 95.5,
        'completeness': 80.0,
        'consistency': 100.0,
        'timeliness': 90.0,
        'uniqueness': 85.0,
        'validity': 100.0,
        'integrity': 100.0
    }
    
    # Case 1: Equal weights
    dqs = calculate_base_dqs(sample_scores)
    print(f"Base DQS (Equal Weights): {dqs}")
    
    # Case 2: Custom Weights (e.g. Focus on Integrity/Uniqueness for Payments)
    # Payment Profile: Validity(0.2), Integrity(0.2), Uniqueness(0.2), others(0.1)
    custom_weights = {
        'accuracy': 0.1,
        'completeness': 0.1,
        'consistency': 0.1,
        'timeliness': 0.1,
        'uniqueness': 0.2,
        'validity': 0.2,
        'integrity': 0.2
    }
    dqs_custom = calculate_base_dqs(sample_scores, weights=custom_weights)
    print(f"Base DQS (Payment Weights): {dqs_custom}")
