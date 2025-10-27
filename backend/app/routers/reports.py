from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from .. import models, schemas, auth
from ..database import get_db
from ..llm_service import LLMService

router = APIRouter()

@router.get("/customers")
def get_customers_with_surveys(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get list of all customers that have surveys.
    Sales and Admin users can see all customers, CXO can see only their own.
    """
    query = db.query(models.Customer).filter(
        models.Customer.is_deleted == False
    )
    
    # Filter by customer_id for CXO users
    if current_user.user_type == models.UserType.CXO and current_user.customer_id:
        query = query.filter(models.Customer.id == current_user.customer_id)
    
    customers = query.all()
    
    # Include all customers, but mark which ones have surveys
    result = []
    for customer in customers:
        survey = db.query(models.Survey).filter(
            models.Survey.customer_id == customer.id
        ).first()
        
        result.append({
            "id": customer.id,
            "customer_code": customer.customer_code,
            "name": customer.name,
            "has_survey": survey is not None,
            "survey_status": survey.status if survey else None
        })
    
    # Debug: Log the results
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"User {current_user.user_id} ({current_user.user_type}) - Found {len(result)} customers with surveys")
    logger.info(f"Customers: {[c['name'] for c in result]}")
    
    return result


@router.get("/customer/{customer_id}/dimensions")
def get_dimension_reports(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.user_type == models.UserType.PARTICIPANT:
        raise HTTPException(status_code=403, detail="Participants cannot view reports")
    
    # Sales and Admin can view any customer, CXO can only view their own
    if current_user.user_type not in [models.UserType.SALES, models.UserType.SYSTEM_ADMIN]:
        if current_user.customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Can only view your own customer's reports")
    
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == customer_id
    ).first()
    
    if not survey:
        return {"message": "No survey data available"}
    
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
    
    # Sales and Admin can view any customer, CXO can only view their own
    if current_user.user_type not in [models.UserType.SALES, models.UserType.SYSTEM_ADMIN]:
        if current_user.customer_id != customer_id:
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
    
    # Generate LLM summary with model_name
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
            # FIXED: Pass model_name from config
            llm_response = await LLMService.generate_dimension_summary(
                llm_config.api_url,
                llm_config.api_key,
                dimension,
                questions_for_llm,
                llm_config.model_name or "default"  # Use configured model_name
            )

            if llm_response.get("success"):
                llm_summary = llm_response.get("final_summary")
            else:
                llm_error = llm_response.get("error")
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
    if current_user.user_type == models.UserType.PARTICIPANT:
        raise HTTPException(status_code=403, detail="Participants cannot view reports")
    
    # Sales and Admin can view any customer, CXO can only view their own
    if current_user.user_type not in [models.UserType.SALES, models.UserType.SYSTEM_ADMIN]:
        if current_user.customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Can only view your own customer's reports")
    
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == customer_id
    ).first()
    
    if not survey:
        return {"error": "No survey data available"}
    
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id
    ).first()
    
    dimensions_query = db.query(models.Question.dimension).distinct().all()
    dimensions = [d[0] for d in dimensions_query]
    
    total_users = db.query(models.User).filter(
        models.User.customer_id == customer_id,
        models.User.user_type.in_([models.UserType.CXO, models.UserType.PARTICIPANT]),
        models.User.is_deleted == False
    ).count()
    
    overall_stats = {
        "total_questions": 0,
        "total_responses": 0,
        "avg_score_overall": 0,
        "dimensions": []
    }
    
    dimension_summaries = {}
    
    for dimension in dimensions:
        questions = db.query(models.Question).filter(
            models.Question.dimension == dimension
        ).all()
        
        question_count = len(questions)
        overall_stats["total_questions"] += question_count
        
        dimension_data = {
            "dimension": dimension,
            "question_count": question_count,
            "responses": [],
            "avg_score": None,
            "min_score": None,
            "max_score": None
        }
        
        questions_for_llm = []
        all_scores = []
        
        for question in questions:
            responses = db.query(models.SurveyResponse).filter(
                models.SurveyResponse.survey_id == survey.id,
                models.SurveyResponse.question_id == question.id,
                models.SurveyResponse.score.isnot(None)
            ).all()
            
            responded_count = len(set(r.user_id for r in responses))
            overall_stats["total_responses"] += responded_count
            
            numeric_scores = [float(r.score) for r in responses if r.score and r.score != 'NA']
            comments = [r.comment for r in responses if r.comment]
            all_scores.extend(numeric_scores)
            
            min_score = min(numeric_scores) if numeric_scores else None
            max_score = max(numeric_scores) if numeric_scores else None
            avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else None
            
            dimension_data["responses"].append({
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
        
        if all_scores:
            dimension_data["avg_score"] = round(sum(all_scores) / len(all_scores), 2)
            dimension_data["min_score"] = round(min(all_scores), 2)
            dimension_data["max_score"] = round(max(all_scores), 2)
        
        overall_stats["dimensions"].append(dimension_data)
        
        # Generate dimension summary for overall report
        try:
            llm_config = db.query(models.LLMConfig).filter(
                models.LLMConfig.purpose == dimension
            ).first()
            
            if not llm_config:
                llm_config = db.query(models.LLMConfig).filter(
                    models.LLMConfig.purpose == "Default"
                ).first()
            
            if llm_config and llm_config.status == "Success":
                llm_response = await LLMService.generate_dimension_summary(
                    llm_config.api_url,
                    llm_config.api_key,
                    dimension,
                    questions_for_llm,
                    llm_config.model_name or "default"
                )

                if llm_response.get("success"):
                    dimension_summaries[dimension] = llm_response.get("final_summary", "Summary generation failed")
                else:
                    dimension_summaries[dimension] = f"Error: {llm_response.get('error', 'Unknown error')}"
            else:
                dimension_summaries[dimension] = "LLM not configured or test not successful"
        except Exception as e:
            dimension_summaries[dimension] = f"Error generating summary: {str(e)}"
    
    # Calculate overall average
    all_dimension_scores = []
    for dim_data in overall_stats["dimensions"]:
        if dim_data["avg_score"]:
            all_dimension_scores.append(dim_data["avg_score"])
    
    if all_dimension_scores:
        overall_stats["avg_score_overall"] = round(sum(all_dimension_scores) / len(all_dimension_scores), 2)
    
    # Generate overall summary using Orchestrate LLM
    overall_summary = None
    overall_error = None
    
    try:
        orchestrate_llm = db.query(models.LLMConfig).filter(
            models.LLMConfig.purpose == "Orchestrate"
        ).first()
        
        if not orchestrate_llm:
            orchestrate_llm = db.query(models.LLMConfig).filter(
                models.LLMConfig.purpose == "Default"
            ).first()
        
        if orchestrate_llm and orchestrate_llm.status == "Success":
            llm_response = await LLMService.generate_overall_summary(
                orchestrate_llm.api_url,
                orchestrate_llm.api_key,
                dimension_summaries,
                orchestrate_llm.model_name or "default"
            )

            if llm_response.get("success"):
                overall_summary = llm_response.get("content")
            else:
                overall_error = llm_response.get("error")
        else:
            overall_error = "Orchestrate LLM not configured or test not successful"
    except Exception as e:
        overall_error = str(e)
    
    return {
        "customer_code": customer.customer_code if customer else None,
        "customer_name": customer.name if customer else None,
        "survey_status": survey.status,
        "submitted_at": survey.submitted_at,
        "total_participants": total_users,
        "overall_stats": overall_stats,
        "dimension_summaries": dimension_summaries,
        "overall_summary": overall_summary,
        "overall_error": overall_error
    }