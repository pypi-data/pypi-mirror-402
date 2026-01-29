"""Benchmark management API endpoints."""

import threading
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..benchmark_runner import (
    run_benchmark_suite,
    get_benchmark_status,
    set_benchmark_status,
    clear_benchmark_status,
    get_benchmark_output,
    stop_benchmark
)

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.post("", response_model=schemas.BenchmarkConfigResponse)
def create_benchmark(
    config: schemas.BenchmarkConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new benchmark configuration."""
    # Validate dataset exists
    dataset = db.query(models.Dataset).filter(models.Dataset.id == config.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Create config
    benchmark_config = models.BenchmarkConfig(
        name=config.name,
        description=config.description,
        dataset_id=config.dataset_id,
        language=config.language,
        topic_count=config.topic_count,
        nmf_method=config.nmf_method,
        tokenizer_type=config.tokenizer_type,
        lemmatize=config.lemmatize,
        words_per_topic=config.words_per_topic,
        n_grams_to_discover=config.n_grams_to_discover,
        num_runs=config.num_runs
    )
    db.add(benchmark_config)
    db.commit()
    db.refresh(benchmark_config)

    return benchmark_config


@router.get("", response_model=List[schemas.BenchmarkConfigResponse])
def list_benchmarks(db: Session = Depends(get_db)):
    """List all benchmark configurations."""
    return db.query(models.BenchmarkConfig).order_by(
        models.BenchmarkConfig.created_at.desc()
    ).all()


@router.get("/{config_id}", response_model=schemas.BenchmarkFullResponse)
def get_benchmark(config_id: int, db: Session = Depends(get_db)):
    """Get a specific benchmark with all details."""
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    # Determine status
    running_status = get_benchmark_status(config_id)
    if running_status:
        status = "running"
    elif config.result and config.result.successful_runs > 0:
        status = "completed"
    elif config.runs and any(r.status == "failed" for r in config.runs):
        status = "failed"
    else:
        status = "pending"

    return schemas.BenchmarkFullResponse(
        config=config,
        dataset=config.dataset,
        runs=config.runs,
        result=config.result,
        status=status
    )


@router.delete("/{config_id}", response_model=schemas.MessageResponse)
def delete_benchmark(config_id: int, db: Session = Depends(get_db)):
    """Delete a benchmark configuration and all its runs."""
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    # Check if benchmark is running
    if get_benchmark_status(config_id):
        raise HTTPException(status_code=400, detail="Cannot delete running benchmark")

    db.delete(config)
    db.commit()

    return schemas.MessageResponse(message=f"Benchmark '{config.name}' deleted successfully")


def _run_benchmark_thread(config_id: int, db_url: str):
    """Run benchmark in a separate thread."""
    from ..database import SessionLocal
    import traceback
    import time as time_module

    db = SessionLocal()
    had_error = False
    try:
        def progress_callback(current: int, total: int, message: str):
            set_benchmark_status(config_id, {
                'current_run': current,
                'total_runs': total,
                'message': message,
                'progress_percent': (current / total) * 100
            })

        run_benchmark_suite(db, config_id, progress_callback)
    except Exception as e:
        had_error = True
        error_msg = str(e)
        tb = traceback.format_exc()

        # Log error to output buffer so user can see it
        status = get_benchmark_status(config_id)
        if status and 'output_buffer' in status:
            status['output_buffer'].append("\n" + "=" * 60)
            status['output_buffer'].append("  BENCHMARK FAILED WITH ERROR")
            status['output_buffer'].append("=" * 60)
            status['output_buffer'].append(f"\nError: {error_msg}")
            status['output_buffer'].append(f"\nTraceback:\n{tb}")

        # Print to console for debugging
        print(f"Benchmark {config_id} failed with error: {error_msg}")
        print(tb)

        # Keep the error visible for a moment before clearing
        time_module.sleep(2)
    finally:
        clear_benchmark_status(config_id)
        db.close()


@router.post("/{config_id}/run", response_model=schemas.BenchmarkStartResponse)
def start_benchmark(
    config_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start running a benchmark."""
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    # Check if already running
    if get_benchmark_status(config_id):
        raise HTTPException(status_code=400, detail="Benchmark is already running")

    # Clear previous runs if any
    db.query(models.BenchmarkRun).filter(
        models.BenchmarkRun.config_id == config_id
    ).delete()
    db.query(models.BenchmarkResult).filter(
        models.BenchmarkResult.config_id == config_id
    ).delete()
    db.commit()

    # Initialize status
    set_benchmark_status(config_id, {
        'current_run': 0,
        'total_runs': config.num_runs,
        'message': 'Starting benchmark...',
        'progress_percent': 0
    })

    # Start benchmark in background thread
    from ..database import DATABASE_URL
    thread = threading.Thread(
        target=_run_benchmark_thread,
        args=(config_id, DATABASE_URL),
        daemon=True
    )
    thread.start()

    return schemas.BenchmarkStartResponse(
        config_id=config_id,
        message=f"Benchmark started with {config.num_runs} runs",
        status="running"
    )


@router.post("/{config_id}/stop", response_model=schemas.MessageResponse)
def stop_benchmark_endpoint(config_id: int, db: Session = Depends(get_db)):
    """Stop a running benchmark.

    This will terminate the current analysis process and stop all remaining runs.
    """
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    # Check if benchmark is running
    running_status = get_benchmark_status(config_id)
    if not running_status:
        raise HTTPException(status_code=400, detail="Benchmark is not running")

    # Request stop
    if stop_benchmark(config_id):
        return schemas.MessageResponse(
            message=f"Stop requested for benchmark '{config.name}'",
            success=True
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to stop benchmark")


@router.get("/{config_id}/status", response_model=schemas.BenchmarkStatus)
def get_status(config_id: int, db: Session = Depends(get_db)):
    """Get the status of a benchmark execution."""
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    running_status = get_benchmark_status(config_id)

    if running_status:
        return schemas.BenchmarkStatus(
            config_id=config_id,
            status="running",
            current_run=running_status['current_run'],
            total_runs=running_status['total_runs'],
            progress_percent=running_status['progress_percent'],
            message=running_status['message']
        )

    # Refresh to ensure we have latest data from the benchmark thread
    db.refresh(config)

    # Check if benchmark has completed (result exists)
    if config.result:
        if config.result.successful_runs > 0:
            return schemas.BenchmarkStatus(
                config_id=config_id,
                status="completed",
                current_run=config.result.total_runs,
                total_runs=config.result.total_runs,
                progress_percent=100,
                message=f"Completed with {config.result.successful_runs}/{config.result.total_runs} successful runs"
            )
        else:
            # Result exists but no successful runs = all failed
            return schemas.BenchmarkStatus(
                config_id=config_id,
                status="failed",
                current_run=config.result.total_runs,
                total_runs=config.result.total_runs,
                progress_percent=100,
                message=f"All {config.result.total_runs} runs failed"
            )

    # Check if any runs exist and have failed (fallback)
    if config.runs:
        completed_runs = [r for r in config.runs if r.status in ("completed", "failed")]
        if completed_runs:
            failed_count = sum(1 for r in config.runs if r.status == "failed")
            if all(r.status == "failed" for r in completed_runs):
                return schemas.BenchmarkStatus(
                    config_id=config_id,
                    status="failed",
                    current_run=len(completed_runs),
                    total_runs=config.num_runs,
                    progress_percent=100,
                    message=f"All {failed_count} runs failed"
                )

    return schemas.BenchmarkStatus(
        config_id=config_id,
        status="pending",
        current_run=0,
        total_runs=config.num_runs,
        progress_percent=0,
        message="Not started"
    )


@router.get("/{config_id}/output", response_model=schemas.BenchmarkOutput)
def get_output(
    config_id: int,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get real-time output from a running benchmark.

    Args:
        config_id: Benchmark configuration ID
        offset: Line offset to fetch from (for incremental updates)

    Returns:
        BenchmarkOutput with lines since offset
    """
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    output = get_benchmark_output(config_id, offset)

    if output is None:
        # No output buffer - benchmark not running or no output yet
        return schemas.BenchmarkOutput(
            config_id=config_id,
            lines=[],
            total_lines=0,
            offset=0,
            has_more=False
        )

    return schemas.BenchmarkOutput(
        config_id=config_id,
        lines=output['lines'],
        total_lines=output['total_lines'],
        offset=output['offset'],
        has_more=len(output['lines']) > 0
    )


@router.get("/{config_id}/results", response_model=Optional[schemas.BenchmarkResultResponse])
def get_results(config_id: int, db: Session = Depends(get_db)):
    """Get the results of a completed benchmark."""
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    return config.result


@router.get("/{config_id}/runs", response_model=List[schemas.BenchmarkRunWithMetrics])
def get_runs(config_id: int, db: Session = Depends(get_db)):
    """Get all runs for a benchmark with their metrics."""
    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    runs = db.query(models.BenchmarkRun).filter(
        models.BenchmarkRun.config_id == config_id
    ).order_by(models.BenchmarkRun.run_number).all()

    return [
        schemas.BenchmarkRunWithMetrics(
            id=run.id,
            config_id=run.config_id,
            run_number=run.run_number,
            status=run.status,
            execution_time_seconds=run.execution_time_seconds,
            peak_memory_mb=run.peak_memory_mb,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_message=run.error_message,
            metrics=[
                schemas.BenchmarkMetricResponse(
                    metric_type=m.metric_type,
                    metric_value=m.metric_value,
                    metric_details=m.metric_details
                )
                for m in run.metrics
            ]
        )
        for run in runs
    ]
