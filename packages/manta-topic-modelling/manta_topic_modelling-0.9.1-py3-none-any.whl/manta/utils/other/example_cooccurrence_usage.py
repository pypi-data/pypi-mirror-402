#!/usr/bin/env python3
"""
Example usage of the word co-occurrence analyzer.

This script demonstrates how to use the memory-efficient word co-occurrence
analyzer with different types of input data.
"""

import pandas as pd
from manta.utils.analysis.word_cooccurrence_analyzer import analyze_word_cooccurrence


def example_with_csv():
    """Example using CSV file input."""
    print("=== Example 1: CSV File Input ===")
    
    # Analyze co-occurrence from a CSV file
    results = analyze_word_cooccurrence(
        input_data="veri_setleri/complaints.csv",  # Path to your CSV file
        text_column="complaint_text",  # Column containing text data
        window_size=5,
        min_count=3,
        max_vocab_size=5000,
        output_dir="./local/Output",
        table_name="complaints_cooccurrence",
        language="turkish",
        create_heatmap=True,
        heatmap_size=15,
        top_n=100
    )
    
    print(f"Found {len(results['pairs'])} co-occurring word pairs")
    print("\nTop 5 co-occurring pairs:")
    for i, pair in enumerate(results['pairs'][:5]):
        print(f"{i+1}. {pair['word_1']} - {pair['word_2']}: {pair['score']:.2f}")


def example_with_text_list():
    """Example using list of texts."""
    print("\n=== Example 2: Text List Input ===")
    
    # Sample Turkish texts
    sample_texts = [
        "Bu uygulama çok güzel ve kullanışlı bir program",
        "Telefon uygulaması çok yavaş çalışıyor",
        "Güzel bir deneyim yaşadım bu programda",
        "Uygulama sürekli donuyor ve çok yavaş",
        "Çok güzel bir telefon uygulaması",
        "Program çok kullanışlı ve hızlı çalışıyor"
    ]
    
    results = analyze_word_cooccurrence(
        input_data=sample_texts,
        window_size=3,
        min_count=2,
        output_dir="./local/Output",
        table_name="sample_texts_cooccurrence",
        language="turkish",
        create_heatmap=True,
        heatmap_size=10,
        top_n=20
    )
    
    print(f"Found {len(results['pairs'])} co-occurring word pairs")
    print("\nTop 3 co-occurring pairs:")
    for i, pair in enumerate(results['pairs'][:3]):
        print(f"{i+1}. {pair['word_1']} - {pair['word_2']}: {pair['score']:.2f}")


def example_with_dataframe():
    """Example using pandas DataFrame."""
    print("\n=== Example 3: DataFrame Input ===")
    
    # Create sample DataFrame
    data = {
        'text': [
            "Machine learning is a powerful tool for data analysis",
            "Deep learning models require large amounts of data",
            "Natural language processing uses machine learning techniques",
            "Data science combines statistics and machine learning",
            "Artificial intelligence includes machine learning and deep learning"
        ],
        'category': ['ML', 'DL', 'NLP', 'DS', 'AI']
    }
    
    df = pd.DataFrame(data)
    
    results = analyze_word_cooccurrence(
        input_data=df,
        text_column='text',
        window_size=4,
        min_count=1,
        output_dir="./local/Output",
        table_name="ml_texts_cooccurrence",
        language="english",
        create_heatmap=True,
        heatmap_size=8,
        top_n=15
    )
    
    print(f"Found {len(results['pairs'])} co-occurring word pairs")
    print("\nTop 3 co-occurring pairs:")
    for i, pair in enumerate(results['pairs'][:3]):
        print(f"{i+1}. {pair['word_1']} - {pair['word_2']}: {pair['score']:.2f}")


def example_memory_efficient():
    """Example with memory-efficient settings for large datasets."""
    print("\n=== Example 4: Memory-Efficient Settings ===")
    
    # For very large datasets, use these settings
    results = analyze_word_cooccurrence(
        input_data="veri_setleri/app_store.csv",  # Large CSV file
        text_column="review_text",
        window_size=3,  # Smaller window for efficiency
        min_count=10,   # Higher threshold to reduce vocabulary
        max_vocab_size=1000,  # Limit vocabulary size
        output_dir="./local/Output",
        table_name="large_dataset_cooccurrence",
        language="turkish",
        create_heatmap=True,
        heatmap_size=12,
        top_n=50,
        batch_size=500  # Process in smaller batches
    )
    
    print(f"Vocabulary size: {results['vocabulary_size']}")
    print(f"Total co-occurrences: {results['total_cooccurrences']}")
    print(f"Found {len(results['pairs'])} top co-occurring pairs")


if __name__ == "__main__":
    print("Word Co-occurrence Analysis Examples")
    print("=" * 40)
    
    # Run examples
    try:
        example_with_text_list()
    except Exception as e:
        print(f"Error in text list example: {e}")
    
    try:
        example_with_dataframe()
    except Exception as e:
        print(f"Error in DataFrame example: {e}")
    
    try:
        example_with_csv()
    except Exception as e:
        print(f"Error in CSV example: {e}")
    
    try:
        example_memory_efficient()
    except Exception as e:
        print(f"Error in memory-efficient example: {e}")
    
    print("\n" + "=" * 40)
    print("Examples completed!")
    print("Check the './local/Output' directory for results and visualizations.")