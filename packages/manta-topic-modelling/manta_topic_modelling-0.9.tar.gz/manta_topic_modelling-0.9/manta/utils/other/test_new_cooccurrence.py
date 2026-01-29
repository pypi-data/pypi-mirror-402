#!/usr/bin/env python3
"""
Test script to verify the new co-occurrence analyzer integration with manta_entry.py
"""

import pandas as pd
from manta._functions.common_language.emoji_processor import EmojiMap
from manta.manta_entry import run_manta_process


def test_new_cooccurrence():
    """Test the new sliding window co-occurrence analyzer."""
    
    # Create a small test dataset
    test_data = {
        'REVIEW': [
            'Bu uygulama çok güzel ve kullanışlı bir program',
            'Telefon uygulaması çok yavaş çalışıyor',
            'Güzel bir deneyim yaşadım bu programda',
            'Uygulama sürekli donuyor ve çok yavaş',
            'Çok güzel bir telefon uygulaması',
            'Program çok kullanışlı ve hızlı çalışıyor',
            'Bu telefon uygulaması çok güzel',
            'Uygulama çok yavaş ve kullanışsız',
            'Güzel program ama yavaş çalışıyor',
            'Çok kullanışlı ve hızlı bir uygulama'
        ]
    }
    
    # Save test data to CSV
    df = pd.DataFrame(test_data)
    test_filepath = 'test_cooccurrence_data.csv'
    df.to_csv(test_filepath, index=False, sep='|')
    
    # Configuration for testing
    table_name = "test_cooccurrence_sliding_window"
    desired_columns = "REVIEW"
    
    emj_map = EmojiMap()
    options = {
        "LEMMATIZE": True,
        "N_TOPICS": 10,
        "DESIRED_TOPIC_COUNT": 3,
        "tokenizer_type": "bpe",
        "tokenizer": None,
        "nmf_type": "nmf",
        "LANGUAGE": "TR",
        "separator": "|",
        "gen_cloud": True,
        "save_excel": True,
        "word_pairs_out": True,
        "gen_topic_distribution": True,
        "filter_app": False,
        "filter_app_name": "",
        "emoji_map": emj_map,
        
        # New co-occurrence analysis options
        "cooccurrence_method": "sliding_window",  # Use new method
        "cooccurrence_window_size": 3,           # Small window for test
        "cooccurrence_min_count": 1,             # Low threshold for test
        "cooccurrence_max_vocab": 50,            # Small vocab for test
        "cooccurrence_heatmap_size": 10,         # Small heatmap for test
        "cooccurrence_top_n": 20,                # Top 20 pairs
        "cooccurrence_batch_size": 5,            # Small batch size
    }
    
    print("Testing new sliding window co-occurrence analyzer...")
    print("=" * 50)
    
    # Run the analysis
    result = run_manta_process(test_filepath, table_name, desired_columns, options)
    
    if result["state"] == "SUCCESS":
        print("✅ SUCCESS: New co-occurrence analyzer integrated successfully!")
        print(f"Data processed: {result['data_name']}")
        print("Check the TopicAnalysis/Output directory for co-occurrence results")
    else:
        print("❌ FAILURE:", result["message"])
        
    # Test with old method for comparison
    print("\n" + "=" * 50)
    print("Testing original NMF-based co-occurrence for comparison...")
    
    options["cooccurrence_method"] = "nmf"  # Switch to old method
    table_name_old = "test_cooccurrence_nmf"
    
    result_old = run_manta_process(test_filepath, table_name_old, desired_columns, options)
    
    if result_old["state"] == "SUCCESS":
        print("✅ SUCCESS: Original co-occurrence method still works!")
        print(f"Data processed: {result_old['data_name']}")
    else:
        print("❌ FAILURE:", result_old["message"])
        
    # Clean up test file
    import os
    if os.path.exists(test_filepath):
        os.remove(test_filepath)
        print(f"\nCleaned up test file: {test_filepath}")


if __name__ == "__main__":
    test_new_cooccurrence()