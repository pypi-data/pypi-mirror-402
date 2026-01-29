"""Dataset management API endpoints."""

import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

# Datasets directory (folder to scan for datasets)
DATASETS_DIR = Path(__file__).parent.parent.parent / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/scan", response_model=List[Dict[str, Any]])
def scan_datasets_folder(db: Session = Depends(get_db)):
    """Scan the datasets folder and return available files."""
    # Get already registered filepaths
    registered = db.query(models.Dataset.filepath).all()
    registered_paths = {r[0] for r in registered}

    available_files = []
    for file_path in DATASETS_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
            abs_path = str(file_path.resolve())
            is_registered = abs_path in registered_paths

            # Get file info
            file_info = {
                'filename': file_path.name,
                'filepath': abs_path,
                'size_bytes': file_path.stat().st_size,
                'extension': file_path.suffix.lower(),
                'is_registered': is_registered
            }

            # Try to get columns
            try:
                if file_path.suffix.lower() == '.csv':
                    df = pd.read_csv(file_path, nrows=0)
                else:
                    df = pd.read_excel(file_path, nrows=0)
                file_info['columns'] = list(df.columns)
            except Exception:
                file_info['columns'] = []

            available_files.append(file_info)

    return sorted(available_files, key=lambda x: x['filename'])


@router.post("/register", response_model=schemas.DatasetResponse)
def register_dataset(
    filepath: str,
    name: str,
    text_column: str,
    separator: str = ",",
    db: Session = Depends(get_db)
):
    """Register a dataset from the datasets folder."""
    # Check for duplicate name
    existing = db.query(models.Dataset).filter(models.Dataset.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Dataset with name '{name}' already exists")

    # Check file exists
    file_path = Path(filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filepath}")

    # Validate file type
    file_ext = file_path.suffix.lower()
    if file_ext not in ['.csv', '.xlsx', '.xls']:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

    # Read file to get metadata
    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path, sep=separator, nrows=0)
            df_full = pd.read_csv(file_path, sep=separator)
        else:
            df = pd.read_excel(file_path, nrows=0)
            df_full = pd.read_excel(file_path)

        # Validate text column exists
        if text_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Column '{text_column}' not found. Available columns: {list(df.columns)}"
            )

        row_count = len(df_full)
        file_size = file_path.stat().st_size

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Create database record
    dataset = models.Dataset(
        name=name,
        filename=file_path.name,
        filepath=str(file_path.resolve()),
        text_column=text_column,
        separator=separator,
        row_count=row_count,
        file_size_bytes=file_size
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


@router.get("", response_model=List[schemas.DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    """List all datasets."""
    return db.query(models.Dataset).order_by(models.Dataset.created_at.desc()).all()


@router.get("/{dataset_id}", response_model=schemas.DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get a specific dataset."""
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.get("/{dataset_id}/columns", response_model=List[str])
def get_dataset_columns(dataset_id: int, db: Session = Depends(get_db)):
    """Get column names for a dataset."""
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        filepath = Path(dataset.filepath)
        if filepath.suffix.lower() == '.csv':
            df = pd.read_csv(filepath, sep=dataset.separator, nrows=0)
        else:
            df = pd.read_excel(filepath, nrows=0)
        return list(df.columns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.get("/{dataset_id}/preview", response_model=schemas.DatasetPreview)
def preview_dataset(dataset_id: int, rows: int = 10, db: Session = Depends(get_db)):
    """Preview first N rows of a dataset."""
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        filepath = Path(dataset.filepath)
        if filepath.suffix.lower() == '.csv':
            df = pd.read_csv(filepath, sep=dataset.separator, nrows=rows)
            total = dataset.row_count or 0
        else:
            df = pd.read_excel(filepath, nrows=rows)
            total = dataset.row_count or 0

        return schemas.DatasetPreview(
            columns=list(df.columns),
            sample_rows=df.to_dict(orient='records'),
            total_rows=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.delete("/{dataset_id}", response_model=schemas.MessageResponse)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Unregister a dataset (does not delete the file)."""
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Check if dataset is used by any benchmark
    benchmarks = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.dataset_id == dataset_id
    ).count()
    if benchmarks > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete dataset: {benchmarks} benchmark(s) depend on it"
        )

    # Delete database record only (don't delete file since it's in the datasets folder)
    db.delete(dataset)
    db.commit()

    return schemas.MessageResponse(message=f"Dataset '{dataset.name}' unregistered successfully")
