"""Comparison API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/comparisons", tags=["comparisons"])


@router.post("", response_model=schemas.ComparisonGroupResponse)
def create_comparison_group(
    data: schemas.ComparisonGroupCreate,
    db: Session = Depends(get_db)
):
    """Create a new comparison group."""
    # Validate all config IDs exist
    for config_id in data.config_ids:
        config = db.query(models.BenchmarkConfig).filter(
            models.BenchmarkConfig.id == config_id
        ).first()
        if not config:
            raise HTTPException(status_code=404, detail=f"Benchmark config {config_id} not found")

    # Create group
    group = models.ComparisonGroup(
        name=data.name,
        description=data.description
    )
    db.add(group)
    db.flush()

    # Add members
    for config_id in data.config_ids:
        member = models.ComparisonMember(
            group_id=group.id,
            config_id=config_id
        )
        db.add(member)

    db.commit()
    db.refresh(group)

    return group


@router.get("", response_model=List[schemas.ComparisonGroupResponse])
def list_comparison_groups(db: Session = Depends(get_db)):
    """List all comparison groups."""
    return db.query(models.ComparisonGroup).order_by(
        models.ComparisonGroup.created_at.desc()
    ).all()


@router.get("/{group_id}", response_model=schemas.ComparisonData)
def get_comparison(group_id: int, db: Session = Depends(get_db)):
    """Get comparison data for a group."""
    group = db.query(models.ComparisonGroup).filter(
        models.ComparisonGroup.id == group_id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Comparison group not found")

    # Get all configs and their results
    configs = []
    results = []
    for member in group.members:
        config = member.config
        configs.append(schemas.BenchmarkConfigWithDataset(
            id=config.id,
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
            num_runs=config.num_runs,
            created_at=config.created_at,
            dataset=config.dataset
        ))
        results.append(config.result)

    # Build metrics comparison dict
    metrics_comparison = {
        'execution_time': [],
        'peak_memory': [],
        'coherence_cv': [],
        'diversity_puw': [],
        'diversity_jaccard': []
    }

    for result in results:
        if result:
            metrics_comparison['execution_time'].append(result.avg_execution_time)
            metrics_comparison['peak_memory'].append(result.avg_peak_memory_mb)
            metrics_comparison['coherence_cv'].append(result.avg_coherence_cv)
            metrics_comparison['diversity_puw'].append(result.avg_diversity_puw)
            metrics_comparison['diversity_jaccard'].append(result.avg_diversity_jaccard)
        else:
            metrics_comparison['execution_time'].append(None)
            metrics_comparison['peak_memory'].append(None)
            metrics_comparison['coherence_cv'].append(None)
            metrics_comparison['diversity_puw'].append(None)
            metrics_comparison['diversity_jaccard'].append(None)

    return schemas.ComparisonData(
        group=group,
        configs=configs,
        results=results,
        metrics_comparison=metrics_comparison
    )


@router.post("/{group_id}/add/{config_id}", response_model=schemas.MessageResponse)
def add_to_comparison(group_id: int, config_id: int, db: Session = Depends(get_db)):
    """Add a benchmark config to a comparison group."""
    group = db.query(models.ComparisonGroup).filter(
        models.ComparisonGroup.id == group_id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Comparison group not found")

    config = db.query(models.BenchmarkConfig).filter(
        models.BenchmarkConfig.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Benchmark config not found")

    # Check if already in group
    existing = db.query(models.ComparisonMember).filter(
        models.ComparisonMember.group_id == group_id,
        models.ComparisonMember.config_id == config_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Config already in comparison group")

    member = models.ComparisonMember(
        group_id=group_id,
        config_id=config_id
    )
    db.add(member)
    db.commit()

    return schemas.MessageResponse(message=f"Added '{config.name}' to comparison group")


@router.delete("/{group_id}", response_model=schemas.MessageResponse)
def delete_comparison_group(group_id: int, db: Session = Depends(get_db)):
    """Delete a comparison group."""
    group = db.query(models.ComparisonGroup).filter(
        models.ComparisonGroup.id == group_id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Comparison group not found")

    db.delete(group)
    db.commit()

    return schemas.MessageResponse(message=f"Comparison group '{group.name}' deleted")


@router.get("/{group_id}/export")
def export_comparison(group_id: int, format: str = "json", db: Session = Depends(get_db)):
    """Export comparison data as JSON or CSV."""
    group = db.query(models.ComparisonGroup).filter(
        models.ComparisonGroup.id == group_id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Comparison group not found")

    # Build export data
    export_data = []
    for member in group.members:
        config = member.config
        result = config.result

        row = {
            'name': config.name,
            'dataset': config.dataset.name,
            'language': config.language,
            'topic_count': config.topic_count,
            'nmf_method': config.nmf_method,
            'num_runs': config.num_runs,
        }

        if result:
            row.update({
                'avg_execution_time': result.avg_execution_time,
                'std_execution_time': result.std_execution_time,
                'avg_peak_memory_mb': result.avg_peak_memory_mb,
                'std_peak_memory_mb': result.std_peak_memory_mb,
                'avg_coherence_cv': result.avg_coherence_cv,
                'std_coherence_cv': result.std_coherence_cv,
                'avg_diversity_puw': result.avg_diversity_puw,
                'successful_runs': result.successful_runs,
            })

        export_data.append(row)

    if format == "csv":
        import csv
        import io
        from fastapi.responses import StreamingResponse

        output = io.StringIO()
        if export_data:
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=comparison_{group_id}.csv"}
        )

    return {
        'group_name': group.name,
        'group_description': group.description,
        'data': export_data
    }
