from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter()

@router.get("/questions", response_model=List[schemas.Question])
def get_questions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_customer_user)
):
    """Get all survey questions. CXO users see only CXO questions, others see all. (Customer users only)"""
    query = db.query(models.Question)

    # CXO users only see CXO questions
    if current_user.user_type == models.UserType.CXO:
        query = query.filter(models.Question.question_type == 'CXO')

    questions = query.all()
    return questions

@router.get("/dimensions")
def get_dimensions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_customer_user)
):
    """Get list of all unique dimensions. (Customer users only)"""
    dimensions = db.query(models.Question.dimension).distinct().all()
    return [{"dimension": d[0]} for d in dimensions]

@router.get("/progress", response_model=List[schemas.DimensionProgress])
def get_survey_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_customer_user)
):
    """
    Get survey progress for the current user's customer.
    Shows progress per dimension. (Customer users only)
    """
    if not current_user.customer_id:
        raise HTTPException(
            status_code=400, 
            detail="User not associated with a customer"
        )
    
    # Get or create survey for this customer
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == current_user.customer_id
    ).first()
    
    if not survey:
        survey = models.Survey(customer_id=current_user.customer_id)
        db.add(survey)
        db.commit()
        db.refresh(survey)
    
    # Get all dimensions
    dimensions = db.query(models.Question.dimension).distinct().all()
    progress = []
    
    for (dimension,) in dimensions:
        # Count total questions in this dimension (filtered by user type)
        question_query = db.query(models.Question).filter(
            models.Question.dimension == dimension
        )
        # CXO users only see CXO questions
        if current_user.user_type == models.UserType.CXO:
            question_query = question_query.filter(models.Question.question_type == 'CXO')

        total_questions = question_query.count()

        # Count answered questions in this dimension for the CURRENT USER
        answer_query = db.query(models.SurveyResponse).join(
            models.Question
        ).filter(
            models.SurveyResponse.survey_id == survey.id,
            models.SurveyResponse.user_id == current_user.id,
            models.Question.dimension == dimension,
            models.SurveyResponse.score.isnot(None)
        )
        # CXO users only count CXO questions
        if current_user.user_type == models.UserType.CXO:
            answer_query = answer_query.filter(models.Question.question_type == 'CXO')

        answered_questions = answer_query.distinct(models.SurveyResponse.question_id).count()
        
        # Determine status
        if answered_questions == 0:
            status = "Not Started"
        elif answered_questions == total_questions:
            status = "Completed"
        else:
            status = f"In Progress {answered_questions}/{total_questions}"
        
        progress.append({
            "dimension": dimension,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "status": status
        })
    
    return progress

@router.get("/questions/{dimension}", response_model=List[schemas.Question])
def get_questions_by_dimension(
    dimension: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_customer_user)
):
    """Get all questions for a specific dimension. CXO users see only CXO questions, others see all. (Customer users only)"""
    query = db.query(models.Question).filter(
        models.Question.dimension == dimension
    )

    # CXO users only see CXO questions
    if current_user.user_type == models.UserType.CXO:
        query = query.filter(models.Question.question_type == 'CXO')

    questions = query.all()
    return questions

@router.get("/responses/{dimension}")
def get_user_responses_for_dimension(
    dimension: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_customer_user)
):
    """
    Get current user's responses for a specific dimension.
    Returns dict mapping question_id to {score, comment}. (Customer users only)
    """
    # Get survey for this customer
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == current_user.customer_id
    ).first()
    
    if not survey:
        return {}
    
    # Get all questions in this dimension (filtered by user type)
    question_query = db.query(models.Question).filter(
        models.Question.dimension == dimension
    )
    # CXO users only see CXO questions
    if current_user.user_type == models.UserType.CXO:
        question_query = question_query.filter(models.Question.question_type == 'CXO')

    questions = question_query.all()

    question_ids = [q.id for q in questions]
    
    # Get responses for this user
    responses = db.query(models.SurveyResponse).filter(
        models.SurveyResponse.survey_id == survey.id,
        models.SurveyResponse.user_id == current_user.id,
        models.SurveyResponse.question_id.in_(question_ids)
    ).all()
    
    # Format as dict
    return {
        r.question_id: {"score": r.score, "comment": r.comment} 
        for r in responses
    }

@router.post("/responses")
def save_response(
    response: schemas.SurveyResponseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_customer_user)
):
    """
    Save or update a survey response (auto-save). (Customer users only)
    Handles both score and comment updates.
    """
    if not current_user.customer_id:
        raise HTTPException(
            status_code=400, 
            detail="User not associated with a customer"
        )
    
    # Get or create survey
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == current_user.customer_id
    ).first()
    
    if not survey:
        survey = models.Survey(customer_id=current_user.customer_id)
        db.add(survey)
        db.commit()
        db.refresh(survey)
    
    # Check if current user has already submitted
    user_submission = db.query(models.UserSurveySubmission).filter(
        models.UserSurveySubmission.survey_id == survey.id,
        models.UserSurveySubmission.user_id == current_user.id
    ).first()

    if user_submission:
        raise HTTPException(
            status_code=400,
            detail="You have already submitted this survey. Cannot modify responses."
        )
    
    # Verify question exists
    question = db.query(models.Question).filter(
        models.Question.id == response.question_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if response already exists
    existing = db.query(models.SurveyResponse).filter(
        models.SurveyResponse.survey_id == survey.id,
        models.SurveyResponse.user_id == current_user.id,
        models.SurveyResponse.question_id == response.question_id
    ).first()
    
    if existing:
        # Update existing response
        if response.score is not None:
            existing.score = response.score
        if response.comment is not None:
            existing.comment = response.comment[:200].strip()
        db.commit()
        db.refresh(existing)
        return {"message": "Response updated", "response": existing}
    else:
        # Create new response
        comment = response.comment[:200].strip() if response.comment else None
        db_response = models.SurveyResponse(
            survey_id=survey.id,
            user_id=current_user.id,
            question_id=response.question_id,
            score=response.score,
            comment=comment
        )
        db.add(db_response)
        db.commit()
        db.refresh(db_response)
        return {"message": "Response saved", "response": db_response}

@router.post("/submit")
def submit_survey(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_customer_user)
):
    """
    Submit the survey. (Customer users only)
    Validates that all questions are answered.
    Once submitted, survey cannot be edited.
    """
    if not current_user.customer_id:
        raise HTTPException(
            status_code=400, 
            detail="User not associated with a customer"
        )
    
    # Get survey
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == current_user.customer_id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=400, detail="No survey found")

    # Check if current user has already submitted
    user_submission = db.query(models.UserSurveySubmission).filter(
        models.UserSurveySubmission.survey_id == survey.id,
        models.UserSurveySubmission.user_id == current_user.id
    ).first()

    if user_submission:
        raise HTTPException(
            status_code=400,
            detail="You have already submitted this survey"
        )
    
    # Validate all relevant questions are answered (filtered by user type)
    question_query = db.query(models.Question)
    # CXO users only need to answer CXO questions
    if current_user.user_type == models.UserType.CXO:
        question_query = question_query.filter(models.Question.question_type == 'CXO')

    total_questions = question_query.count()

    # Count answered questions (filtered by user type)
    answer_query = db.query(models.SurveyResponse).join(models.Question).filter(
        models.SurveyResponse.survey_id == survey.id,
        models.SurveyResponse.user_id == current_user.id,
        models.SurveyResponse.score.isnot(None)
    )
    # CXO users only count CXO questions
    if current_user.user_type == models.UserType.CXO:
        answer_query = answer_query.filter(models.Question.question_type == 'CXO')

    answered = answer_query.distinct(models.SurveyResponse.question_id).count()

    if answered < total_questions:
        raise HTTPException(
            status_code=400,
            detail=f"Survey incomplete. {answered}/{total_questions} questions answered"
        )

    # Create user submission record
    user_submission = models.UserSurveySubmission(
        survey_id=survey.id,
        user_id=current_user.id,
        submitted_at=func.now()
    )
    db.add(user_submission)

    # Update survey status if this is the first submission
    if survey.status == "Not Started":
        survey.status = "In Progress"

    # Check if all users from this customer have submitted
    customer_users = db.query(models.User).filter(
        models.User.customer_id == current_user.customer_id,
        models.User.user_type.in_([models.UserType.CXO, models.UserType.PARTICIPANT]),
        models.User.is_deleted == False
    ).count()

    submissions_count = db.query(models.UserSurveySubmission).filter(
        models.UserSurveySubmission.survey_id == survey.id
    ).count() + 1  # +1 for current submission

    if submissions_count >= customer_users:
        survey.status = "Submitted"
        survey.submitted_at = func.now()

    db.commit()

    return {"message": "Survey submitted successfully"}

@router.get("/status")
def get_survey_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_customer_user)
):
    """
    Get overall survey status and customer code.
    Used for breadcrumbs and status display. (Customer users only)
    """
    if not current_user.customer_id:
        return {"status": "Not Started", "customer_code": None}
    
    # Get customer
    customer = db.query(models.Customer).filter(
        models.Customer.id == current_user.customer_id
    ).first()
    
    # Get survey
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == current_user.customer_id
    ).first()
    
    if not survey:
        return {
            "status": "Not Started",
            "customer_code": customer.customer_code if customer else None
        }

    # Check if current user has submitted
    user_submission = db.query(models.UserSurveySubmission).filter(
        models.UserSurveySubmission.survey_id == survey.id,
        models.UserSurveySubmission.user_id == current_user.id
    ).first()

    if user_submission:
        return {
            "status": "Submitted",
            "customer_code": customer.customer_code if customer else None
        }
    
    # Calculate progress for the CURRENT USER (filtered by user type)
    question_query = db.query(models.Question)
    # CXO users only see CXO questions
    if current_user.user_type == models.UserType.CXO:
        question_query = question_query.filter(models.Question.question_type == 'CXO')

    total_questions = question_query.count()

    # Count answered questions (filtered by user type)
    answer_query = db.query(models.SurveyResponse).join(models.Question).filter(
        models.SurveyResponse.survey_id == survey.id,
        models.SurveyResponse.user_id == current_user.id,
        models.SurveyResponse.score.isnot(None)
    )
    # CXO users only count CXO questions
    if current_user.user_type == models.UserType.CXO:
        answer_query = answer_query.filter(models.Question.question_type == 'CXO')

    answered = answer_query.distinct(models.SurveyResponse.question_id).count()
    
    if answered == 0:
        status = "Not Started"
    elif answered == total_questions:
        status = "Completed"
    else:
        status = f"In Progress {answered}/{total_questions}"
    
    return {
        "status": status, 
        "customer_code": customer.customer_code if customer else None
    }