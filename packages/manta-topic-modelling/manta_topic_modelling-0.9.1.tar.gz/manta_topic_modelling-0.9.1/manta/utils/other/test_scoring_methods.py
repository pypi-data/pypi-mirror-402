#!/usr/bin/env python3
"""
Test script to verify the alternative scoring methods for NMTF document scoring.
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manta._functions.common_language.topic_analyzer import _apply_alternative_scoring

def test_scoring_methods():
    """Test all scoring methods with sample data."""
    
    # Create sample topic document vector with small NMTF-style values
    topic_doc_vector = np.array([0.001, 0.0005, 0.002, 0.0015, 0.0008, 0.0001, 0.003, 0.0012])
    doc_ids = np.array([0, 1, 2, 3, 4, 5, 6, 7])  # All documents
    
    print("Original scores:", topic_doc_vector)
    print("=" * 60)
    
    methods = ["percentile", "zscore", "minmax", "exponential", "raw"]
    
    for method in methods:
        print(f"\n{method.upper()} METHOD:")
        print("-" * 30)
        
        try:
            transformed_scores = _apply_alternative_scoring(topic_doc_vector, doc_ids, method)
            
            for doc_id in doc_ids:
                original = topic_doc_vector[doc_id]
                transformed = transformed_scores[doc_id]
                print(f"Doc {doc_id}: {original:.6f} -> {transformed:.6f}")
                
        except Exception as e:
            print(f"Error with {method}: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")

if __name__ == "__main__":
    test_scoring_methods()