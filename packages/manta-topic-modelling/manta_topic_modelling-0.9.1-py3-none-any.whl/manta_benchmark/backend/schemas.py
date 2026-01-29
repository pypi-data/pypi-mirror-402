"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============== Dataset Schemas ==============

class DatasetCreate(BaseModel):
    """Schema for creating a new dataset."""
    name: str = Field(..., min_length=1, max_length=255)
    text_column: str = Field(..., min_length=1, max_length=100)
    separator: str = Field(default=",", max_length=10)


class DatasetResponse(BaseModel):
    """Schema for dataset response."""
    id: int
    name: str
    filename: str
    filepath: str
    text_column: str
    separator: str
    row_count: Optional[int]
    file_size_bytes: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetPreview(BaseModel):
    """Schema for dataset preview."""
    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    total_rows: int


# ============== Benchmark Config Schemas ==============

class BenchmarkConfigCreate(BaseModel):
    """Schema for creating a benchmark configuration."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_id: int

    # Analysis parameters
    language: str = Field(default="EN", pattern="^(EN|TR)$")
    topic_count: int = Field(default=5, ge=1, le=100)
    nmf_method: str = Field(default="nmf", pattern="^(nmf|nmtf|pnmf)$")
    tokenizer_type: str = Field(default="bpe", pattern="^(bpe|wordpiece)$")
    lemmatize: bool = False
    words_per_topic: int = Field(default=15, ge=5, le=50)
    n_grams_to_discover: Optional[int] = Field(default=None, ge=1)

    # Benchmark settings
    num_runs: int = Field(default=10, ge=1, le=50)


class BenchmarkConfigResponse(BaseModel):
    """Schema for benchmark configuration response."""
    id: int
    name: str
    description: Optional[str]
    dataset_id: int
    language: str
    topic_count: int
    nmf_method: str
    tokenizer_type: str
    lemmatize: bool
    words_per_topic: int
    n_grams_to_discover: Optional[int]
    num_runs: int
    created_at: datetime

    class Config:
        from_attributes = True


class BenchmarkConfigWithDataset(BenchmarkConfigResponse):
    """Benchmark config with dataset info."""
    dataset: DatasetResponse


# ============== Benchmark Run Schemas ==============

class BenchmarkRunResponse(BaseModel):
    """Schema for individual benchmark run."""
    id: int
    config_id: int
    run_number: int
    status: str
    execution_time_seconds: Optional[float]
    peak_memory_mb: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class BenchmarkMetricResponse(BaseModel):
    """Schema for benchmark metric."""
    metric_type: str
    metric_value: float
    metric_details: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class BenchmarkRunWithMetrics(BenchmarkRunResponse):
    """Run with detailed metrics."""
    metrics: List[BenchmarkMetricResponse]


# ============== Benchmark Result Schemas ==============

class BenchmarkResultResponse(BaseModel):
    """Schema for aggregated benchmark results."""
    id: int
    config_id: int

    # Execution metrics
    avg_execution_time: Optional[float]
    std_execution_time: Optional[float]
    avg_peak_memory_mb: Optional[float]
    std_peak_memory_mb: Optional[float]

    # Quality metrics
    avg_coherence_cv: Optional[float]
    std_coherence_cv: Optional[float]
    avg_diversity_puw: Optional[float]
    avg_diversity_jaccard: Optional[float]

    # Statistics
    total_runs: int
    successful_runs: int
    computed_at: datetime

    class Config:
        from_attributes = True


class BenchmarkFullResponse(BaseModel):
    """Full benchmark response with config, dataset, runs, and results."""
    config: BenchmarkConfigResponse
    dataset: DatasetResponse
    runs: List[BenchmarkRunResponse]
    result: Optional[BenchmarkResultResponse]
    status: str  # pending, running, completed, failed


# ============== Benchmark Execution Schemas ==============

class BenchmarkStatus(BaseModel):
    """Schema for benchmark execution status."""
    config_id: int
    status: str  # pending, running, completed, failed
    current_run: int
    total_runs: int
    progress_percent: float
    message: Optional[str]


class BenchmarkOutput(BaseModel):
    """Schema for real-time benchmark output streaming."""
    config_id: int
    lines: List[str]
    total_lines: int
    offset: int
    has_more: bool


class BenchmarkStartResponse(BaseModel):
    """Response when starting a benchmark."""
    config_id: int
    message: str
    status: str


# ============== Comparison Schemas ==============

class ComparisonGroupCreate(BaseModel):
    """Schema for creating a comparison group."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config_ids: List[int] = Field(..., min_length=2)


class ComparisonGroupResponse(BaseModel):
    """Schema for comparison group response."""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ComparisonData(BaseModel):
    """Schema for comparison data."""
    group: ComparisonGroupResponse
    configs: List[BenchmarkConfigWithDataset]
    results: List[Optional[BenchmarkResultResponse]]
    metrics_comparison: Dict[str, List[Optional[float]]]  # metric_name -> values per config


# ============== Utility Schemas ==============

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    error_code: Optional[str] = None
