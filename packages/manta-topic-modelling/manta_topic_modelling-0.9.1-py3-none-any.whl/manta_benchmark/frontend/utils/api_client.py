"""API client for communicating with the FastAPI backend."""

import requests
from typing import Dict, Any, Optional, List
import streamlit as st

# API base URL
API_BASE_URL = "http://localhost:8000"


def _handle_response(response: requests.Response) -> Dict[str, Any]:
    """Handle API response and raise errors if needed."""
    if response.status_code >= 400:
        try:
            error_data = response.json()
            raise Exception(error_data.get('detail', 'Unknown error'))
        except Exception:
            raise Exception(f"API error: {response.status_code}")
    return response.json()


def check_api_health() -> bool:
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def get_api_stats() -> Dict[str, int]:
    """Get API statistics."""
    try:
        datasets = requests.get(f"{API_BASE_URL}/api/datasets", timeout=2).json()
        benchmarks = requests.get(f"{API_BASE_URL}/api/benchmarks", timeout=2).json()
        comparisons = requests.get(f"{API_BASE_URL}/api/comparisons", timeout=2).json()
        return {
            'datasets': len(datasets),
            'benchmarks': len(benchmarks),
            'comparisons': len(comparisons)
        }
    except Exception:
        return {'datasets': 0, 'benchmarks': 0, 'comparisons': 0}


# ============== Dataset API ==============

def scan_datasets_folder() -> List[Dict[str, Any]]:
    """Scan the datasets folder for available files."""
    response = requests.get(f"{API_BASE_URL}/api/datasets/scan")
    return _handle_response(response)


def register_dataset(filepath: str, name: str, text_column: str, separator: str = ",") -> Dict[str, Any]:
    """Register a dataset from the datasets folder."""
    params = {
        "filepath": filepath,
        "name": name,
        "text_column": text_column,
        "separator": separator
    }
    response = requests.post(f"{API_BASE_URL}/api/datasets/register", params=params)
    return _handle_response(response)


def list_datasets() -> List[Dict[str, Any]]:
    """List all datasets."""
    response = requests.get(f"{API_BASE_URL}/api/datasets")
    return _handle_response(response)


def get_dataset(dataset_id: int) -> Dict[str, Any]:
    """Get a specific dataset."""
    response = requests.get(f"{API_BASE_URL}/api/datasets/{dataset_id}")
    return _handle_response(response)


def get_dataset_columns(dataset_id: int) -> List[str]:
    """Get column names for a dataset."""
    response = requests.get(f"{API_BASE_URL}/api/datasets/{dataset_id}/columns")
    return _handle_response(response)


def preview_dataset(dataset_id: int, rows: int = 10) -> Dict[str, Any]:
    """Preview first N rows of a dataset."""
    response = requests.get(f"{API_BASE_URL}/api/datasets/{dataset_id}/preview", params={"rows": rows})
    return _handle_response(response)


def delete_dataset(dataset_id: int) -> Dict[str, Any]:
    """Delete a dataset."""
    response = requests.delete(f"{API_BASE_URL}/api/datasets/{dataset_id}")
    return _handle_response(response)


# ============== Benchmark API ==============

def create_benchmark(config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new benchmark configuration."""
    response = requests.post(f"{API_BASE_URL}/api/benchmarks", json=config)
    return _handle_response(response)


def list_benchmarks() -> List[Dict[str, Any]]:
    """List all benchmarks."""
    response = requests.get(f"{API_BASE_URL}/api/benchmarks")
    return _handle_response(response)


def get_benchmark(config_id: int) -> Dict[str, Any]:
    """Get a specific benchmark with all details."""
    response = requests.get(f"{API_BASE_URL}/api/benchmarks/{config_id}")
    return _handle_response(response)


def delete_benchmark(config_id: int) -> Dict[str, Any]:
    """Delete a benchmark."""
    response = requests.delete(f"{API_BASE_URL}/api/benchmarks/{config_id}")
    return _handle_response(response)


def start_benchmark(config_id: int) -> Dict[str, Any]:
    """Start running a benchmark."""
    response = requests.post(f"{API_BASE_URL}/api/benchmarks/{config_id}/run")
    return _handle_response(response)


def get_benchmark_status(config_id: int) -> Dict[str, Any]:
    """Get the status of a benchmark execution."""
    response = requests.get(f"{API_BASE_URL}/api/benchmarks/{config_id}/status")
    return _handle_response(response)


def get_benchmark_results(config_id: int) -> Optional[Dict[str, Any]]:
    """Get the results of a completed benchmark."""
    response = requests.get(f"{API_BASE_URL}/api/benchmarks/{config_id}/results")
    if response.status_code == 200:
        return response.json()
    return None


def get_benchmark_runs(config_id: int) -> List[Dict[str, Any]]:
    """Get all runs for a benchmark."""
    response = requests.get(f"{API_BASE_URL}/api/benchmarks/{config_id}/runs")
    return _handle_response(response)


def get_benchmark_output(config_id: int, offset: int = 0) -> Dict[str, Any]:
    """Get real-time output from a running benchmark.

    Args:
        config_id: Benchmark configuration ID
        offset: Line offset for incremental fetching

    Returns:
        Dict with 'lines', 'total_lines', 'offset', 'has_more'
    """
    response = requests.get(
        f"{API_BASE_URL}/api/benchmarks/{config_id}/output",
        params={"offset": offset}
    )
    return _handle_response(response)


def stop_benchmark(config_id: int) -> Dict[str, Any]:
    """Stop a running benchmark.

    Args:
        config_id: Benchmark configuration ID

    Returns:
        Dict with 'message' and 'success'
    """
    response = requests.post(f"{API_BASE_URL}/api/benchmarks/{config_id}/stop")
    return _handle_response(response)


# ============== Comparison API ==============

def create_comparison(name: str, description: str, config_ids: List[int]) -> Dict[str, Any]:
    """Create a new comparison group."""
    data = {
        "name": name,
        "description": description,
        "config_ids": config_ids
    }
    response = requests.post(f"{API_BASE_URL}/api/comparisons", json=data)
    return _handle_response(response)


def list_comparisons() -> List[Dict[str, Any]]:
    """List all comparison groups."""
    response = requests.get(f"{API_BASE_URL}/api/comparisons")
    return _handle_response(response)


def get_comparison(group_id: int) -> Dict[str, Any]:
    """Get comparison data for a group."""
    response = requests.get(f"{API_BASE_URL}/api/comparisons/{group_id}")
    return _handle_response(response)


def delete_comparison(group_id: int) -> Dict[str, Any]:
    """Delete a comparison group."""
    response = requests.delete(f"{API_BASE_URL}/api/comparisons/{group_id}")
    return _handle_response(response)


def export_comparison(group_id: int, format: str = "json") -> Any:
    """Export comparison data."""
    response = requests.get(f"{API_BASE_URL}/api/comparisons/{group_id}/export", params={"format": format})
    if format == "csv":
        return response.content
    return _handle_response(response)
