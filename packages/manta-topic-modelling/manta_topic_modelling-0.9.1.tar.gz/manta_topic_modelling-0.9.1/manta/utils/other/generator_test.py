import pandas as pd
import numpy as np
import psutil
import os
import time
import gc
from memory_profiler import memory_usage
import matplotlib.pyplot as plt
from datetime import datetime


# Mock implementations for testing (replace with actual imports)
class MockEmojiMap:
    def process_text(self, text):
        return text


# Simplified versions of the functions for testing
def process_text_simple(text, emoji_map=None):
    """Simplified version for testing - just does basic transformations"""
    result = text.lower()
    result = ' '.join(result.split())  # Remove extra spaces
    result = result.replace('xxx', '')  # Simple replacement
    return result


def process_texts_generator(texts, emoji_map=None):
    """Generator version"""
    for text in texts:
        yield process_text_simple(text, emoji_map)


def metin_temizle_turkish_old(df, desired_column, emoji_map=None):
    """Old version - creates new list"""
    metin = [process_text_simple(i, emoji_map) for i in df[desired_column].values]
    return metin


def metin_temizle_turkish_new(df, desired_column, emoji_map=None, inplace=False):
    """New version with generator"""
    if inplace:
        for i, processed in enumerate(process_texts_generator(df[desired_column].values, emoji_map)):
            df.at[i, desired_column] = processed
        return None
    else:
        return list(process_texts_generator(df[desired_column].values, emoji_map))


# Memory monitoring utilities
def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def monitor_memory_during_execution(func, *args, **kwargs):
    """Monitor memory usage during functi
    on execution"""
    gc.collect()
    initial_memory = get_memory_usage()

    # Record memory usage over time
    memory_points = []

    def wrapper():
        result = func(*args, **kwargs)
        return result

    # Use memory_profiler to track memory usage
    mem_usage = memory_usage(wrapper, interval=0.1, timeout=None)

    final_memory = get_memory_usage()
    peak_memory = max(mem_usage) if mem_usage else final_memory

    return {
        'initial': initial_memory,
        'final': final_memory,
        'peak': peak_memory,
        'increase': final_memory - initial_memory,
        'peak_increase': peak_memory - initial_memory,
        'memory_timeline': mem_usage
    }


def create_test_dataframe(n_rows=10000, text_length=100):
    """Create a test DataFrame with random text data"""
    print(f"Creating test DataFrame with {n_rows:,} rows...")

    # Generate random text data
    texts = []
    for i in range(n_rows):
        # Create realistic text with varying lengths
        words = ['lorem', 'ipsum', 'dolor', 'sit', 'amet', 'xxx', 'consectetur',
                 'adipiscing', 'elit', 'sed', 'do', 'eiusmod', 'tempor']
        text = ' '.join(np.random.choice(words, size=text_length))
        texts.append(text)

    df = pd.DataFrame({'text': texts})
    return df


def run_memory_tests(sizes=[1000, 5000, 10000, 20000, 50000]):
    """Run memory efficiency tests with different dataset sizes"""
    results = {
        'old_method': [],
        'new_method_list': [],
        'new_method_inplace': []
    }

    print("=" * 70)
    print("MEMORY EFFICIENCY TEST - Turkish Text Preprocessor")
    print("=" * 70)

    for size in sizes:
        print(f"\nTesting with {size:,} rows...")
        print("-" * 50)

        # Test 1: Old method (list comprehension)
        df1 = create_test_dataframe(size, text_length=50)
        gc.collect()
        time.sleep(1)

        print("Testing OLD method (list comprehension)...")
        start_time = time.time()
        mem_stats_old = monitor_memory_during_execution(
            metin_temizle_turkish_old, df1, 'text'
        )
        old_time = time.time() - start_time

        results['old_method'].append({
            'size': size,
            'memory': mem_stats_old,
            'time': old_time
        })

        # Test 2: New method returning list
        df2 = create_test_dataframe(size, text_length=50)
        gc.collect()
        time.sleep(1)

        print("Testing NEW method (generator -> list)...")
        start_time = time.time()
        mem_stats_new_list = monitor_memory_during_execution(
            metin_temizle_turkish_new, df2, 'text', inplace=False
        )
        new_list_time = time.time() - start_time

        results['new_method_list'].append({
            'size': size,
            'memory': mem_stats_new_list,
            'time': new_list_time
        })

        # Test 3: New method in-place
        df3 = create_test_dataframe(size, text_length=50)
        gc.collect()
        time.sleep(1)

        print("Testing NEW method (in-place modification)...")
        start_time = time.time()
        mem_stats_new_inplace = monitor_memory_during_execution(
            metin_temizle_turkish_new, df3, 'text', inplace=True
        )
        inplace_time = time.time() - start_time

        results['new_method_inplace'].append({
            'size': size,
            'memory': mem_stats_new_inplace,
            'time': inplace_time
        })

        # Print results for this size
        print(f"\nResults for {size:,} rows:")
        print(
            f"Old method:           Peak memory increase: {mem_stats_old['peak_increase']:.2f} MB, Time: {old_time:.2f}s")
        print(
            f"New method (list):    Peak memory increase: {mem_stats_new_list['peak_increase']:.2f} MB, Time: {new_list_time:.2f}s")
        print(
            f"New method (inplace): Peak memory increase: {mem_stats_new_inplace['peak_increase']:.2f} MB, Time: {inplace_time:.2f}s")

        # Calculate savings
        savings_vs_old = (1 - mem_stats_new_inplace['peak_increase'] / mem_stats_old['peak_increase']) * 100
        print(f"\nMemory savings (in-place vs old): {savings_vs_old:.1f}%")

        # Clean up
        del df1, df2, df3
        gc.collect()

    return results


def plot_results(results):
    """Create visualization of memory usage comparison"""
    sizes = [r['size'] for r in results['old_method']]

    # Extract peak memory increases
    old_memory = [r['memory']['peak_increase'] for r in results['old_method']]
    new_list_memory = [r['memory']['peak_increase'] for r in results['new_method_list']]
    new_inplace_memory = [r['memory']['peak_increase'] for r in results['new_method_inplace']]

    # Extract times
    old_time = [r['time'] for r in results['old_method']]
    new_list_time = [r['time'] for r in results['new_method_list']]
    new_inplace_time = [r['time'] for r in results['new_method_inplace']]

    # Create plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Memory usage plot
    ax1.plot(sizes, old_memory, 'r-o', label='Old method (list)', linewidth=2, markersize=8)
    ax1.plot(sizes, new_list_memory, 'b-s', label='New method (generator->list)', linewidth=2, markersize=8)
    ax1.plot(sizes, new_inplace_memory, 'g-^', label='New method (in-place)', linewidth=2, markersize=8)
    ax1.set_xlabel('Dataset Size (number of texts)', fontsize=12)
    ax1.set_ylabel('Peak Memory Increase (MB)', fontsize=12)
    ax1.set_title('Memory Usage Comparison', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')

    # Time comparison plot
    ax2.plot(sizes, old_time, 'r-o', label='Old method (list)', linewidth=2, markersize=8)
    ax2.plot(sizes, new_list_time, 'b-s', label='New method (generator->list)', linewidth=2, markersize=8)
    ax2.plot(sizes, new_inplace_time, 'g-^', label='New method (in-place)', linewidth=2, markersize=8)
    ax2.set_xlabel('Dataset Size (number of texts)', fontsize=12)
    ax2.set_ylabel('Execution Time (seconds)', fontsize=12)
    ax2.set_title('Execution Time Comparison', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')

    plt.tight_layout()

    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'memory_efficiency_test_{timestamp}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved as: {filename}")

    #plt.show()


def generate_summary_report(results):
    """Generate a summary report of the test results"""
    print("\n" + "=" * 70)
    print("SUMMARY REPORT")
    print("=" * 70)

    # Calculate average memory savings
    savings = []
    for i in range(len(results['old_method'])):
        old_mem = results['old_method'][i]['memory']['peak_increase']
        inplace_mem = results['new_method_inplace'][i]['memory']['peak_increase']
        saving = (1 - inplace_mem / old_mem) * 100
        savings.append(saving)

    avg_saving = np.mean(savings)

    print(f"\nAverage memory savings (in-place vs old method): {avg_saving:.1f}%")

    # Find the dataset size where memory difference is most significant
    max_diff_idx = np.argmax([results['old_method'][i]['memory']['peak_increase'] -
                              results['new_method_inplace'][i]['memory']['peak_increase']
                              for i in range(len(results['old_method']))])

    max_diff_size = results['old_method'][max_diff_idx]['size']
    max_diff_mb = (results['old_method'][max_diff_idx]['memory']['peak_increase'] -
                   results['new_method_inplace'][max_diff_idx]['memory']['peak_increase'])

    print(f"Maximum memory difference: {max_diff_mb:.2f} MB at {max_diff_size:,} texts")

    # Performance comparison
    print("\nPerformance Impact:")
    for i, size in enumerate([r['size'] for r in results['old_method']]):
        old_time = results['old_method'][i]['time']
        inplace_time = results['new_method_inplace'][i]['time']
        time_diff = ((inplace_time - old_time) / old_time) * 100
        print(f"  {size:,} texts: {time_diff:+.1f}% time difference")


# Main execution
if __name__ == "__main__":
    print("Starting memory efficiency tests...")
    print("Note: This test requires 'memory_profiler' package")
    print("Install with: pip install memory-profiler psutil matplotlib")

    # Run tests with different sizes
    # Adjust these sizes based on your available memory
    test_sizes = [1000, 5000, 10000, 25000, 50000]

    try:
        results = run_memory_tests(test_sizes)
        plot_results(results)
        generate_summary_report(results)
    except MemoryError:
        print("\nMemoryError: Reduce test sizes for your system")
    except Exception as e:
        print(f"\nError during testing: {e}")
        print("Make sure you have installed required packages:")
        print("pip install memory-profiler psutil matplotlib pandas numpy")