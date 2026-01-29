"""Datasets management page - folder-based."""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.api_client import (
    check_api_health, list_datasets, register_dataset,
    get_dataset, preview_dataset, delete_dataset,
    get_dataset_columns, scan_datasets_folder
)

st.set_page_config(page_title="Datasets - MANTA Benchmark", layout="wide")

st.title("Dataset Management")

# Check API health
if not check_api_health():
    st.error("API is not available. Please start the backend server first.")
    st.stop()

# Tabs for scan and manage
tab1, tab2 = st.tabs(["Available Files", "Registered Datasets"])

with tab1:
    st.subheader("Datasets Folder")
    st.info("Place your CSV/Excel files in the `manta_benchmark/datasets/` folder, then register them here.")

    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Scan folder for files
    try:
        available_files = scan_datasets_folder()
    except Exception as e:
        st.error(f"Failed to scan folder: {str(e)}")
        available_files = []

    if not available_files:
        st.warning("No CSV or Excel files found in the datasets folder.")
        st.markdown("**Datasets folder location:** `manta_benchmark/datasets/`")
    else:
        # Filter out already registered files
        unregistered_files = [f for f in available_files if not f.get('is_registered', False)]
        registered_files = [f for f in available_files if f.get('is_registered', False)]

        if unregistered_files:
            st.markdown(f"**Found {len(unregistered_files)} unregistered file(s):**")

            for file_info in unregistered_files:
                with st.expander(f"📄 {file_info['filename']} ({file_info['size_bytes'] / 1024:.1f} KB)"):
                    st.write(f"**Path:** `{file_info['filepath']}`")

                    if file_info.get('columns'):
                        st.write("**Columns:**")
                        st.code(", ".join(file_info['columns']))

                        # Registration form
                        with st.form(key=f"register_{file_info['filename']}"):
                            st.markdown("**Register this dataset:**")

                            col1, col2 = st.columns(2)
                            with col1:
                                name = st.text_input(
                                    "Dataset Name",
                                    value=Path(file_info['filename']).stem,
                                    key=f"name_{file_info['filename']}"
                                )
                            with col2:
                                separator = st.selectbox(
                                    "CSV Separator",
                                    [",", ";", "\t", "|"],
                                    key=f"sep_{file_info['filename']}"
                                )

                            text_column = st.selectbox(
                                "Text Column",
                                file_info['columns'],
                                key=f"col_{file_info['filename']}"
                            )

                            if st.form_submit_button("Register Dataset", use_container_width=True):
                                try:
                                    result = register_dataset(
                                        file_info['filepath'],
                                        name,
                                        text_column,
                                        separator
                                    )
                                    st.success(f"Dataset '{name}' registered! ({result.get('row_count', 0)} rows)")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Registration failed: {str(e)}")
                    else:
                        st.warning("Could not read columns from this file.")
        else:
            st.success("All files in the datasets folder are registered!")

        if registered_files:
            st.markdown("---")
            st.markdown(f"**Already registered:** {', '.join(f['filename'] for f in registered_files)}")

with tab2:
    st.subheader("Registered Datasets")

    # Refresh button
    if st.button("Refresh", key="refresh_registered"):
        st.rerun()

    try:
        datasets = list_datasets()
    except Exception as e:
        st.error(f"Failed to load datasets: {str(e)}")
        datasets = []

    if not datasets:
        st.info("No datasets registered yet. Go to 'Available Files' tab to register datasets.")
    else:
        for dataset in datasets:
            with st.expander(f"📁 {dataset['name']} ({dataset['row_count']} rows)"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**File:** {dataset['filename']}")
                    st.write(f"**Text Column:** {dataset['text_column']}")
                    st.write(f"**Separator:** `{dataset['separator']}`")
                    st.write(f"**Size:** {dataset.get('file_size_bytes', 0) / 1024:.1f} KB")
                    st.write(f"**Created:** {dataset['created_at']}")

                with col2:
                    # Preview button
                    if st.button("Preview", key=f"preview_{dataset['id']}"):
                        try:
                            preview = preview_dataset(dataset['id'], rows=10)
                            st.write("**Sample Data:**")
                            preview_df = pd.DataFrame(preview['sample_rows'])
                            st.dataframe(preview_df, use_container_width=True, hide_index=True)
                        except Exception as e:
                            st.error(f"Failed to preview: {str(e)}")

                    # Unregister button
                    if st.button("Unregister", key=f"delete_{dataset['id']}", type="secondary"):
                        if st.session_state.get(f'confirm_delete_{dataset["id"]}'):
                            try:
                                delete_dataset(dataset['id'])
                                st.success(f"Dataset '{dataset['name']}' unregistered!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {str(e)}")
                        else:
                            st.session_state[f'confirm_delete_{dataset["id"]}'] = True
                            st.warning("Click again to confirm")

                # Show columns
                try:
                    columns = get_dataset_columns(dataset['id'])
                    st.write("**Columns:**")
                    st.code(", ".join(columns))
                except Exception:
                    pass

        # Summary
        st.markdown("---")
        total_rows = sum(d.get('row_count', 0) for d in datasets)
        total_size = sum(d.get('file_size_bytes', 0) for d in datasets) / 1024 / 1024

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Datasets", len(datasets))
        with col2:
            st.metric("Total Rows", f"{total_rows:,}")
        with col3:
            st.metric("Total Size", f"{total_size:.2f} MB")
