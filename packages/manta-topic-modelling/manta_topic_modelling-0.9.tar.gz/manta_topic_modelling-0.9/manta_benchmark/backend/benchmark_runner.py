"""Benchmark runner service for executing MANTA analysis with metrics collection."""

import json
import os
import platform
import re
import subprocess
import tempfile
import threading
import time
import statistics
import math
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Tuple

from sqlalchemy.orm import Session

from . import models


class OutputBuffer:
    """Thread-safe circular buffer for capturing subprocess output in real-time."""

    def __init__(self, maxlen: int = 10000):
        self._buffer: deque = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._line_count = 0

    def append(self, line: str):
        """Append a line to the buffer (thread-safe)."""
        with self._lock:
            self._buffer.append(line)
            self._line_count += 1

    def get_lines(self, offset: int = 0) -> Tuple[List[str], int]:
        """Get lines from offset. Returns (lines, total_count).

        Args:
            offset: Number of lines to skip from the beginning

        Returns:
            Tuple of (list of lines after offset, total line count)
        """
        with self._lock:
            lines = list(self._buffer)
            total = self._line_count
        # Return lines after offset
        if offset < len(lines):
            return lines[offset:], total
        return [], total

    def get_all(self) -> str:
        """Get all buffered output as a single string."""
        with self._lock:
            return '\n'.join(self._buffer)


def create_worker_script(
    filepath: str,
    column: str,
    separator: str,
    language: str,
    topic_count: int,
    nmf_method: str,
    tokenizer_type: str,
    lemmatize: bool,
    words_per_topic: int,
    n_grams_to_discover: Optional[int],
    output_dir: str,
    use_cache: bool = True
) -> str:
    """Create a worker script that runs a single MANTA analysis.

    Args:
        use_cache: Whether to use cached data. First run should be False to build cache.

    Returns the path to the temporary script file.
    """
    n_grams_param = str(n_grams_to_discover) if n_grams_to_discover else "None"

    script_content = f'''
import manta
import resource
import platform
import json
import sys
import gc
import os

def run_analysis():
    # Clean up memory before measurement
    gc.collect()

    # Run the analysis
    result = manta.run_topic_analysis(
        filepath="{filepath}",
        column="{column}",
        separator="{separator}",
        language="{language}",
        topic_count={topic_count},
        nmf_method="{nmf_method}",
        tokenizer_type="{tokenizer_type}",
        lemmatize={lemmatize},
        words_per_topic={words_per_topic},
        n_grams_to_discover={n_grams_param},
        generate_wordclouds=True,
        export_excel=False,
        topic_distribution=False,
        word_pairs_out=False,
        save_to_db=False,
        emoji_map=False,
        output_dir="{output_dir}",
        use_cache={use_cache},
    )

    # Get peak memory usage throughout process lifetime
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    # Convert from system units to MB
    if platform.system() == "Darwin":  # macOS
        peak_mb = peak_rss / 1024 / 1024
    else:  # Linux
        peak_mb = peak_rss / 1024

    return {{
        "peak_memory_mb": peak_mb,
        "state": result.get("state", "UNKNOWN"),
    }}

if __name__ == "__main__":
    try:
        metrics = run_analysis()
        print("BENCHMARK_RESULT:" + json.dumps(metrics))
    except Exception as e:
        import traceback
        print("BENCHMARK_ERROR:" + json.dumps({{"error": str(e), "traceback": traceback.format_exc()}}))
        sys.exit(1)
'''

    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        return f.name


def parse_coherence_from_output(stdout: str) -> Optional[float]:
    """Parse coherence score from MANTA stdout output."""
    # Look for "Gensim c_v Average: X.XXXX" pattern
    match = re.search(r'Gensim c_v Average:\s*([\d.]+)', stdout)
    if match:
        return float(match.group(1))
    return None


def parse_benchmark_result(stdout: str) -> Dict[str, Any]:
    """Parse the benchmark result JSON from stdout."""
    for line in stdout.strip().split('\n'):
        if line.startswith('BENCHMARK_RESULT:'):
            json_str = line[len('BENCHMARK_RESULT:'):]
            return json.loads(json_str)
    return {}


def parse_benchmark_error(stdout: str) -> Optional[Dict[str, Any]]:
    """Parse the benchmark error JSON from stdout."""
    for line in stdout.strip().split('\n'):
        if line.startswith('BENCHMARK_ERROR:'):
            json_str = line[len('BENCHMARK_ERROR:'):]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                return {'error': json_str}
    return None


def run_single_benchmark(
    config: models.BenchmarkConfig,
    dataset: models.Dataset,
    output_base_dir: str,
    output_buffer: Optional[OutputBuffer] = None,
    config_id: Optional[int] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Run a single benchmark iteration with optional real-time output capture.

    Args:
        config: Benchmark configuration
        dataset: Dataset to analyze
        output_base_dir: Directory for output files
        output_buffer: Optional buffer for real-time output streaming
        config_id: Optional config ID for tracking process (enables termination)
        use_cache: Whether to use cached data (False for first run, True for subsequent)

    Returns:
        Metrics dict with execution_time, peak_memory_mb, coherence_cv, state.
    """
    # Create worker script
    worker_script = create_worker_script(
        filepath=dataset.filepath,
        column=dataset.text_column,
        separator=dataset.separator,
        language=config.language,
        topic_count=config.topic_count,
        nmf_method=config.nmf_method,
        tokenizer_type=config.tokenizer_type,
        lemmatize=config.lemmatize,
        words_per_topic=config.words_per_topic,
        n_grams_to_discover=config.n_grams_to_discover,
        output_dir=output_base_dir,
        use_cache=use_cache
    )

    try:
        start_time = time.time()
        stdout_lines = []

        # Use Popen for real-time output capture
        process = subprocess.Popen(
            ['python', '-u', worker_script],  # -u for unbuffered output
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
            cwd=os.getcwd()
        )

        # Track the process for potential termination
        if config_id:
            set_current_process(config_id, process)

        # Read output line by line in real-time
        try:
            for line in iter(process.stdout.readline, ''):
                # Check if stop was requested
                if config_id and is_benchmark_stopped(config_id):
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    return {
                        'execution_time': time.time() - start_time,
                        'peak_memory_mb': None,
                        'coherence_cv': None,
                        'state': 'STOPPED',
                        'error': 'Benchmark stopped by user'
                    }

                line = line.rstrip('\n')
                stdout_lines.append(line)
                if output_buffer:
                    output_buffer.append(line)

            process.wait(timeout=3600)  # 1 hour timeout
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return {
                'execution_time': 3600,
                'peak_memory_mb': None,
                'coherence_cv': None,
                'state': 'TIMEOUT',
                'error': 'Benchmark timed out after 1 hour'
            }

        execution_time = time.time() - start_time
        stdout = '\n'.join(stdout_lines)

        # Check for explicit error output from worker script
        error_info = parse_benchmark_error(stdout)
        if error_info:
            error_msg = error_info.get('error', 'Unknown error')
            traceback_str = error_info.get('traceback', '')
            full_error = f"{error_msg}\n{traceback_str}" if traceback_str else error_msg
            return {
                'execution_time': execution_time,
                'peak_memory_mb': None,
                'coherence_cv': None,
                'state': 'FAILED',
                'error': full_error
            }

        if process.returncode != 0:
            # Process failed but no BENCHMARK_ERROR - use full output as error
            error_msg = stdout.strip() if stdout.strip() else f"Process exited with code {process.returncode}"
            return {
                'execution_time': execution_time,
                'peak_memory_mb': None,
                'coherence_cv': None,
                'state': 'FAILED',
                'error': error_msg
            }

        # Parse metrics from stdout
        metrics = parse_benchmark_result(stdout)
        coherence_cv = parse_coherence_from_output(stdout)

        # Check if we got valid metrics
        state = metrics.get('state', 'UNKNOWN')
        if not metrics or state not in ['SUCCESS', 'COMPLETED']:
            # No valid result found - something went wrong
            error_msg = f"No valid benchmark result found. State: {state}. Output: {stdout[-500:]}" if stdout else "No output captured"
            return {
                'execution_time': execution_time,
                'peak_memory_mb': None,
                'coherence_cv': None,
                'state': 'FAILED',
                'error': error_msg
            }

        return {
            'execution_time': execution_time,
            'peak_memory_mb': metrics.get('peak_memory_mb'),
            'coherence_cv': coherence_cv,
            'state': 'SUCCESS',
            'error': None
        }

    except Exception as e:
        return {
            'execution_time': None,
            'peak_memory_mb': None,
            'coherence_cv': None,
            'state': 'ERROR',
            'error': str(e)
        }
    finally:
        # Clean up temporary script
        try:
            os.unlink(worker_script)
        except OSError:
            pass


def run_benchmark_suite(
    db: Session,
    config_id: int,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """Run a complete benchmark suite with multiple iterations.

    Args:
        db: Database session
        config_id: Benchmark configuration ID
        progress_callback: Optional callback(current_run, total_runs, status_message)

    Returns:
        Aggregated results dictionary
    """
    # Load config and dataset
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()

    if not config:
        raise ValueError(f"Benchmark config {config_id} not found")

    dataset = config.dataset

    # Create output directory for this benchmark
    output_base_dir = Path(__file__).parent.parent / "data" / "outputs" / f"benchmark_{config_id}"
    output_base_dir.mkdir(parents=True, exist_ok=True)

    # Initialize result tracking
    execution_times: List[float] = []
    peak_memories: List[float] = []
    coherence_scores: List[float] = []
    successful_runs = 0

    # Run benchmark iterations
    for i in range(config.num_runs):
        # Check if stop was requested before starting next run
        if is_benchmark_stopped(config_id):
            if progress_callback:
                progress_callback(i, config.num_runs, "Benchmark stopped by user")
            break

        run_number = i + 1

        if progress_callback:
            progress_callback(run_number, config.num_runs, f"Running iteration {run_number}/{config.num_runs}")

        # Get output buffer from status for real-time streaming
        status = get_benchmark_status(config_id)
        output_buffer = status.get('output_buffer') if status else None

        # Determine use_cache: False for first run (to build cache), True for subsequent runs
        use_cache = (run_number > 1)

        # Add run separator to output
        if output_buffer:
            output_buffer.append(f"\n{'='*60}")
            output_buffer.append(f"  Starting Run {run_number}/{config.num_runs} (use_cache={use_cache})")
            output_buffer.append(f"{'='*60}\n")

        # Create run record
        run = models.BenchmarkRun(
            config_id=config_id,
            run_number=run_number,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(run)
        db.commit()

        # Execute benchmark with real-time output capture
        # First run uses use_cache=False to build cache, subsequent runs use cache
        result = run_single_benchmark(config, dataset, str(output_base_dir), output_buffer, config_id, use_cache)

        # Check if stopped during execution
        if result['state'] == 'STOPPED':
            run.completed_at = datetime.utcnow()
            run.status = "stopped"
            run.error_message = "Stopped by user"
            db.commit()
            break

        # Update run record
        run.completed_at = datetime.utcnow()
        run.execution_time_seconds = result.get('execution_time')
        run.peak_memory_mb = result.get('peak_memory_mb')

        if result['state'] == 'SUCCESS':
            run.status = "completed"
            successful_runs += 1

            if result['execution_time']:
                execution_times.append(result['execution_time'])
            if result['peak_memory_mb']:
                peak_memories.append(result['peak_memory_mb'])
            if result['coherence_cv']:
                coherence_scores.append(result['coherence_cv'])

                # Store coherence metric
                metric = models.BenchmarkMetric(
                    run_id=run.id,
                    metric_type="coherence_cv",
                    metric_value=result['coherence_cv']
                )
                db.add(metric)
        else:
            run.status = "failed"
            run.error_message = result.get('error', 'Unknown error')

        db.commit()

    # Calculate aggregated statistics
    def calc_stats(values: List[float]) -> tuple:
        if not values:
            return None, None
        avg = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        return avg, std

    avg_time, std_time = calc_stats(execution_times)
    avg_memory, std_memory = calc_stats(peak_memories)
    avg_coherence, std_coherence = calc_stats(coherence_scores)

    # Create or update result record
    existing_result = db.query(models.BenchmarkResult).filter(
        models.BenchmarkResult.config_id == config_id
    ).first()

    if existing_result:
        result_record = existing_result
    else:
        result_record = models.BenchmarkResult(config_id=config_id)
        db.add(result_record)

    result_record.avg_execution_time = avg_time
    result_record.std_execution_time = std_time
    result_record.avg_peak_memory_mb = avg_memory
    result_record.std_peak_memory_mb = std_memory
    result_record.avg_coherence_cv = avg_coherence
    result_record.std_coherence_cv = std_coherence
    result_record.total_runs = config.num_runs
    result_record.successful_runs = successful_runs
    result_record.computed_at = datetime.utcnow()

    db.commit()

    if progress_callback:
        progress_callback(config.num_runs, config.num_runs, "Benchmark completed")

    return {
        'config_id': config_id,
        'total_runs': config.num_runs,
        'successful_runs': successful_runs,
        'avg_execution_time': avg_time,
        'std_execution_time': std_time,
        'avg_peak_memory_mb': avg_memory,
        'std_peak_memory_mb': std_memory,
        'avg_coherence_cv': avg_coherence,
        'std_coherence_cv': std_coherence,
    }


# Global state for tracking running benchmarks
_running_benchmarks: Dict[int, Dict[str, Any]] = {}
_benchmark_locks: Dict[int, threading.Lock] = {}


def _get_benchmark_lock(config_id: int) -> threading.Lock:
    """Get or create a lock for a benchmark."""
    if config_id not in _benchmark_locks:
        _benchmark_locks[config_id] = threading.Lock()
    return _benchmark_locks[config_id]


def get_benchmark_status(config_id: int) -> Optional[Dict[str, Any]]:
    """Get the status of a running benchmark."""
    return _running_benchmarks.get(config_id)


def set_benchmark_status(config_id: int, status: Dict[str, Any]):
    """Set the status of a running benchmark.

    Preserves existing output_buffer, stop_requested flag, and process if present.
    """
    if config_id in _running_benchmarks:
        # Preserve existing output buffer
        existing_buffer = _running_benchmarks[config_id].get('output_buffer')
        if existing_buffer:
            status['output_buffer'] = existing_buffer
        # Preserve stop_requested flag
        if _running_benchmarks[config_id].get('stop_requested'):
            status['stop_requested'] = True
        # Preserve current process reference
        existing_process = _running_benchmarks[config_id].get('process')
        if existing_process:
            status['process'] = existing_process
    if 'output_buffer' not in status:
        # Initialize new output buffer
        status['output_buffer'] = OutputBuffer(maxlen=10000)
    if 'stop_requested' not in status:
        status['stop_requested'] = False
    _running_benchmarks[config_id] = status


def clear_benchmark_status(config_id: int):
    """Clear the status of a completed benchmark."""
    _running_benchmarks.pop(config_id, None)
    _benchmark_locks.pop(config_id, None)


def stop_benchmark(config_id: int) -> bool:
    """Request a benchmark to stop.

    Args:
        config_id: Benchmark configuration ID

    Returns:
        True if stop was requested, False if benchmark not found
    """
    status = _running_benchmarks.get(config_id)
    if not status:
        return False

    # Set the stop flag
    status['stop_requested'] = True

    # Kill the current process if running
    process = status.get('process')
    if process and process.poll() is None:  # Process is still running
        try:
            process.terminate()
            # Give it a moment to terminate gracefully
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if it doesn't terminate
        except Exception:
            pass

    # Add message to output buffer
    output_buffer = status.get('output_buffer')
    if output_buffer:
        output_buffer.append("\n" + "=" * 60)
        output_buffer.append("  BENCHMARK STOPPED BY USER")
        output_buffer.append("=" * 60 + "\n")

    return True


def is_benchmark_stopped(config_id: int) -> bool:
    """Check if a benchmark has been requested to stop."""
    status = _running_benchmarks.get(config_id)
    return status.get('stop_requested', False) if status else False


def set_current_process(config_id: int, process: subprocess.Popen):
    """Set the current subprocess for a benchmark."""
    status = _running_benchmarks.get(config_id)
    if status:
        status['process'] = process


def get_benchmark_output(config_id: int, offset: int = 0) -> Optional[Dict[str, Any]]:
    """Get buffered output for a running benchmark.

    Args:
        config_id: Benchmark configuration ID
        offset: Number of lines to skip from the beginning

    Returns:
        Dict with 'lines', 'total_lines', 'offset' or None if not found
    """
    status = _running_benchmarks.get(config_id)
    if status and 'output_buffer' in status:
        buffer = status['output_buffer']
        lines, total = buffer.get_lines(offset)
        return {
            'lines': lines,
            'total_lines': total,
            'offset': offset + len(lines)
        }
    return None
