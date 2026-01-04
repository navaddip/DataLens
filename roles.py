import logging
from typing import Dict, Any, Tuple, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _make_weights(focus_map: Dict[str, float]) -> Dict[str, float]:
    """Helper to distribute weights."""
    dims = ['accuracy', 'completeness', 'consistency', 'timeliness', 'uniqueness', 'validity', 'integrity']
    current_sum = sum(focus_map.values())
    remaining = 1.0 - current_sum
    start_count = len(dims) - len(focus_map)
    weights = {}
    for d in dims:
        weights[d] = focus_map.get(d, remaining / start_count if start_count > 0 else 0.0)
    return weights

# Define Profiles at Module Level
PROFILES = {
    "Data Engineer": {
        "description": "Focuses on pipeline reliability, schema adherence, and completeness.",
        "risk_level": "Technical",
        "weights": _make_weights({'completeness': 0.25, 'integrity': 0.25, 'accuracy': 0.2}),
        "critical_dimensions": ["completeness", "integrity", "accuracy"],
        "risk_threshold": 80,
        "required_signals": [] # Always applicable
    },
    "Data Scientist": {
        "description": "Needs clean distributions, consistent history, and valid values for modeling.",
        "risk_level": "Model Performance",
        "weights": _make_weights({'consistency': 0.25, 'validity': 0.2, 'completeness': 0.2}),
        "critical_dimensions": ["consistency", "validity", "completeness"],
        "risk_threshold": 75,
        "required_signals": [] # Always applicable
    },
    "Fraud Analyst": {
        "description": "Detects anomalies; relies on unique identities and real-time signals.",
        "risk_level": "High Operational",
        "weights": _make_weights({'uniqueness': 0.3, 'timeliness': 0.3, 'validity': 0.1}),
        "critical_dimensions": ["uniqueness", "timeliness"],
        "risk_threshold": 75,
        "required_signals": ["has_transaction_id"] # ID is bare minimum implies payment/user entity
    },
    "Compliance Officer": {
        "description": "Strict adherence to rules (KYC), accuracy of records, and data integrity.",
        "risk_level": "Regulatory",
        "weights": _make_weights({'accuracy': 0.25, 'integrity': 0.25, 'completeness': 0.2}),
        "critical_dimensions": ["accuracy", "integrity", "validity"],
        "risk_threshold": 85,
        "required_signals": ["has_kyc"] # Needs user info
    }, 
    "Finance / Settlement": {
        "description": "Zero tolerance for accuracy errors in amounts and validity of status.",
        "risk_level": "Financial",
        "weights": _make_weights({'accuracy': 0.3, 'validity': 0.3, 'timeliness': 0.15}),
        "critical_dimensions": ["accuracy", "validity"],
        "risk_threshold": 90,
        "required_signals": ["has_amount"] # Must have money
    },
    "Executive / Leadership": {
        "description": "High level overview, balanced concern for overall trust.",
        "risk_level": "Strategic",
        "weights": _make_weights({}),
        "critical_dimensions": [], 
        "risk_threshold": 60,
        "required_signals": []
    }
}

def get_role_profile(role_name: str) -> Dict[str, Any]:
    """
    Returns a predefined role profile.
    """
    role_key = next((k for k in PROFILES if k.lower() == role_name.lower()), "Executive / Leadership")
    profile = PROFILES[role_key].copy() # Copy to avoid mutating global state if we add keys later
    profile['role_name'] = role_key
    return profile

def get_all_role_names() -> List[str]:
    """Returns a list of all available role names."""
    return list(PROFILES.keys())

def is_role_applicable(role_profile: Dict[str, Any], metadata_signals: Dict[str, bool]) -> bool:
    """Checks if the dataset contains the necessary signals for the role."""
    required = role_profile.get('required_signals', [])
    for signal in required:
        if not metadata_signals.get(signal, False):
            return False
    return True

def calculate_role_score(base_dqs: float, dimension_scores: Dict[str, float], 
                         role_profile: Dict[str, Any], metadata: Any = None, alpha: float = 0.6) -> Tuple[Optional[float], bool]:
    """
    Calculates the Role-Specific Utility Score (RUS) and checks for critical risks.
    Handles Applicability Check.
    
    Returns:
        Tuple[Optional[float], bool]: (rus_score, risk_detected_or_not_applicable)
        - If not applicable: (None, False)
        - If applicable: (float_score, bool_risk_detected)
    """
    # 1. Applicability Check
    if metadata and hasattr(metadata, 'signals'):
        if not is_role_applicable(role_profile, metadata.signals):
            return None, False

    # 2. Alpha Enforcement
    if alpha < 0.6:
        alpha = 0.6
        
    weights = role_profile['weights']
    
    # 3. Calculate Role Component
    role_component = 0.0
    for dim, score in dimension_scores.items():
        weight = weights.get(dim, 0.0)
        role_component += weight * score
        
    rus_score = (alpha * base_dqs) + ((1 - alpha) * role_component)
    
    # 4. Check Critical Risks
    check_dims = role_profile.get('critical_dimensions', [])
    threshold = role_profile.get('risk_threshold', 75)
    
    risk_detected = False
    for dim in check_dims:
        if dimension_scores.get(dim, 0) < threshold:
            risk_detected = True
            break
            
    return round(rus_score, 2), risk_detected

def explain_role_impact(role_profile: Dict[str, Any], dimension_scores: Dict[str, float], metadata: Any = None) -> str:
    """
    Generates a conditional explanation.
    Handles Role Applicability.
    """
    role_name = role_profile['role_name']
    
    # Applicability Check
    if metadata and hasattr(metadata, 'signals'):
        if not is_role_applicable(role_profile, metadata.signals):
            required = role_profile.get('required_signals', [])
            return (f"⚠️ **Role Not Applicable**\n\n"
                    f"This dataset lacks the semantic signals required for a **{role_name}** analysis.\n"
                    f"Missing critical signals: `{'`, `'.join(required)}`\n"
                    f"Please switch to a role that matches the dataset content (e.g., Data Engineer).")

    check_dims = role_profile.get('critical_dimensions', [])
    threshold = role_profile.get('risk_threshold', 75)
    
    explanation_parts = [f"**Perspective: {role_name}**"]
    explanation_parts.append(f"{role_profile['description']}")
    explanation_parts.append("")
    
    # Identify failures
    failures = []
    for dim in check_dims:
        score = dimension_scores.get(dim, 0)
        if score < threshold:
            failures.append((dim, score))
            
    if not failures and check_dims:
        explanation_parts.append(f"✅ **No critical risks detected.**")
        explanation_parts.append(f"All critical dimensions ({', '.join(check_dims)}) are above the risk threshold of {threshold}.")
        explanation_parts.append("The dataset is suitable for this specific role/use-case.")
    elif not check_dims:
        if dimension_scores.get('accuracy', 100) < 60:
             explanation_parts.append("⚠️ General Notice: Data Accuracy is significantly low.")
        else:
             explanation_parts.append("ℹ️ Balanced Overview: Base DQS reflects the general state.")
    else:
        explanation_parts.append(f"⚠️ **Critical Data Quality Risks Detected:**")
        explanation_parts.append(f"The following dimensions fell below the {role_name} risk threshold ({threshold}):")
        
        for dim, score in failures:
            explanation_parts.append(f"- **{dim.title()}**: {score:.1f} (Threshold: {threshold})")
            
        explanation_parts.append("\n**Impact:**")
        explanation_parts.append(f"These deficiencies directly impact {role_profile['risk_level']} objectives. Proceed with caution.")
        
    return "\n".join(explanation_parts)
