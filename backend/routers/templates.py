"""
API routes for response template management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import ResponseTemplate
from schemas import ResponseTemplateCreate, ResponseTemplateResponse


router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=List[ResponseTemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only return active templates"),
):
    """
    Get response templates with optional filtering.
    """
    query = db.query(ResponseTemplate)
    
    if category:
        query = query.filter(ResponseTemplate.category == category)
    if active_only:
        query = query.filter(ResponseTemplate.is_active == True)
    
    templates = query.order_by(ResponseTemplate.name).all()
    
    return [ResponseTemplateResponse.model_validate(t) for t in templates]


@router.get("/categories")
def get_template_categories(db: Session = Depends(get_db)):
    """
    Get list of template categories.
    """
    categories = db.query(ResponseTemplate.category).distinct().all()
    return [c[0] for c in categories if c[0]]


@router.get("/{template_id}", response_model=ResponseTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """
    Get a single template by ID.
    """
    template = db.query(ResponseTemplate).filter(
        ResponseTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return ResponseTemplateResponse.model_validate(template)


@router.post("", response_model=ResponseTemplateResponse)
def create_template(
    template_data: ResponseTemplateCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new response template.
    """
    template = ResponseTemplate(**template_data.model_dump())
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return ResponseTemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=ResponseTemplateResponse)
def update_template(
    template_id: int,
    template_data: ResponseTemplateCreate,
    db: Session = Depends(get_db),
):
    """
    Update a response template.
    """
    template = db.query(ResponseTemplate).filter(
        ResponseTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template_data.model_dump().items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return ResponseTemplateResponse.model_validate(template)


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """
    Delete a response template.
    """
    template = db.query(ResponseTemplate).filter(
        ResponseTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    
    return {"message": "Template deleted", "template_id": template_id}


@router.post("/{template_id}/toggle")
def toggle_template(template_id: int, db: Session = Depends(get_db)):
    """
    Toggle a template's active status.
    """
    template = db.query(ResponseTemplate).filter(
        ResponseTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_active = not template.is_active
    db.commit()
    
    return {
        "message": f"Template {'activated' if template.is_active else 'deactivated'}",
        "template_id": template_id,
        "is_active": template.is_active,
    }


@router.post("/{template_id}/render")
def render_template(
    template_id: int,
    variables: dict,
    db: Session = Depends(get_db),
):
    """
    Render a template with the given variables.
    
    Variables should match the template's expected placeholders.
    Example: {"reviewer_name": "John", "facility_name": "Sage House"}
    """
    template = db.query(ResponseTemplate).filter(
        ResponseTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        rendered = template.template_text.format(**variables)
        return {
            "template_id": template_id,
            "rendered_text": rendered,
        }
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Missing variable: {e}"
        )
