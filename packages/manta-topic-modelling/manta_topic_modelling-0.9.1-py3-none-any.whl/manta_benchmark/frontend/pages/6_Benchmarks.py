"""Benchmarks management page for viewing and controlling running benchmarks."""

import html
import time
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.api_client import (
    check_api_health, list_benchmarks, get_benchmark,
    get_benchmark_status, get_benchmark_output, stop_benchmark,
    start_benchmark, delete_benchmark
)

st.set_page_config(page_title="Benchmarks - MANTA Benchmark", layout="wide")

st.title("Benchmarks")

# Check API health
if not check_api_health():
    st.error("API is not available. Please start the backend server first.")
    st.stop()

# CSS for scrollable log containers
st.markdown("""
<style>
.benchmark-log {
    height: 350px;
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
.benchmark-card {
    border: 1px solid #262730;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 15px;
    background-color: #0e1117;
}
</style>
""", unsafe_allow_html=True)

# Load benchmarks
try:
    benchmarks = list_benchmarks()
except Exception as e:
    st.error(f"Failed to load benchmarks: {str(e)}")
    benchmarks = []

# Categorize benchmarks
running_benchmarks = []
completed_benchmarks = []
pending_benchmarks = []

for b in benchmarks:
    try:
        status = get_benchmark_status(b['id'])
        status_str = status.get('status', 'pending')
        b['_status'] = status
        b['_status_str'] = status_str

        if status_str == 'running':
            running_benchmarks.append(b)
        elif status_str == 'completed':
            completed_benchmarks.append(b)
        else:
            pending_benchmarks.append(b)
    except Exception:
        b['_status'] = None
        b['_status_str'] = 'pending'
        pending_benchmarks.append(b)

# Initialize session state for output tracking
if 'benchmark_log_offsets' not in st.session_state:
    st.session_state.benchmark_log_offsets = {}
if 'benchmark_log_lines' not in st.session_state:
    st.session_state.benchmark_log_lines = {}

# ============== Running Benchmarks Section ==============
st.subheader(f"Running Benchmarks ({len(running_benchmarks)})")

if running_benchmarks:
    for b in running_benchmarks:
        config_id = b['id']
        status = b['_status']

        with st.container():
            # Header row
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"### {b['name']}")
                st.caption(f"ID: {config_id} | Topics: {b['topic_count']} | Method: {b['nmf_method']} | Runs: {b['num_runs']}")

            with col2:
                if status:
                    progress = status.get('progress_percent', 0)
                    st.metric("Progress", f"{progress:.0f}%")

            with col3:
                # Stop button
                if st.button("Stop", key=f"stop_{config_id}", type="primary", use_container_width=True):
                    try:
                        result = stop_benchmark(config_id)
                        st.success(result.get('message', 'Stop requested'))
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to stop: {str(e)}")

            # Progress bar
            if status:
                progress = status.get('progress_percent', 0)
                st.progress(int(progress) / 100)
                st.caption(status.get('message', 'Running...'))

            # Fetch and display output
            offset = st.session_state.benchmark_log_offsets.get(config_id, 0)
            if config_id not in st.session_state.benchmark_log_lines:
                st.session_state.benchmark_log_lines[config_id] = []

            try:
                output = get_benchmark_output(config_id, offset=offset)
                if output and output.get('lines'):
                    st.session_state.benchmark_log_lines[config_id].extend(output['lines'])
                    st.session_state.benchmark_log_offsets[config_id] = output.get('offset', offset)
            except Exception:
                pass

            # Display log
            display_lines = st.session_state.benchmark_log_lines.get(config_id, [])[-300:]
            log_text = '\n'.join(display_lines) if display_lines else "Waiting for output..."
            escaped_log = html.escape(log_text)
            st.markdown(
                f'<div class="benchmark-log">{escaped_log}</div>',
                unsafe_allow_html=True
            )

            st.markdown("---")

    # Auto-refresh while benchmarks are running
    time.sleep(2)
    st.rerun()

else:
    st.info("No benchmarks are currently running.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create New Benchmark", use_container_width=True):
            st.switch_page("pages/2_New_Benchmark.py")

st.markdown("---")

# ============== All Benchmarks Table ==============
st.subheader("All Benchmarks")

if benchmarks:
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["All", f"Completed ({len(completed_benchmarks)})", f"Pending ({len(pending_benchmarks)})"])

    def display_benchmark_table(benchmark_list):
        if not benchmark_list:
            st.info("No benchmarks in this category.")
            return

        data = []
        for b in benchmark_list:
            status = b.get('_status')
            progress = status.get('progress_percent', 0) if status else 0
            status_str = b.get('_status_str', 'pending')

            data.append({
                'ID': b['id'],
                'Name': b['name'],
                'Language': b['language'],
                'Topics': b['topic_count'],
                'Method': b['nmf_method'],
                'Runs': b['num_runs'],
                'Status': status_str.upper(),
                'Progress': f"{progress:.0f}%"
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab1:
        display_benchmark_table(benchmarks)

    with tab2:
        display_benchmark_table(completed_benchmarks)

    with tab3:
        display_benchmark_table(pending_benchmarks)

        # Option to start pending benchmarks
        if pending_benchmarks:
            st.markdown("### Start a Pending Benchmark")
            selected_benchmark = st.selectbox(
                "Select benchmark to start",
                options=[b['id'] for b in pending_benchmarks],
                format_func=lambda x: next((b['name'] for b in pending_benchmarks if b['id'] == x), str(x))
            )

            if st.button("Start Selected Benchmark", type="primary"):
                try:
                    start_benchmark(selected_benchmark)
                    st.success("Benchmark started!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start: {str(e)}")

else:
    st.info("No benchmarks created yet.")
    if st.button("Create Your First Benchmark"):
        st.switch_page("pages/2_New_Benchmark.py")

st.markdown("---")

# ============== Benchmark Details ==============
st.subheader("Benchmark Details")

if benchmarks:
    selected_id = st.selectbox(
        "Select a benchmark to view details",
        options=[b['id'] for b in benchmarks],
        format_func=lambda x: next((f"{b['name']} (ID: {x})" for b in benchmarks if b['id'] == x), str(x))
    )

    if selected_id:
        try:
            details = get_benchmark(selected_id)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Configuration**")
                st.json({
                    'name': details['config']['name'],
                    'description': details['config'].get('description', 'N/A'),
                    'language': details['config']['language'],
                    'topic_count': details['config']['topic_count'],
                    'nmf_method': details['config']['nmf_method'],
                    'tokenizer_type': details['config']['tokenizer_type'],
                    'lemmatize': details['config']['lemmatize'],
                    'words_per_topic': details['config']['words_per_topic'],
                    'num_runs': details['config']['num_runs']
                })

            with col2:
                st.markdown("**Results**")
                if details.get('result'):
                    result = details['result']
                    avg_time = result.get('avg_execution_time')
                    avg_coherence = result.get('avg_coherence_cv')
                    successful = result.get('successful_runs', 0) or 0
                    total = result.get('total_runs', 0) or 0

                    st.metric("Avg Execution Time", f"{avg_time:.2f}s" if avg_time is not None else "N/A")
                    st.metric("Avg Coherence (c_v)", f"{avg_coherence:.4f}" if avg_coherence is not None else "N/A")
                    st.metric("Successful Runs", f"{successful}/{total}")
                else:
                    st.info("No results yet - benchmark may not have completed.")

            # Actions
            st.markdown("**Actions**")
            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                if details['status'] == 'pending':
                    if st.button("Start Benchmark", key="start_detail", use_container_width=True):
                        try:
                            start_benchmark(selected_id)
                            st.success("Benchmark started!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {str(e)}")

            with action_col2:
                if st.button("View Full Results", key="view_results", use_container_width=True):
                    st.switch_page("pages/3_Results.py")

            with action_col3:
                if details['status'] != 'running':
                    if st.button("Delete Benchmark", key="delete_detail", type="secondary", use_container_width=True):
                        try:
                            delete_benchmark(selected_id)
                            st.success("Benchmark deleted!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {str(e)}")
                else:
                    st.warning("Cannot delete running benchmark")

        except Exception as e:
            st.error(f"Failed to load benchmark details: {str(e)}")
