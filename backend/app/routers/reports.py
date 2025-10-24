from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from .. import models, schemas, auth
from ..database import get_db
from ..llm_service import LLMService

router = APIRouter()

@router.get("/customer/{customer_id}/dimensions")
def get_dimension_reports(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get list of dimensions for reports. (CXO/Sales only)
    CXO can only view their own customer's reports.
    Sales can view any customer's reports.
    """
    # Check permissions
    if current_user.user_type == models.UserType.PARTICIPANT:
        raise HTTPException(
            status_code=403, 
            detail="Participants cannot view reports"
        )
    
    if current_user.user_type in [models.UserType.CXO] and current_user.customer_id != customer_id:
        raise HTTPException(
            status_code=403, 
            detail="Can only view your own customer's reports"
        )
    
    # Get survey
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == customer_id
    ).first()
    
    if not survey:
        return {"message": "No survey data available"}
    
    # Get all dimensions
    dimensions = db.query(models.Question.dimension).distinct().all()
    return [{"dimension": d[0]} for d in dimensions]

@router.get("/customer/{customer_id}/dimension/{dimension}")
async def get_dimension_report(
    customer_id: int,
    dimension: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.user_type == models.UserType.PARTICIPANT:
        raise HTTPException(status_code=403, detail="Participants cannot view reports")
    
    if current_user.user_type in [models.UserType.CXO] and current_user.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Can only view your own customer's reports")
    
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == customer_id
    ).first()
    
    if not survey:
        return {"error": "No survey data available"}
    
    questions = db.query(models.Question).filter(
        models.Question.dimension == dimension
    ).all()
    
    total_users = db.query(models.User).filter(
        models.User.customer_id == customer_id,
        models.User.user_type.in_([models.UserType.CXO, models.UserType.PARTICIPANT]),
        models.User.is_deleted == False
    ).count()
    
    report_data = []
    questions_for_llm = []
    
    for question in questions:
        responses = db.query(models.SurveyResponse).filter(
            models.SurveyResponse.survey_id == survey.id,
            models.SurveyResponse.question_id == question.id,
            models.SurveyResponse.score.isnot(None)
        ).all()
        
        responded_count = len(set(r.user_id for r in responses))
        
        numeric_scores = [float(r.score) for r in responses if r.score and r.score != 'NA']
        comments = [r.comment for r in responses if r.comment]
        
        min_score = min(numeric_scores) if numeric_scores else None
        max_score = max(numeric_scores) if numeric_scores else None
        avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else None
        
        report_data.append({
            "question": question.text,
            "responded": f"{responded_count}/{total_users}",
            "min_score": min_score,
            "max_score": max_score,
            "avg_score": round(avg_score, 2) if avg_score else None
        })
        
        questions_for_llm.append({
            "text": question.text,
            "avg_score": round(avg_score, 2) if avg_score else "N/A",
            "comments": comments
        })
    
    llm_summary = None
    llm_error = None
    
    try:
        llm_config = db.query(models.LLMConfig).filter(
            models.LLMConfig.purpose == dimension
        ).first()
        
        if not llm_config:
            llm_config = db.query(models.LLMConfig).filter(
                models.LLMConfig.purpose == "Default"
            ).first()
        
        if llm_config and llm_config.status == "Success":
            llm_summary = await LLMService.generate_dimension_summary(
                llm_config.api_url,
                llm_config.api_key,
                dimension,
                questions_for_llm,
                llm_config.model_name  # PASS MODEL NAME
            )
    except Exception as e:
        llm_error = str(e)
    
    return {
        "dimension": dimension,
        "questions": report_data,
        "llm_summary": llm_summary,
        "llm_error": llm_error
    }

@router.get("/customer/{customer_id}/overall")
async def get_overall_report(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get overall report aggregating all dimensions. (CXO/Sales only)
    Uses Orchestrate LLM for cross-dimension analysis.
    PLACEHOLDER - Full implementation in next iteration.
    """
    # Check permissions
    if current_user.user_type == models.UserType.PARTICIPANT:
        raise HTTPException(
            status_code=403, 
            detail="Participants cannot view reports"
        )
    
    if current_user.user_type in [models.UserType.CXO] and current_user.customer_id != customer_id:
        raise HTTPException(
            status_code=403, 
            detail="Can only view your own customer's reports"
        )
    
    return {
        "message": "Overall report - Placeholder",
        "note": "This will aggregate all dimension reports and use the Orchestrate LLM for comprehensive analysis. Full implementation coming in next iteration."
    }