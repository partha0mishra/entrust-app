"""
Data Loader Tools
Loads survey data from database for flow processing
"""

import sys
import os
from typing import Dict, Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


def load_survey_from_db(survey_id: int, customer_id: int) -> Dict:
    """
    Load survey data from database

    Args:
        survey_id: Survey database ID
        customer_id: Customer database ID

    Returns:
        Dictionary with survey data, customer info, metadata

    Example:
        >>> data = load_survey_from_db(survey_id=1, customer_id=101)
        >>> print(data.keys())
        dict_keys(['survey_data', 'customer_code', 'customer_name', 'survey_metadata'])
    """
    try:
        from app.database import SessionLocal
        from app import models
        from sqlalchemy import func

        db = SessionLocal()

        # Get customer
        customer = db.query(models.Customer).filter(
            models.Customer.id == customer_id
        ).first()

        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Get survey
        survey = db.query(models.Survey).filter(
            models.Survey.id == survey_id,
            models.Survey.customer_id == customer_id
        ).first()

        if not survey:
            raise ValueError(f"Survey {survey_id} not found for customer {customer_id}")

        # Get all questions
        questions = db.query(models.Question).all()

        # Build survey data per dimension
        dimensions = db.query(models.Question.dimension).distinct().all()
        survey_data = {}

        for (dimension,) in dimensions:
            dim_questions = [q for q in questions if q.dimension == dimension]
            dim_responses = db.query(models.SurveyResponse).join(
                models.Question
            ).filter(
                models.SurveyResponse.survey_id == survey_id,
                models.Question.dimension == dimension
            ).all()

            questions_data = []
            for question in dim_questions:
                q_responses = [r for r in dim_responses if r.question_id == question.id]

                numeric_scores = [
                    float(r.score) for r in q_responses
                    if r.score and r.score != 'NA'
                ]
                comments = [r.comment for r in q_responses if r.comment]

                avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else None

                questions_data.append({
                    "question_id": question.question_id,
                    "text": question.text,
                    "category": question.category,
                    "process": question.process,
                    "lifecycle_stage": question.lifecycle_stage,
                    "guidance": question.guidance,
                    "avg_score": round(avg_score, 2) if avg_score else None,
                    "count": len(numeric_scores),
                    "comments": comments
                })

            survey_data[dimension] = {
                "questions": questions_data
            }

        # Get total users
        total_users = db.query(models.User).filter(
            models.User.customer_id == customer_id,
            models.User.user_type.in_([models.UserType.CXO, models.UserType.PARTICIPANT]),
            models.User.is_deleted == False
        ).count()

        # Get unique respondents
        total_respondents = len(set(r.user_id for r in dim_responses))

        survey_metadata = {
            "survey_id": survey.id,
            "customer_id": customer.id,
            "status": survey.status,
            "submitted_at": survey.submitted_at.isoformat() if survey.submitted_at else None,
            "total_users": total_users,
            "total_respondents": total_respondents,
            "response_rate": round((total_respondents / total_users * 100), 1) if total_users > 0 else 0
        }

        db.close()

        return {
            "survey_data": survey_data,
            "customer_code": customer.customer_code,
            "customer_name": customer.name,
            "survey_metadata": survey_metadata
        }

    except ImportError as e:
        raise ImportError(f"Database access requires backend modules: {e}")
    except Exception as e:
        raise Exception(f"Error loading survey from database: {e}")


# Tool definition for Azure AI Foundry
TOOL_DEFINITIONS = {
    "load_survey_from_db": {
        "function": load_survey_from_db,
        "description": "Load survey data from database",
        "parameters": {
            "type": "object",
            "properties": {
                "survey_id": {
                    "type": "integer",
                    "description": "Survey database ID"
                },
                "customer_id": {
                    "type": "integer",
                    "description": "Customer database ID"
                }
            },
            "required": ["survey_id", "customer_id"]
        }
    }
}


if __name__ == "__main__":
    # Test data loader (requires database connection)
    print("Testing Data Loader...")
    try:
        data = load_survey_from_db(survey_id=1, customer_id=1)
        print(f"Loaded data for: {data['customer_name']}")
        print(f"Dimensions: {list(data['survey_data'].keys())}")
        print(f"Metadata: {data['survey_metadata']}")
    except Exception as e:
        print(f"Error (expected if no DB): {e}")
