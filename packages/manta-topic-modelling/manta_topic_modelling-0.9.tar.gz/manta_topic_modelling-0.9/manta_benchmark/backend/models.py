"""SQLAlchemy ORM models for MANTA Benchmarking."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from .database import Base


class Dataset(Base):
    """Uploaded dataset metadata."""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(Text, nullable=False)
    text_column = Column(String(100), nullable=False)
    separator = Column(String(10), default=",")
    row_count = Column(Integer)
    file_size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    benchmark_configs = relationship("BenchmarkConfig", back_populates="dataset")


class BenchmarkConfig(Base):
    """Benchmark configuration settings."""
    __tablename__ = "benchmark_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    # Analysis parameters
    language = Column(String(10), nullable=False, default="EN")
    topic_count = Column(Integer, nullable=False, default=5)
    nmf_method = Column(String(20), nullable=False, default="nmf")
    tokenizer_type = Column(String(20), default="bpe")
    lemmatize = Column(Boolean, default=False)
    words_per_topic = Column(Integer, default=15)
    n_grams_to_discover = Column(Integer, nullable=True)

    # Benchmark settings
    num_runs = Column(Integer, default=10)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="benchmark_configs")
    runs = relationship("BenchmarkRun", back_populates="config", cascade="all, delete-orphan")
    result = relationship("BenchmarkResult", back_populates="config", uselist=False, cascade="all, delete-orphan")


class BenchmarkRun(Base):
    """Individual benchmark run results."""
    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("benchmark_configs.id"), nullable=False)
    run_number = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed

    # Metrics
    execution_time_seconds = Column(Float)
    peak_memory_mb = Column(Float)

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    # Relationships
    config = relationship("BenchmarkConfig", back_populates="runs")
    metrics = relationship("BenchmarkMetric", back_populates="run", cascade="all, delete-orphan")


class BenchmarkMetric(Base):
    """Detailed metrics per run."""
    __tablename__ = "benchmark_metrics"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("benchmark_runs.id"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # coherence_cv, diversity_puw, etc.
    metric_value = Column(Float, nullable=False)
    metric_details = Column(JSON)  # Additional details (per-topic scores, etc.)

    # Relationships
    run = relationship("BenchmarkRun", back_populates="metrics")


class BenchmarkResult(Base):
    """Aggregated benchmark results across all runs."""
    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("benchmark_configs.id"), nullable=False, unique=True)

    # Aggregated execution metrics
    avg_execution_time = Column(Float)
    std_execution_time = Column(Float)
    avg_peak_memory_mb = Column(Float)
    std_peak_memory_mb = Column(Float)

    # Aggregated quality metrics
    avg_coherence_cv = Column(Float)
    std_coherence_cv = Column(Float)
    avg_diversity_puw = Column(Float)
    avg_diversity_jaccard = Column(Float)

    # Run statistics
    total_runs = Column(Integer)
    successful_runs = Column(Integer)

    computed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    config = relationship("BenchmarkConfig", back_populates="result")


class ComparisonGroup(Base):
    """Saved comparison groups."""
    __tablename__ = "comparison_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    members = relationship("ComparisonMember", back_populates="group", cascade="all, delete-orphan")


class ComparisonMember(Base):
    """Members of a comparison group."""
    __tablename__ = "comparison_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("comparison_groups.id"), nullable=False)
    config_id = Column(Integer, ForeignKey("benchmark_configs.id"), nullable=False)

    # Relationships
    group = relationship("ComparisonGroup", back_populates="members")
    config = relationship("BenchmarkConfig")
