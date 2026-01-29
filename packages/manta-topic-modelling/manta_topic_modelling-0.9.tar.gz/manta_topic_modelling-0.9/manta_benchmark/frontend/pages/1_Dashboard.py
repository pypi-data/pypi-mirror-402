"""Dashboard page showing overview of benchmarks."""

import html
import time
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.api_client import (
    check_api_health, list_datasets, list_benchmarks,
    list_comparisons, get_benchmark_status, get_benchmark_output
)

st.set_page_config(page_title="Dashboard - MANTA Benchmark", layout="wide")

st.title("Dashboard")

# Check API health
if not check_api_health():
    st.error("API is not available. Please start the backend server first.")
    st.code("uvicorn manta_benchmark.backend.main:app --reload", language="bash")
    st.stop()

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

try:
    datasets = list_datasets()
    benchmarks = list_benchmarks()
    comparisons = list_comparisons()

    # Count running benchmarks
    running_count = 0
    for b in benchmarks:
        try:
            status = get_benchmark_status(b['id'])
            if status.get('status') == 'running':
                running_count += 1
        except Exception:
            pass

    with col1:
        st.metric("Total Datasets", len(datasets))

    with col2:
        st.metric("Total Benchmarks", len(benchmarks))

    with col3:
        st.metric("Running", running_count)

    with col4:
        st.metric("Comparison Groups", len(comparisons))

except Exception as e:
    st.error(f"Failed to load data: {str(e)}")
    datasets = []
    benchmarks = []
    comparisons = []

st.markdown("---")

# Running Benchmarks Section
st.subheader("Running Benchmarks")

# Find all running benchmarks
running_benchmarks = []
for b in benchmarks:
    try:
        status = get_benchmark_status(b['id'])
        if status.get('status') == 'running':
            running_benchmarks.append({
                'id': b['id'],
                'name': b['name'],
                'status': status
            })
    except Exception:
        pass

if running_benchmarks:
    # CSS for scrollable log containers
    st.markdown("""
    <style>
    .log-container-dashboard {
        height: 300px;
        overflow-y: auto;
        background-color: #0e1117;
        border-radius: 5px;
        padding: 10px;
        font-family: 'Source Code Pro', monospace;
        font-size: 12px;
        line-height: 1.4;
        white-space: pre-wrap;
        word-wrap: break-word;
        color: #fafafa;
        border: 1px solid #262730;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state for output tracking
    if 'dashboard_log_offsets' not in st.session_state:
        st.session_state.dashboard_log_offsets = {}
    if 'dashboard_log_lines' not in st.session_state:
        st.session_state.dashboard_log_lines = {}

    for rb in running_benchmarks:
        config_id = rb['id']
        status = rb['status']

        with st.container():
            # Header with benchmark info and progress
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{rb['name']}** (ID: {config_id})")
            with col2:
                progress = status.get('progress_percent', 0)
                st.progress(int(progress) / 100, text=f"{progress:.0f}%")

            st.caption(status.get('message', 'Running...'))

            # Fetch output
            offset = st.session_state.dashboard_log_offsets.get(config_id, 0)
            if config_id not in st.session_state.dashboard_log_lines:
                st.session_state.dashboard_log_lines[config_id] = []

            try:
                output = get_benchmark_output(config_id, offset=offset)
                if output and output.get('lines'):
                    st.session_state.dashboard_log_lines[config_id].extend(output['lines'])
                    st.session_state.dashboard_log_offsets[config_id] = output.get('offset', offset)
            except Exception:
                pass

            # Display log output
            display_lines = st.session_state.dashboard_log_lines.get(config_id, [])[-300:]
            log_text = '\n'.join(display_lines) if display_lines else "Waiting for output..."
            escaped_log = html.escape(log_text)
            st.markdown(
                f'<div class="log-container-dashboard">{escaped_log}</div>',
                unsafe_allow_html=True
            )
            st.markdown("")  # Spacing between benchmarks

    # Auto-refresh while benchmarks are running
    time.sleep(2)
    st.rerun()

else:
    st.info("No benchmarks are currently running.")
    if st.button("Start a New Benchmark"):
        st.switch_page("pages/2_New_Benchmark.py")

st.markdown("---")

# Recent benchmarks
st.subheader("Recent Benchmarks")

if benchmarks:
    # Create DataFrame for display
    benchmark_data = []
    for b in benchmarks[:10]:  # Show last 10
        try:
            status = get_benchmark_status(b['id'])
            status_str = status.get('status', 'unknown')
            progress = status.get('progress_percent', 0)
        except Exception:
            status_str = 'unknown'
            progress = 0

        benchmark_data.append({
            'ID': b['id'],
            'Name': b['name'],
            'Dataset': b.get('dataset_id', 'N/A'),
            'Language': b['language'],
            'Topics': b['topic_count'],
            'Method': b['nmf_method'],
            'Runs': b['num_runs'],
            'Status': status_str,
            'Progress': f"{progress:.0f}%"
        })

    df = pd.DataFrame(benchmark_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Quick actions
    st.markdown("**Quick Actions:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("View All Results"):
            st.switch_page("pages/3_Results.py")

    with col2:
        if st.button("Create New Benchmark"):
            st.switch_page("pages/2_New_Benchmark.py")

    with col3:
        if st.button("Compare Benchmarks"):
            st.switch_page("pages/4_Compare.py")

else:
    st.info("No benchmarks created yet. Create your first benchmark to get started!")
    if st.button("Create Benchmark"):
        st.switch_page("pages/2_New_Benchmark.py")

st.markdown("---")

# Recent datasets
st.subheader("Available Datasets")

if datasets:
    dataset_data = []
    for d in datasets[:5]:  # Show last 5
        dataset_data.append({
            'ID': d['id'],
            'Name': d['name'],
            'File': d['filename'],
            'Text Column': d['text_column'],
            'Rows': d.get('row_count', 'N/A'),
            'Size': f"{d.get('file_size_bytes', 0) / 1024:.1f} KB"
        })

    df = pd.DataFrame(dataset_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("Manage Datasets"):
        st.switch_page("pages/5_Datasets.py")

else:
    st.info("No datasets uploaded yet. Upload a dataset to begin benchmarking.")
    if st.button("Upload Dataset"):
        st.switch_page("pages/5_Datasets.py")
