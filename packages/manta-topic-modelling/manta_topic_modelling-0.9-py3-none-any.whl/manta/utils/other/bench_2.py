import pandas as pd
import numpy as np
import psutil
import os
import time
import gc
from memory_profiler import memory_usage
import matplotlib.pyplot as plt
from datetime import datetime
import unicodedata
import re


# Simplified mock implementations for testing
def remove_space_between_terms(text, pattern, term, position):
    """Mock implementation"""
    return text


class TurkishStr(str):
    lang = 'tr'
    _case_lookup_upper = {'İ': 'i', 'Ğ': 'ğ', 'Ş': 'ş', 'Ü': 'ü', 'Ö': 'ö', 'Ç': 'ç'}
    _case_lookup_lower = {v: k for (k, v) in _case_lookup_upper.items()}

    def lower(self):
        chars = [self._case_lookup_upper.get(c, c) for c in self]
        result = ''.join(chars).lower()
        return TurkishStr(result)


# Turkish stopwords for testing
TURKISH_STOPWORDS = ['ve', 'ile', 'bu', 'da', 'de', 'bir', 'için', 'çok', 'daha', 'var', 'ama', 'ne', 'ben', 'ki']


# Simplified process_text for testing
def process_text(text: str, emoji_map=None) -> str:
    """Simplified version of process_text for testing"""
    metin = str(text)
    secilen_kategoriler = ['Ll', "Nd"]
    metin = TurkishStr(metin).lower()

    # Unicode category filtering
    kategoriler = [unicodedata.category(karakter) for karakter in metin]
    yeni_metin = "".join([metin[j] if kategoriler[j] in secilen_kategoriler
                          else ' ' for j in range(len(metin))])

    # Clean up
    metin = re.sub(' +', ' ', yeni_metin)
    metin = re.sub(r'\b[xX]{2,}\b', '', metin)
    metin = re.sub(r'(.)\1{2,}', r'\1', metin)

    # Remove stopwords
    metin = [i for i in metin.split() if i not in TURKISH_STOPWORDS]
    metin = ' '.join(metin)

    return metin


# OLD METHOD - Creates a new list
def metin_temizle_turkish_old(df: pd.DataFrame, desired_column: str, emoji_map=None) -> list:
    """Old method - creates a new list"""
    metin = [process_text(i, emoji_map) for i in df[desired_column].values]
    return metin


# NEW METHOD - Updates in place
def metin_temizle_turkish_new(df: pd.DataFrame, desired_column: str, emoji_map=None) -> pd.DataFrame:
    """New method - updates DataFrame in place"""
    for i, text in enumerate(df[desired_column].values):
        processed = process_text(text, emoji_map)
        df.at[i, desired_column] = processed
    return df


# Memory monitoring utilities
def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def create_test_dataframe(n_rows=10000, avg_text_length=100):
    """Create a realistic test DataFrame with Turkish text"""
    print(f"Creating test DataFrame with {n_rows:,} rows...")

    # Turkish words for generating realistic text
    turkish_words = [
        'merhaba', 'dünya', 'İstanbul', 'Türkiye', 'güzel', 'büyük', 'küçük',
        'Şehir', 'deniz', 'gökyüzü', 'yıldız', 'güneş', 'kitap', 'okul',
        'öğrenci', 'öğretmen', 'xxxxx', 'Çalışmak', 'yazmak', 'okumak',
        'gitmek', 'gelmek', 'görmek', 'bilmek', 'istemek', 'yapmak',
        've', 'ile', 'ama', 'çünkü', 'için', 'gibi', 'kadar', 'sonra',
        '123', '456', 'gb', 'tl', 'saniye', 'sn'
    ]

    texts = []
    for i in range(n_rows):
        # Generate text with varying length
        text_length = np.random.randint(avg_text_length // 2, avg_text_length * 2)
        words = np.random.choice(turkish_words, size=text_length // 5)  # Approximate words
        text = ' '.join(words)

        # Add some repeated characters
        if np.random.random() > 0.8:
            text += ' aaaaaaa'

        texts.append(text)

    df = pd.DataFrame({'text': texts})
    return df


def measure_method_memory(method_name, method_func, df, column_name):
    """Measure memory usage for a specific method"""
    gc.collect()
    time.sleep(0.5)

    # Create a copy of DataFrame for fair comparison
    df_copy = df.copy()

    # Wrapper function for memory_usage
    def wrapper():
        return method_func(df_copy, column_name)

    # Measure memory usage of the function execution
    start_time = time.time()
    mem_usage = memory_usage(wrapper, interval=0.1, timeout=None)
    end_time = time.time()

    # Calculate function memory usage
    if mem_usage:
        baseline_memory = mem_usage[0]  # Memory before function starts
        max_memory = max(mem_usage)  # Maximum memory during execution
        final_memory = mem_usage[-1]  # Memory after function completes
        function_memory_usage = max_memory - baseline_memory  # Memory used by function
    else:
        function_memory_usage = 0
        baseline_memory = 0
        max_memory = 0
        final_memory = 0

    return {
        'method': method_name,
        'baseline_memory': baseline_memory,
        'max_memory': max_memory,
        'final_memory': final_memory,
        'function_memory_usage': function_memory_usage,
        'execution_time': end_time - start_time,
        'memory_timeline': mem_usage
    }


def run_comparison_test(test_sizes=[1000, 5000, 10000, 20000]):
    """Run the comparison test between old and new methods"""
    results = []

    print("=" * 70)
    print("MEMORY EFFICIENCY COMPARISON TEST")
    print("Old Method (List) vs New Method (In-Place)")
    print("=" * 70)

    for size in test_sizes:
        print(f"\n{'=' * 50}")
        print(f"Testing with {size:,} texts")
        print(f"{'=' * 50}")

        # Create test data
        df = create_test_dataframe(size, avg_text_length=50)

        # Test OLD method
        print("\nTesting OLD method (creates new list)...")
        old_result = measure_method_memory('Old Method', metin_temizle_turkish_old, df, 'text')

        # Test NEW method
        print("Testing NEW method (in-place update)...")
        new_result = measure_method_memory('New Method', metin_temizle_turkish_new, df, 'text')

        # Calculate savings
        memory_savings = (1 - new_result['function_memory_usage'] / old_result['function_memory_usage']) * 100
        time_difference = ((new_result['execution_time'] - old_result['execution_time']) /
                           old_result['execution_time']) * 100

        # Store results
        result = {
            'size': size,
            'old': old_result,
            'new': new_result,
            'memory_savings': memory_savings,
            'time_difference': time_difference
        }
        results.append(result)

        # Print summary
        print(f"\nResults for {size:,} texts:")
        print(f"{'Method':<15} {'Function Memory Usage':<25} {'Execution Time':<20}")
        print("-" * 60)
        print(
            f"{'Old Method':<15} {old_result['function_memory_usage']:<25.2f} MB {old_result['execution_time']:<20.2f}s")
        print(
            f"{'New Method':<15} {new_result['function_memory_usage']:<25.2f} MB {new_result['execution_time']:<20.2f}s")
        print(f"\nMemory Savings: {memory_savings:.1f}%")
        print(f"Time Difference: {time_difference:+.1f}%")

        # Clean up
        del df
        gc.collect()
        time.sleep(1)

    return results


def plot_comparison_results(results):
    """Create visualization comparing the two methods"""
    sizes = [r['size'] for r in results]
    old_memory = [r['old']['function_memory_usage'] for r in results]
    new_memory = [r['new']['function_memory_usage'] for r in results]
    old_time = [r['old']['execution_time'] for r in results]
    new_time = [r['new']['execution_time'] for r in results]
    memory_savings = [r['memory_savings'] for r in results]

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Memory Usage Comparison
    ax1.plot(sizes, old_memory, 'r-o', label='Old Method (List)', linewidth=2, markersize=8)
    ax1.plot(sizes, new_memory, 'g-o', label='New Method (In-Place)', linewidth=2, markersize=8)
    ax1.set_xlabel('Number of Texts', fontsize=12)
    ax1.set_ylabel('Function Memory Usage (MB)', fontsize=12)
    ax1.set_title('Function Memory Usage Comparison', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Execution Time Comparison
    ax2.plot(sizes, old_time, 'r-s', label='Old Method (List)', linewidth=2, markersize=8)
    ax2.plot(sizes, new_time, 'g-s', label='New Method (In-Place)', linewidth=2, markersize=8)
    ax2.set_xlabel('Number of Texts', fontsize=12)
    ax2.set_ylabel('Execution Time (seconds)', fontsize=12)
    ax2.set_title('Execution Time Comparison', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Memory Savings Percentage
    ax3.bar(range(len(sizes)), memory_savings, color='green', alpha=0.7)
    ax3.set_xlabel('Dataset Size', fontsize=12)
    ax3.set_ylabel('Memory Savings (%)', fontsize=12)
    ax3.set_title('Memory Savings with New Method', fontsize=14, fontweight='bold')
    ax3.set_xticks(range(len(sizes)))
    ax3.set_xticklabels([f'{s:,}' for s in sizes])
    ax3.grid(True, alpha=0.3, axis='y')

    # Add percentage labels on bars
    for i, v in enumerate(memory_savings):
        ax3.text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom')

    # 4. Memory Difference (Absolute)
    memory_diff = [old - new for old, new in zip(old_memory, new_memory)]
    ax4.bar(range(len(sizes)), memory_diff, color='blue', alpha=0.7)
    ax4.set_xlabel('Dataset Size', fontsize=12)
    ax4.set_ylabel('Memory Saved (MB)', fontsize=12)
    ax4.set_title('Absolute Memory Saved', fontsize=14, fontweight='bold')
    ax4.set_xticks(range(len(sizes)))
    ax4.set_xticklabels([f'{s:,}' for s in sizes])
    ax4.grid(True, alpha=0.3, axis='y')

    # Add MB labels on bars
    for i, v in enumerate(memory_diff):
        ax4.text(i, v + 0.5, f'{v:.1f} MB', ha='center', va='bottom')

    plt.tight_layout()

    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'turkish_preprocessor_comparison_{timestamp}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved as: {filename}")

    #plt.show()


def generate_report(results):
    """Generate a detailed report of the comparison"""
    print("\n" + "=" * 70)
    print("DETAILED COMPARISON REPORT")
    print("=" * 70)

    # Average metrics
    avg_memory_savings = np.mean([r['memory_savings'] for r in results])
    avg_time_diff = np.mean([r['time_difference'] for r in results])

    print(f"\nAverage Memory Savings: {avg_memory_savings:.1f}%")
    print(f"Average Time Difference: {avg_time_diff:+.1f}%")

    print("\nDetailed Results by Dataset Size:")
    print("-" * 70)
    print(f"{'Size':<10} {'Memory Saved':<15} {'Savings %':<12} {'Time Diff':<15}")
    print("-" * 70)

    for r in results:
        memory_saved = r['old']['function_memory_usage'] - r['new']['function_memory_usage']
        print(f"{r['size']:<10,} {memory_saved:<15.2f} MB {r['memory_savings']:<12.1f}% {r['time_difference']:+15.1f}%")

    print("\nConclusion:")
    print(f"The new in-place method saves an average of {avg_memory_savings:.1f}% memory")
    print(f"with a {abs(avg_time_diff):.1f}% {'increase' if avg_time_diff > 0 else 'decrease'} in execution time.")


# Main execution
if __name__ == "__main__":
    print("Turkish Preprocessor Memory Comparison Test")
    print("Old Method (List) vs New Method (In-Place Update)")
    print("\nNote: Requires 'memory_profiler' and 'psutil' packages")
    print("Install with: pip install memory-profiler psutil matplotlib pandas numpy")

    # Run tests
    test_sizes = [1000, 5000, 10000, 25000]

    try:
        results = run_comparison_test(test_sizes)
        plot_comparison_results(results)
        generate_report(results)
    except Exception as e:
        print(f"\nError during testing: {e}")
        print("Make sure all required packages are installed.")