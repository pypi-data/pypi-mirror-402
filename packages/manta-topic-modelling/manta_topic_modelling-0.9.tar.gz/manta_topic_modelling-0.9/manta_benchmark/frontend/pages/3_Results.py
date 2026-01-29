"""Results page for viewing benchmark results."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.api_client import (
    check_api_health, list_benchmarks, get_benchmark,
    get_benchmark_status, get_benchmark_runs, delete_benchmark,
    start_benchmark
)

st.set_page_config(page_title="Results - MANTA Benchmark", layout="wide")

st.title("Benchmark Results")

# Check API health
if not check_api_health():
    st.error("API is not available. Please start the backend server first.")
    st.stop()

# Load benchmarks
try:
    benchmarks = list_benchmarks()
except Exception as e:
    st.error(f"Failed to load benchmarks: {str(e)}")
    benchmarks = []

if not benchmarks:
    st.info("No benchmarks created yet.")
    if st.button("Create Benchmark"):
        st.switch_page("pages/2_New_Benchmark.py")
    st.stop()

# Sidebar for benchmark selection
st.sidebar.subheader("Select Benchmark")

benchmark_options = {f"{b['name']} (ID: {b['id']})": b['id'] for b in benchmarks}
selected_label = st.sidebar.selectbox("Benchmark", options=list(benchmark_options.keys()))
selected_id = benchmark_options[selected_label]

# Load benchmark details
try:
    benchmark = get_benchmark(selected_id)
    status = get_benchmark_status(selected_id)
    runs = get_benchmark_runs(selected_id)
except Exception as e:
    st.error(f"Failed to load benchmark details: {str(e)}")
    st.stop()

# Display benchmark info
st.subheader(benchmark['config']['name'])

if benchmark['config'].get('description'):
    st.markdown(f"*{benchmark['config']['description']}*")

# Status and actions
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    status_str = status.get('status', 'unknown')
    if status_str == 'completed':
        st.success(f"Status: Completed ({status['successful_runs']}/{status['total_runs']} runs)")
    elif status_str == 'running':
        st.warning(f"Status: Running ({status['progress_percent']:.0f}%)")
        st.progress(int(status['progress_percent']) / 100)
    elif status_str == 'failed':
        st.error("Status: Failed")
    else:
        st.info("Status: Pending")

with col2:
    if status_str != 'running':
        if st.button("Run/Rerun Benchmark"):
            try:
                start_benchmark(selected_id)
                st.success("Benchmark started!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to start: {str(e)}")

with col3:
    if st.button("Delete Benchmark", type="secondary"):
        if st.session_state.get('confirm_delete') == selected_id:
            try:
                delete_benchmark(selected_id)
                st.success("Deleted!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete: {str(e)}")
        else:
            st.session_state.confirm_delete = selected_id
            st.warning("Click again to confirm deletion")

st.markdown("---")

# Configuration summary
st.subheader("Configuration")

config = benchmark['config']
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Dataset", benchmark['dataset']['name'])
    st.metric("Language", config['language'])

with col2:
    st.metric("Topics", config['topic_count'])
    st.metric("Words/Topic", config['words_per_topic'])

with col3:
    st.metric("NMF Method", config['nmf_method'])
    st.metric("Tokenizer", config['tokenizer_type'])

with col4:
    st.metric("Lemmatize", "Yes" if config['lemmatize'] else "No")
    st.metric("Num Runs", config['num_runs'])

st.markdown("---")

# Results section
if benchmark.get('result'):
    result = benchmark['result']

    st.subheader("Aggregated Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if result.get('avg_execution_time'):
            st.metric(
                "Execution Time",
                f"{result['avg_execution_time']:.2f}s",
                f"± {result.get('std_execution_time', 0):.2f}s"
            )
        else:
            st.metric("Execution Time", "N/A")

    with col2:
        if result.get('avg_peak_memory_mb'):
            st.metric(
                "Peak Memory",
                f"{result['avg_peak_memory_mb']:.1f} MB",
                f"± {result.get('std_peak_memory_mb', 0):.1f} MB"
            )
        else:
            st.metric("Peak Memory", "N/A")

    with col3:
        if result.get('avg_coherence_cv'):
            st.metric(
                "Coherence (C_v)",
                f"{result['avg_coherence_cv']:.4f}",
                f"± {result.get('std_coherence_cv', 0):.4f}"
            )
        else:
            st.metric("Coherence (C_v)", "N/A")

    with col4:
        if result.get('avg_diversity_puw'):
            st.metric("Diversity (PUW)", f"{result['avg_diversity_puw']:.4f}")
        else:
            st.metric("Diversity", "N/A")

    st.markdown("---")

    # Per-run charts
    st.subheader("Per-Run Analysis")

    if runs:
        # Create DataFrames for charts
        run_data = []
        for run in runs:
            if run['status'] == 'completed':
                run_data.append({
                    'Run': run['run_number'],
                    'Execution Time (s)': run.get('execution_time_seconds', 0),
                    'Peak Memory (MB)': run.get('peak_memory_mb', 0),
                    'Coherence': next(
                        (m['metric_value'] for m in run.get('metrics', []) if m['metric_type'] == 'coherence_cv'),
                        None
                    )
                })

        if run_data:
            df = pd.DataFrame(run_data)

            col1, col2 = st.columns(2)

            with col1:
                # Execution time chart
                fig = px.bar(
                    df,
                    x='Run',
                    y='Execution Time (s)',
                    title='Execution Time per Run',
                    color='Execution Time (s)',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Memory usage chart
                fig = px.bar(
                    df,
                    x='Run',
                    y='Peak Memory (MB)',
                    title='Peak Memory per Run',
                    color='Peak Memory (MB)',
                    color_continuous_scale='Oranges'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # Box plots
            col1, col2 = st.columns(2)

            with col1:
                fig = px.box(
                    df,
                    y='Execution Time (s)',
                    title='Execution Time Distribution',
                    points='all'
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.box(
                    df,
                    y='Peak Memory (MB)',
                    title='Memory Usage Distribution',
                    points='all'
                )
                st.plotly_chart(fig, use_container_width=True)

            # Coherence if available
            if df['Coherence'].notna().any():
                fig = px.line(
                    df,
                    x='Run',
                    y='Coherence',
                    title='Coherence Score per Run',
                    markers=True
                )
                fig.add_hline(
                    y=result.get('avg_coherence_cv', 0),
                    line_dash="dash",
                    annotation_text="Average"
                )
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Raw data table
    st.subheader("Run Details")

    if runs:
        runs_df = pd.DataFrame([
            {
                'Run #': r['run_number'],
                'Status': r['status'],
                'Time (s)': f"{r.get('execution_time_seconds', 0):.2f}" if r.get('execution_time_seconds') else 'N/A',
                'Memory (MB)': f"{r.get('peak_memory_mb', 0):.1f}" if r.get('peak_memory_mb') else 'N/A',
                'Error': r.get('error_message', '')[:50] if r.get('error_message') else ''
            }
            for r in runs
        ])
        st.dataframe(runs_df, use_container_width=True, hide_index=True)

else:
    if status_str == 'running':
        st.info("Benchmark is currently running. Results will appear here when complete.")
    elif status_str == 'pending':
        st.info("Benchmark has not been run yet. Click 'Run Benchmark' to start.")
    else:
        st.warning("No results available. The benchmark may have failed or was not completed.")
