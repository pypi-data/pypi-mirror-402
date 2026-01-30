"""Utility functions for TPDF"""

import json


def load_tpdf(filename):
    """
    Load TPDF from file
    
    Args:
        filename: Path to .tpdf file
    
    Returns:
        dict: TPDF data
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_tpdf(data):
    """
    Validate TPDF structure
    
    Args:
        data: TPDF data dict
    
    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    
    # Check version
    if 'version' not in data:
        errors.append("Missing 'version' field")
    
    # Check format
    if 'pages' in data:
        # Multi-page format
        if not isinstance(data['pages'], list):
            errors.append("'pages' must be a list")
        for i, page in enumerate(data.get('pages', [])):
            if 'elements' not in page:
                errors.append(f"Page {i} missing 'elements' field")
    elif 'page' in data:
        # Single page format
        if 'elements' not in data:
            errors.append("Missing 'elements' field")
    else:
        errors.append("Must have either 'page' or 'pages' field")
    
    return (len(errors) == 0, errors)
