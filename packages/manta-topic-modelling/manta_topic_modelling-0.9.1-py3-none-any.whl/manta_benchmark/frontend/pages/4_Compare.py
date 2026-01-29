"""Compare page for comparing multiple benchmark results."""

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
    list_comparisons, create_comparison, get_comparison,
    delete_comparison, export_comparison
)

st.set_page_config(page_title="Compare - MANTA Benchmark", layout="wide")

st.title("Compare Benchmarks")

# Check API health
if not check_api_health():
    st.error("API is not available. Please start the backend server first.")
    st.stop()

# Tabs for different views
tab1, tab2 = st.tabs(["Quick Compare", "Saved Comparisons"])

with tab1:
    st.subheader("Quick Comparison")

    # Load benchmarks
    try:
        benchmarks = list_benchmarks()
    except Exception as e:
        st.error(f"Failed to load benchmarks: {str(e)}")
        benchmarks = []

    if len(benchmarks) < 2:
        st.warning("Need at least 2 benchmarks to compare. Create more benchmarks first.")
        st.stop()

    # Multi-select benchmarks
    benchmark_options = {f"{b['name']} (ID: {b['id']})": b['id'] for b in benchmarks}

    selected_labels = st.multiselect(
        "Select benchmarks to compare",
        options=list(benchmark_options.keys()),
        default=list(benchmark_options.keys())[:2] if len(benchmark_options) >= 2 else []
    )

    if len(selected_labels) < 2:
        st.info("Select at least 2 benchmarks to compare")
        st.stop()

    selected_ids = [benchmark_options[label] for label in selected_labels]

    # Load selected benchmarks
    selected_benchmarks = []
    for bid in selected_ids:
        try:
            b = get_benchmark(bid)
            if b.get('result'):
                selected_benchmarks.append(b)
        except Exception:
            pass

    if len(selected_benchmarks) < 2:
        st.warning("At least 2 selected benchmarks need completed results")
        st.stop()

    # Build comparison data
    comparison_data = []
    for b in selected_benchmarks:
        result = b['result']
        config = b['config']
        comparison_data.append({
            'Name': config['name'],
            'Dataset': b['dataset']['name'],
            'Topics': config['topic_count'],
            'Method': config['nmf_method'],
            'Runs': config['num_runs'],
            'Exec Time (s)': result.get('avg_execution_time'),
            'Time Std': result.get('std_execution_time'),
            'Memory (MB)': result.get('avg_peak_memory_mb'),
            'Memory Std': result.get('std_peak_memory_mb'),
            'Coherence': result.get('avg_coherence_cv'),
            'Coherence Std': result.get('std_coherence_cv'),
            'Diversity PUW': result.get('avg_diversity_puw'),
        })

    df = pd.DataFrame(comparison_data)

    # Display comparison table
    st.subheader("Comparison Table")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Comparison charts
    st.subheader("Visual Comparison")

    col1, col2 = st.columns(2)

    with col1:
        # Execution time comparison
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Name'],
            y=df['Exec Time (s)'],
            error_y=dict(type='data', array=df['Time Std']),
            name='Execution Time',
            marker_color='steelblue'
        ))
        fig.update_layout(
            title='Execution Time Comparison',
            xaxis_title='Benchmark',
            yaxis_title='Time (seconds)',
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Memory comparison
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Name'],
            y=df['Memory (MB)'],
            error_y=dict(type='data', array=df['Memory Std']),
            name='Memory',
            marker_color='coral'
        ))
        fig.update_layout(
            title='Peak Memory Comparison',
            xaxis_title='Benchmark',
            yaxis_title='Memory (MB)',
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Coherence comparison
        if df['Coherence'].notna().any():
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['Name'],
                y=df['Coherence'],
                error_y=dict(type='data', array=df['Coherence Std']),
                name='Coherence',
                marker_color='seagreen'
            ))
            fig.update_layout(
                title='Coherence Score Comparison',
                xaxis_title='Benchmark',
                yaxis_title='Coherence (C_v)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Diversity comparison
        if df['Diversity PUW'].notna().any():
            fig = px.bar(
                df,
                x='Name',
                y='Diversity PUW',
                title='Diversity Score Comparison',
                color='Diversity PUW',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # Radar chart for normalized comparison
    st.subheader("Normalized Performance Radar")

    # Normalize metrics to 0-1 scale
    metrics = ['Exec Time (s)', 'Memory (MB)', 'Coherence']
    radar_df = df[['Name'] + metrics].copy()

    for col in metrics:
        if radar_df[col].notna().any():
            min_val = radar_df[col].min()
            max_val = radar_df[col].max()
            if max_val > min_val:
                # For time and memory, lower is better (invert)
                if col in ['Exec Time (s)', 'Memory (MB)']:
                    radar_df[col] = 1 - (radar_df[col] - min_val) / (max_val - min_val)
                else:
                    radar_df[col] = (radar_df[col] - min_val) / (max_val - min_val)

    fig = go.Figure()

    for i, row in radar_df.iterrows():
        values = [row[m] if pd.notna(row[m]) else 0 for m in metrics]
        values.append(values[0])  # Close the polygon

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics + [metrics[0]],
            fill='toself',
            name=row['Name'],
            opacity=0.6
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title='Normalized Performance (higher is better)'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Save comparison
    st.markdown("---")
    st.subheader("Save Comparison")

    with st.form("save_comparison"):
        comp_name = st.text_input("Comparison Name", placeholder="e.g., NMF vs NMTF comparison")
        comp_desc = st.text_area("Description (optional)")

        if st.form_submit_button("Save Comparison"):
            if comp_name:
                try:
                    create_comparison(comp_name, comp_desc, selected_ids)
                    st.success(f"Comparison '{comp_name}' saved!")
                except Exception as e:
                    st.error(f"Failed to save: {str(e)}")
            else:
                st.error("Please enter a name")

with tab2:
    st.subheader("Saved Comparisons")

    try:
        comparisons = list_comparisons()
    except Exception as e:
        st.error(f"Failed to load comparisons: {str(e)}")
        comparisons = []

    if not comparisons:
        st.info("No saved comparisons yet. Create one in the Quick Compare tab.")
    else:
        for comp in comparisons:
            with st.expander(f"{comp['name']} (ID: {comp['id']})"):
                if comp.get('description'):
                    st.markdown(f"*{comp['description']}*")

                st.markdown(f"Created: {comp['created_at']}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("View Details", key=f"view_{comp['id']}"):
                        try:
                            comp_data = get_comparison(comp['id'])
                            st.write("**Configs:**")
                            for c in comp_data['configs']:
                                st.write(f"- {c['name']}")
                        except Exception as e:
                            st.error(f"Failed to load: {str(e)}")

                with col2:
                    if st.button("Export CSV", key=f"export_{comp['id']}"):
                        try:
                            csv_data = export_comparison(comp['id'], format="csv")
                            st.download_button(
                                "Download CSV",
                                csv_data,
                                file_name=f"comparison_{comp['id']}.csv",
                                mime="text/csv",
                                key=f"download_{comp['id']}"
                            )
                        except Exception as e:
                            st.error(f"Failed to export: {str(e)}")

                with col3:
                    if st.button("Delete", key=f"delete_{comp['id']}", type="secondary"):
                        try:
                            delete_comparison(comp['id'])
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {str(e)}")
