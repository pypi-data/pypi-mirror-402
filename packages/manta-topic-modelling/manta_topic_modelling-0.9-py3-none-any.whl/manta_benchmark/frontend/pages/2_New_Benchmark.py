"""New Benchmark page for configuring and starting benchmarks."""

import html
import streamlit as st
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.api_client import (
    check_api_health, list_datasets, create_benchmark,
    start_benchmark, get_benchmark_status, get_benchmark_output
)

st.set_page_config(page_title="New Benchmark - MANTA Benchmark", layout="wide")

st.title("Create New Benchmark")

# Check API health
if not check_api_health():
    st.error("API is not available. Please start the backend server first.")
    st.stop()

# Initialize session state
if 'benchmark_created' not in st.session_state:
    st.session_state.benchmark_created = False
if 'created_config_id' not in st.session_state:
    st.session_state.created_config_id = None

# Load datasets
try:
    datasets = list_datasets()
except Exception as e:
    st.error(f"Failed to load datasets: {str(e)}")
    datasets = []

if not datasets:
    st.warning("No datasets available. Please upload a dataset first.")
    if st.button("Go to Datasets"):
        st.switch_page("pages/5_Datasets.py")
    st.stop()

# Configuration form
st.subheader("Benchmark Configuration")

with st.form("benchmark_form"):
    # Basic info
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Benchmark Name", placeholder="e.g., BBC News - 10 Topics NMF")

    with col2:
        description = st.text_area("Description (optional)", placeholder="Describe this benchmark...")

    st.markdown("---")

    # Dataset selection
    st.subheader("Dataset")

    dataset_options = {f"{d['name']} ({d['row_count']} rows)": d['id'] for d in datasets}
    selected_dataset_label = st.selectbox("Select Dataset", options=list(dataset_options.keys()))
    dataset_id = dataset_options[selected_dataset_label]

    st.markdown("---")

    # Analysis parameters
    st.subheader("Analysis Parameters")

    col1, col2, col3 = st.columns(3)

    with col1:
        language = st.selectbox("Language", ["EN", "TR"], help="EN for English, TR for Turkish")
        topic_count = st.slider("Number of Topics", min_value=2, max_value=50, value=5)
        words_per_topic = st.slider("Words per Topic", min_value=5, max_value=30, value=15)

    with col2:
        nmf_method = st.selectbox(
            "NMF Method",
            ["nmf", "nmtf", "pnmf"],
            help="nmf: Standard NMF, nmtf: Tri-Factorization, pnmf: Projective NMF"
        )
        tokenizer_type = st.selectbox(
            "Tokenizer",
            ["bpe", "wordpiece"],
            help="Tokenization method (mainly for Turkish)"
        )
        lemmatize = st.checkbox("Enable Lemmatization", value=False, help="Apply lemmatization (English only)")

    with col3:
        n_grams = st.number_input(
            "N-grams to Discover",
            min_value=0,
            max_value=1000,
            value=0,
            help="Number of n-grams to discover via BPE (0 to disable)"
        )
        n_grams_to_discover = n_grams if n_grams > 0 else None

    st.markdown("---")

    # Benchmark settings
    st.subheader("Benchmark Settings")

    num_runs = st.slider(
        "Number of Runs",
        min_value=1,
        max_value=20,
        value=5,
        help="Number of times to run the analysis for statistical significance"
    )

    st.info(f"This benchmark will run {num_runs} iterations to compute average metrics with standard error.")

    # Submit button
    submitted = st.form_submit_button("Create Benchmark", use_container_width=True)

    if submitted:
        if not name:
            st.error("Please enter a benchmark name")
        else:
            try:
                config = {
                    "name": name,
                    "description": description,
                    "dataset_id": dataset_id,
                    "language": language,
                    "topic_count": topic_count,
                    "nmf_method": nmf_method,
                    "tokenizer_type": tokenizer_type,
                    "lemmatize": lemmatize,
                    "words_per_topic": words_per_topic,
                    "n_grams_to_discover": n_grams_to_discover,
                    "num_runs": num_runs
                }

                result = create_benchmark(config)
                st.session_state.benchmark_created = True
                st.session_state.created_config_id = result['id']
                st.success(f"Benchmark '{name}' created successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to create benchmark: {str(e)}")

# Show run button if benchmark was created
if st.session_state.benchmark_created and st.session_state.created_config_id:
    st.markdown("---")
    st.subheader("Run Benchmark")

    config_id = st.session_state.created_config_id

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Benchmark Now", type="primary", use_container_width=True):
            try:
                start_benchmark(config_id)
                st.success("Benchmark started!")

                # Progress section
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Output log section with scrollable container
                st.subheader("Analysis Output")

                # Inject CSS for scrollable log with auto-scroll to bottom
                st.markdown("""
                <style>
                .log-container {
                    height: 400px;
                    overflow-y: auto;
                    background-color: #0e1117;
                    border-radius: 5px;
                    padding: 10px;
                    font-family: 'Source Code Pro', monospace;
                    font-size: 13px;
                    line-height: 1.4;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    color: #fafafa;
                }
                </style>
                """, unsafe_allow_html=True)

                log_placeholder = st.empty()

                # State for incremental log fetching
                log_offset = 0
                accumulated_lines = []

                while True:
                    # Fetch status
                    status = get_benchmark_status(config_id)
                    progress = status.get('progress_percent', 0)
                    message = status.get('message', 'Running...')

                    progress_bar.progress(int(progress) / 100)
                    status_text.text(f"Status: {message} ({progress:.0f}%)")

                    # Fetch new output lines incrementally
                    try:
                        output = get_benchmark_output(config_id, offset=log_offset)
                        if output and output.get('lines'):
                            accumulated_lines.extend(output['lines'])
                            log_offset = output.get('offset', log_offset)

                        # Update log display (show last 500 lines to avoid slowdown)
                        display_lines = accumulated_lines[-500:]
                        log_text = '\n'.join(display_lines)
                        # Escape HTML characters and use div with scrollable container
                        escaped_log = html.escape(log_text)
                        log_placeholder.markdown(
                            f'<div class="log-container" id="log-box">{escaped_log}</div>',
                            unsafe_allow_html=True
                        )
                    except Exception:
                        pass  # Ignore output fetch errors

                    # Check completion
                    if status.get('status') == 'completed':
                        st.success("Benchmark completed!")
                        st.session_state.benchmark_created = False
                        st.session_state.created_config_id = None
                        if st.button("View Results"):
                            st.switch_page("pages/3_Results.py")
                        break
                    elif status.get('status') == 'failed':
                        st.error("Benchmark failed!")
                        break

                    time.sleep(1)  # Poll more frequently for responsiveness

            except Exception as e:
                st.error(f"Failed to start benchmark: {str(e)}")

    with col2:
        if st.button("View Results Later", use_container_width=True):
            st.session_state.benchmark_created = False
            st.session_state.created_config_id = None
            st.switch_page("pages/3_Results.py")

# Reset button
if st.session_state.benchmark_created:
    if st.button("Create Another Benchmark"):
        st.session_state.benchmark_created = False
        st.session_state.created_config_id = None
        st.rerun()
