"""Main Streamlit application for MANTA Benchmarking UI."""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="MANTA Benchmark",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (minimal - let Streamlit handle theming)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main page content
st.markdown('<p class="main-header">MANTA Benchmark Dashboard</p>', unsafe_allow_html=True)

st.markdown("""
Welcome to the MANTA Benchmarking Framework. This tool allows you to:

- **Upload datasets** for topic modeling analysis
- **Configure and run benchmarks** with different parameters
- **Track metrics** including execution time, memory usage, and coherence scores
- **Compare results** across multiple benchmark configurations

### Getting Started

1. Navigate to **Datasets** to upload your data
2. Go to **New Benchmark** to configure and start an analysis
3. View results in the **Results** page
4. Compare multiple benchmarks in the **Compare** page

---

### Quick Navigation
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📁 Datasets", use_container_width=True):
        st.switch_page("pages/5_Datasets.py")

with col2:
    if st.button("🆕 New Benchmark", use_container_width=True):
        st.switch_page("pages/2_New_Benchmark.py")

with col3:
    if st.button("📊 Results", use_container_width=True):
        st.switch_page("pages/3_Results.py")

with col4:
    if st.button("🔄 Compare", use_container_width=True):
        st.switch_page("pages/4_Compare.py")

# Show API status
st.markdown("---")
st.subheader("System Status")

from utils.api_client import check_api_health, get_api_stats

health = check_api_health()
stats = get_api_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("API Status", "Online" if health else "Offline")

with col2:
    st.metric("Datasets", stats.get('datasets', 0))

with col3:
    st.metric("Benchmarks", stats.get('benchmarks', 0))

with col4:
    st.metric("Comparisons", stats.get('comparisons', 0))
