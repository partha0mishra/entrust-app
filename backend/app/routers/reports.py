from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional
from collections import Counter
import logging
import traceback
import asyncio
from .. import models, schemas, auth
from ..database import get_db
from ..llm_service import LLMService
from ..report_utils import save_reports, get_cached_report, check_report_exists_for_today, check_reports_path_exists, get_report_paths

router = APIRouter()
logger = logging.getLogger(__name__)


def aggregate_by_facet(
    facet_type: str,  # 'category', 'process', or 'lifecycle_stage'
    responses: List,
    questions: List
) -> Dict:
    """
    Aggregate scores by a specific facet (category, process, or lifecycle_stage)
    Returns dict with facet values as keys and their statistics
    """
    facet_data = {}

    # Get unique facet values
    facet_values = set()
    for q in questions:
        facet_value = getattr(q, facet_type, None)
        if facet_value:
            facet_values.add(facet_value)

    for facet_value in facet_values:
        # Get questions for this facet
        facet_questions = [q for q in questions if getattr(q, facet_type, None) == facet_value]
        facet_question_ids = [q.id for q in facet_questions]

        # Get responses for these questions
        facet_responses = [r for r in responses if r.question_id in facet_question_ids]

        # Calculate scores
        numeric_scores = [
            float(r.score) for r in facet_responses
            if r.score and r.score != 'NA'
        ]

        # Get comments
        comments = [r.comment for r in facet_responses if r.comment]

        # Get unique respondents
        respondent_count = len(set(r.user_id for r in facet_responses))

        if numeric_scores:
            # Calculate score distribution
            high_scores = [s for s in numeric_scores if s >= 8.0]
            medium_scores = [s for s in numeric_scores if 5.0 <= s < 8.0]
            low_scores = [s for s in numeric_scores if s < 5.0]

            total_scores = len(numeric_scores)
            pct_high = round((len(high_scores) / total_scores * 100), 1) if total_scores > 0 else 0
            pct_medium = round((len(medium_scores) / total_scores * 100), 1) if total_scores > 0 else 0
            pct_low = round((len(low_scores) / total_scores * 100), 1) if total_scores > 0 else 0

            facet_data[facet_value] = {
                'name': facet_value,
                'avg_score': round(sum(numeric_scores) / len(numeric_scores), 2),
                'min_score': round(min(numeric_scores), 2),
                'max_score': round(max(numeric_scores), 2),
                'count': len(numeric_scores),
                'respondents': respondent_count,
                'comments': comments,
                # Score distribution
                'score_distribution': {
                    'high_count': len(high_scores),
                    'medium_count': len(medium_scores),
                    'low_count': len(low_scores),
                    'pct_high': pct_high,
                    'pct_medium': pct_medium,
                    'pct_low': pct_low
                },
                'questions': [
                    {
                        'text': q.text,
                        'question_id': q.question_id
                    }
                    for q in facet_questions
                ]
            }
        else:
            facet_data[facet_value] = {
                'name': facet_value,
                'avg_score': None,
                'min_score': None,
                'max_score': None,
                'count': 0,
                'respondents': 0,
                'comments': [],
                # Score distribution
                'score_distribution': {
                    'high_count': 0,
                    'medium_count': 0,
                    'low_count': 0,
                    'pct_high': 0,
                    'pct_medium': 0,
                    'pct_low': 0
                },
                'questions': [
                    {
                        'text': q.text,
                        'question_id': q.question_id
                    }
                    for q in facet_questions
                ]
            }

    return facet_data


def analyze_comments_basic(all_comments: List[str]) -> Dict:
    """
    Perform basic comment analysis without LLM
    Returns word frequency, basic statistics, and simple sentiment analysis
    """
    if not all_comments:
        return {
            'total_comments': 0,
            'word_frequency': {},
            'avg_comment_length': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'positive_words': [],
            'negative_words': []
        }

    # Word frequency analysis
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
        'when', 'where', 'why', 'how', 'not', 'no', 'yes',
        # Additional stop words
        'some', 'there', 'its', 'their', 'our', 'your', 'my', 'his', 'her',
        'them', 'us', 'me', 'him', 'from', 'into', 'out', 'up', 'down',
        'over', 'under', 'about', 'just', 'very', 'so', 'than', 'too',
        'also', 'only', 'other', 'such', 'more', 'most', 'much', 'many',
        'any', 'all', 'both', 'each', 'few', 'as', 'by', 'if', 'then',
        'because', 'while', 'after', 'before', 'since', 'until', 'through',
        'during', 'within', 'without', 'between', 'among'
    }

    word_counter = Counter()
    total_length = 0
    all_meaningful_words = []

    for comment in all_comments:
        total_length += len(comment)
        # Simple word tokenization
        words = comment.lower().split()
        # Filter out stop words and short words
        meaningful_words = [
            w.strip('.,!?;:()[]{}"\'-')
            for w in words
            if len(w) > 3 and w.lower() not in stop_words
        ]
        word_counter.update(meaningful_words)
        all_meaningful_words.append(meaningful_words)

    # Get top 20 words
    top_words = dict(word_counter.most_common(20))

    # Simple sentiment analysis using keyword matching
    positive_keywords = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
        'strong', 'effective', 'efficient', 'helpful', 'useful', 'valuable', 'benefit',
        'improved', 'improvement', 'better', 'best', 'well', 'clear', 'easy', 'simple',
        'comprehensive', 'robust', 'reliable', 'satisfied', 'satisfaction', 'success',
        'successful', 'positive', 'progress', 'advanced', 'quality', 'sound'
    }

    negative_keywords = {
        'poor', 'bad', 'terrible', 'awful', 'horrible', 'worst', 'weak', 'ineffective',
        'inefficient', 'useless', 'lacking', 'missing', 'inadequate', 'insufficient',
        'issue', 'issues', 'problem', 'problems', 'concern', 'concerns', 'challenge',
        'challenges', 'difficulty', 'difficult', 'hard', 'complicated', 'complex',
        'confusing', 'unclear', 'inconsistent', 'incomplete', 'limited', 'lack',
        'need', 'needs', 'require', 'required', 'should', 'must', 'gap', 'gaps'
    }

    positive_count = 0
    negative_count = 0
    neutral_count = 0
    positive_comment_words = Counter()
    negative_comment_words = Counter()

    for idx, comment in enumerate(all_comments):
        comment_lower = comment.lower()
        words_in_comment = set(comment_lower.split())

        # Check for positive and negative keywords
        has_positive = any(keyword in words_in_comment for keyword in positive_keywords)
        has_negative = any(keyword in words_in_comment for keyword in negative_keywords)

        if has_positive and not has_negative:
            positive_count += 1
            # Track words from positive comments
            if idx < len(all_meaningful_words):
                positive_comment_words.update(all_meaningful_words[idx])
        elif has_negative and not has_positive:
            negative_count += 1
            # Track words from negative comments
            if idx < len(all_meaningful_words):
                negative_comment_words.update(all_meaningful_words[idx])
        else:
            neutral_count += 1

    return {
        'total_comments': len(all_comments),
        'word_frequency': top_words,
        'avg_comment_length': round(total_length / len(all_comments), 1) if all_comments else 0,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'positive_words': dict(positive_comment_words.most_common(10)),
        'negative_words': dict(negative_comment_words.most_common(10))
    }

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

    # Sales, Admin, and CXO can view reports
    if current_user.user_type not in [models.UserType.SALES, models.UserType.SYSTEM_ADMIN, models.UserType.CXO]:
        raise HTTPException(status_code=403, detail="You do not have permission to view reports")

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
    force_regenerate: bool = Query(False, description="Force regeneration of report even if cached version exists"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.user_type == models.UserType.PARTICIPANT:
        raise HTTPException(status_code=403, detail="Participants cannot view reports")

    # Sales, Admin, and CXO can view reports
    if current_user.user_type not in [models.UserType.SALES, models.UserType.SYSTEM_ADMIN, models.UserType.CXO]:
        raise HTTPException(status_code=403, detail="You do not have permission to view reports")

    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == customer_id
    ).first()

    if not survey:
        return {"error": "No survey data available"}

    # Get customer information
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id
    ).first()

    if not customer:
        return {"error": "Customer not found"}

    # Check for cached report if not forcing regeneration
    if not force_regenerate:
        cached_report = get_cached_report(customer.customer_code, dimension, survey.updated_at)
        if cached_report:
            logger.info(f"Returning cached report for {customer.customer_code}/{dimension}")
            return cached_report

    questions = db.query(models.Question).filter(
        models.Question.dimension == dimension
    ).all()

    # Get all responses for this dimension
    all_responses = db.query(models.SurveyResponse).join(
        models.Question
    ).filter(
        models.SurveyResponse.survey_id == survey.id,
        models.Question.dimension == dimension,
        models.SurveyResponse.score.isnot(None)
    ).all()

    total_users = db.query(models.User).filter(
        models.User.customer_id == customer_id,
        models.User.user_type.in_([models.UserType.CXO, models.UserType.PARTICIPANT]),
        models.User.is_deleted == False
    ).count()

    # Overall metrics calculation
    all_numeric_scores = [float(r.score) for r in all_responses if r.score and r.score != 'NA']
    all_comments = [r.comment for r in all_responses if r.comment]
    total_respondents = len(set(r.user_id for r in all_responses))

    overall_metrics = {
        'avg_score': round(sum(all_numeric_scores) / len(all_numeric_scores), 2) if all_numeric_scores else None,
        'min_score': round(min(all_numeric_scores), 2) if all_numeric_scores else None,
        'max_score': round(max(all_numeric_scores), 2) if all_numeric_scores else None,
        'total_responses': len(all_numeric_scores),
        'total_respondents': total_respondents,
        'total_users': total_users,
        'response_rate': f"{round((total_respondents / total_users * 100), 1)}%" if total_users > 0 else "0%"
    }

    # Question-level data
    report_data = []
    questions_for_llm = []

    for question in questions:
        responses = [r for r in all_responses if r.question_id == question.id]

        responded_count = len(set(r.user_id for r in responses))

        numeric_scores = [float(r.score) for r in responses if r.score and r.score != 'NA']
        comments = [r.comment for r in responses if r.comment]

        min_score = min(numeric_scores) if numeric_scores else None
        max_score = max(numeric_scores) if numeric_scores else None
        avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else None

        report_data.append({
            "question": question.text,
            "question_id": question.question_id,
            "category": question.category,
            "process": question.process,
            "lifecycle_stage": question.lifecycle_stage,
            "responded": f"{responded_count}/{total_users}",
            "min_score": min_score,
            "max_score": max_score,
            "avg_score": round(avg_score, 2) if avg_score else None
        })

        questions_for_llm.append({
            "text": question.text,
            "avg_score": round(avg_score, 2) if avg_score else "N/A",
            "comments": comments,
            "category": question.category,
            "process": question.process,
            "lifecycle_stage": question.lifecycle_stage
        })

    # Multi-faceted aggregation
    category_analysis = aggregate_by_facet('category', all_responses, questions)
    process_analysis = aggregate_by_facet('process', all_responses, questions)
    lifecycle_analysis = aggregate_by_facet('lifecycle_stage', all_responses, questions)

    # Comment analysis
    comment_insights = analyze_comments_basic(all_comments)

    # Get LLM config
    llm_config = db.query(models.LLMConfig).filter(
        models.LLMConfig.purpose == dimension
    ).first()

    if not llm_config:
        llm_config = db.query(models.LLMConfig).filter(
            models.LLMConfig.purpose == "Default"
        ).first()

    # Generate dimension-level LLM analysis
    # Use asyncio.create_task to run LLM call in background - don't block the response
    dimension_llm_analysis = None
    rag_context = None
    llm_error = None

    # Log LLM config status for debugging
    if llm_config:
        logger.info(f"LLM config found for dimension '{dimension}': status='{llm_config.status}', provider='{llm_config.provider_type}', model='{llm_config.azure_deployment_name if llm_config.provider_type == models.LLMProviderType.AZURE else (llm_config.aws_model_id if llm_config.provider_type == models.LLMProviderType.BEDROCK else llm_config.model_name)}'")
        if llm_config.status != "Success":
            logger.warning(f"LLM config status is '{llm_config.status}' - LLM analysis will be skipped. Please test the connection first.")
    else:
        logger.warning(f"No LLM config found for dimension '{dimension}' - using Default config if available")

    if llm_config and llm_config.status == "Success":
        try:
            # Run LLM call with timeout to prevent hanging
            # With thinking mode enabled, Claude can take 20+ minutes for complex analysis
            # Check if thinking mode is enabled to adjust timeout
            is_thinking_mode = getattr(llm_config, 'aws_thinking_mode', None) == 'enabled'
            timeout_seconds = 1800.0 if is_thinking_mode else 300.0  # 30 min for thinking, 5 min for non-thinking (should be much faster with 8000 max_tokens)
            
            try:
                llm_response = await asyncio.wait_for(
                    LLMService.generate_deep_dimension_analysis(
                        llm_config,
                        dimension,
                        overall_metrics,
                        questions_for_llm,
                        category_analysis,
                        process_analysis,
                        lifecycle_analysis
                    ),
                    timeout=timeout_seconds
                )
                if llm_response.get("success"):
                    dimension_llm_analysis = llm_response.get("content")
                    rag_context = llm_response.get("rag_context")  # Capture RAG context
                else:
                    llm_error = llm_response.get("error")
                    logger.error(f"LLM analysis failed for dimension {dimension}: {llm_error}")
            except asyncio.TimeoutError:
                timeout_minutes = int(timeout_seconds / 60)
                llm_error = f"LLM analysis timed out after {timeout_minutes} minutes. {'With thinking mode enabled, this can take 20-30 minutes. ' if is_thinking_mode else ''}Please try again or check LLM configuration."
                logger.error(f"LLM analysis timed out for dimension {dimension} after {timeout_minutes} minutes (thinking_mode={is_thinking_mode})")
        except Exception as e:
            llm_error = str(e)
            logger.error(f"Exception generating dimension LLM analysis for {dimension}: {str(e)}\n{traceback.format_exc()}")

    # Generate facet-level LLM analyses
    category_llm_analyses = {}
    process_llm_analyses = {}
    lifecycle_llm_analyses = {}

    # Facet-level analyses provide detailed insights by category, process, and lifecycle stage
    # These analyses enhance report quality by providing granular insights
    if llm_config and llm_config.status == "Success":
        is_thinking_mode = getattr(llm_config, 'aws_thinking_mode', None) == 'enabled'
        # Increase timeout for thinking mode, use reasonable timeout for standard mode
        facet_timeout = 600.0 if is_thinking_mode else 300.0  # 10 min for thinking, 5 min for standard
        
        logger.info(f"Generating facet-level analyses for dimension {dimension} (timeout={facet_timeout}s, thinking_mode={is_thinking_mode})")
        
        # Category analyses
        for category_name, category_data in category_analysis.items():
            try:
                llm_response = await asyncio.wait_for(
                    LLMService.analyze_facet(
                        llm_config,
                        'category',
                        category_name,
                        category_data
                    ),
                    timeout=facet_timeout
                )
                if llm_response.get("success"):
                    category_llm_analyses[category_name] = llm_response.get("content")
                    logger.info(f"✓ Category analysis completed for {category_name}")
                else:
                    logger.warning(f"Category analysis failed for {category_name}: {llm_response.get('error', 'Unknown error')}")
            except asyncio.TimeoutError:
                logger.warning(f"Category analysis timed out for {category_name} after {facet_timeout}s")
            except Exception as e:
                logger.error(f"Category analysis error for {category_name}: {str(e)}")

        # Process analyses
        for process_name, process_data in process_analysis.items():
            try:
                llm_response = await asyncio.wait_for(
                    LLMService.analyze_facet(
                        llm_config,
                        'process',
                        process_name,
                        process_data
                    ),
                    timeout=facet_timeout
                )
                if llm_response.get("success"):
                    process_llm_analyses[process_name] = llm_response.get("content")
                    logger.info(f"✓ Process analysis completed for {process_name}")
                else:
                    logger.warning(f"Process analysis failed for {process_name}: {llm_response.get('error', 'Unknown error')}")
            except asyncio.TimeoutError:
                logger.warning(f"Process analysis timed out for {process_name} after {facet_timeout}s")
            except Exception as e:
                logger.error(f"Process analysis error for {process_name}: {str(e)}")

        # Lifecycle analyses
        for lifecycle_name, lifecycle_data in lifecycle_analysis.items():
            try:
                llm_response = await asyncio.wait_for(
                    LLMService.analyze_facet(
                        llm_config,
                        'lifecycle_stage',
                        lifecycle_name,
                        lifecycle_data
                    ),
                    timeout=facet_timeout
                )
                if llm_response.get("success"):
                    lifecycle_llm_analyses[lifecycle_name] = llm_response.get("content")
                    logger.info(f"✓ Lifecycle analysis completed for {lifecycle_name}")
                else:
                    logger.warning(f"Lifecycle analysis failed for {lifecycle_name}: {llm_response.get('error', 'Unknown error')}")
            except asyncio.TimeoutError:
                logger.warning(f"Lifecycle analysis timed out for {lifecycle_name} after {facet_timeout}s")
            except Exception as e:
                logger.error(f"Lifecycle analysis error for {lifecycle_name}: {str(e)}")
        
        logger.info(f"Facet analysis summary: {len(category_llm_analyses)} categories, {len(process_llm_analyses)} processes, {len(lifecycle_llm_analyses)} lifecycle stages")

    # Generate comment sentiment analysis with LLM
    comment_llm_analysis = None
    if llm_config and llm_config.status == "Success" and all_comments:
        try:
            llm_response = await asyncio.wait_for(
                LLMService.analyze_comments_sentiment(
                    llm_config,
                    all_comments
                ),
                timeout=300.0  # 5 minute timeout
            )
            if llm_response.get("success"):
                comment_llm_analysis = llm_response.get("content")
        except (asyncio.TimeoutError, Exception):
            pass  # Silently skip if analysis fails or times out

    # Prepare report data
    report_response = {
        "dimension": dimension,
        "overall_metrics": overall_metrics,
        "questions": report_data,

        # Multi-faceted analysis
        "category_analysis": category_analysis,
        "process_analysis": process_analysis,
        "lifecycle_analysis": lifecycle_analysis,

        # Comment insights
        "comment_insights": {
            **comment_insights,
            "llm_analysis": comment_llm_analysis
        },

        # LLM analyses
        "dimension_llm_analysis": dimension_llm_analysis,
        "category_llm_analyses": category_llm_analyses,
        "process_llm_analyses": process_llm_analyses,
        "lifecycle_llm_analyses": lifecycle_llm_analyses,

        # RAG context
        "rag_context": rag_context,

        "llm_error": llm_error if llm_error else ("Orchestrate LLM not configured or test not successful" if not (llm_config and llm_config.status == "Success") else None)
    }

    # Save reports to disk (markdown and JSON) using customer storage configuration
    try:
        save_result = save_reports(
            customer_code=customer.customer_code,
            customer_name=customer.name,
            dimension=dimension,
            report_data=report_response,
            rag_context=rag_context,  # Pass RAG context retrieved from LLM analysis
            customer=customer  # Pass customer for storage configuration
        )
        if save_result.get('error'):
            logger.warning(f"Report save had issues: {save_result['error']}")
        else:
            storage_type = save_result.get('storage_type', 'LOCAL')
            logger.info(f"Reports saved to {storage_type}: MD={save_result.get('markdown_path')}, JSON={save_result.get('json_path')}")
    except Exception as e:
        logger.error(f"Failed to save reports: {str(e)}")
        # Don't fail the request if saving fails

    return report_response


@router.get("/customer/{customer_id}/overall")
async def get_overall_report(
    customer_id: int,
    force_regenerate: bool = Query(False, description="Force regeneration of report even if cached version exists"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.user_type == models.UserType.PARTICIPANT:
        raise HTTPException(status_code=403, detail="Participants cannot view reports")

    # Sales, Admin, and CXO can view reports
    if current_user.user_type not in [models.UserType.SALES, models.UserType.SYSTEM_ADMIN, models.UserType.CXO]:
        raise HTTPException(status_code=403, detail="You do not have permission to view reports")

    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == customer_id
    ).first()

    if not survey:
        return {"error": "No survey data available"}

    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id
    ).first()

    if not customer:
        return {"error": "Customer not found"}

    # Check for cached report if not forcing regeneration
    if not force_regenerate:
        cached_report = get_cached_report(customer.customer_code, "Overall", survey.updated_at)
        if cached_report:
            logger.info(f"Returning cached overall report for {customer.customer_code}")
            return cached_report

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
            
            # If dimension-specific config doesn't exist or is not tested, fall back to Default
            if not llm_config or (llm_config and llm_config.status != "Success"):
                llm_config = db.query(models.LLMConfig).filter(
                    models.LLMConfig.purpose == "Default"
                ).first()
            
            if llm_config and llm_config.status == "Success":
                llm_response = await LLMService.generate_dimension_summary(
                    llm_config,
                    dimension,
                    questions_for_llm
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
        
        logger.info(f"Orchestrate LLM check: found={orchestrate_llm is not None}, status={orchestrate_llm.status if orchestrate_llm else 'None'}, dimension_summaries_count={len(dimension_summaries)}")
        
        if orchestrate_llm and orchestrate_llm.status == "Success":
            # Check if we have valid dimension summaries (not all error messages)
            valid_summaries = {k: v for k, v in dimension_summaries.items() 
                             if v and not v.startswith("LLM not configured") and not v.startswith("Error:")}
            
            if not valid_summaries:
                overall_error = "No valid dimension summaries available. Please ensure at least one dimension has a tested LLM configuration."
                logger.warning(f"All dimension summaries are errors: {list(dimension_summaries.values())}")
            else:
                # Use only valid summaries for overall report
                llm_response = await LLMService.generate_overall_summary(
                    orchestrate_llm,
                    valid_summaries
                )

                if llm_response.get("success"):
                    # generate_overall_summary returns "markdown_content" not "content"
                    overall_summary = llm_response.get("markdown_content") or llm_response.get("content")
                else:
                    overall_error = llm_response.get("error")
                    logger.error(f"LLM overall summary generation failed: {overall_error}")
        else:
            overall_error = "Orchestrate LLM not configured or test not successful"
            logger.warning(f"Orchestrate LLM not available: status={orchestrate_llm.status if orchestrate_llm else 'None'}")
    except Exception as e:
        overall_error = str(e)
        logger.error(f"Exception generating overall summary: {str(e)}\n{traceback.format_exc()}")
    
    # Aggregate dimension-level data for cross-dimension analysis
    all_dimension_data = []
    aggregated_rag_contexts = {}

    for dim_data in overall_stats["dimensions"]:
        if dim_data["avg_score"] is not None:
            all_dimension_data.append({
                "dimension": dim_data["dimension"],
                "avg_score": dim_data["avg_score"],
                "min_score": dim_data["min_score"],
                "max_score": dim_data["max_score"],
                "question_count": dim_data["question_count"]
            })

    # Prepare comprehensive report data (matching dimension report structure)
    report_response = {
        "dimension": "Overall",
        "customer_code": customer.customer_code if customer else None,
        "customer_name": customer.name if customer else None,
        "survey_status": survey.status,
        "submitted_at": survey.submitted_at.isoformat() if survey.submitted_at else None,
        "total_participants": total_users,

        # Overall metrics (similar to dimension reports)
        "overall_metrics": {
            "avg_score": overall_stats["avg_score_overall"],
            "response_rate": f"{round((total_users / total_users * 100) if total_users > 0 else 0, 1)}%",
            "total_responses": overall_stats["total_responses"],
            "total_respondents": total_users,
            "total_users": total_users,
            "total_questions": overall_stats["total_questions"],
            "total_dimensions": len(dimensions)
        },

        # Main analysis content
        "overall_summary": overall_summary,
        "dimension_llm_analysis": overall_summary,  # Use overall_summary as main analysis

        # Dimension-level data for visualizations
        "overall_stats": overall_stats,
        "dimension_summaries": dimension_summaries,
        "dimension_comparison": all_dimension_data,

        # Aggregated RAG contexts from dimension analyses
        "rag_context": aggregated_rag_contexts if aggregated_rag_contexts else None,

        # Error tracking
        "llm_error": overall_error,
        "overall_error": overall_error
    }

    # Save reports to disk (markdown and JSON) using customer storage configuration
    try:
        save_result = save_reports(
            customer_code=customer.customer_code,
            customer_name=customer.name,
            dimension="Overall",
            report_data=report_response,
            rag_context=None,  # RAG context is dimension-specific, not applicable for overall report
            customer=customer  # Pass customer for storage configuration
        )
        if save_result.get('error'):
            logger.warning(f"Report save had issues: {save_result['error']}")
        else:
            storage_type = save_result.get('storage_type', 'LOCAL')
            logger.info(f"Overall reports saved to {storage_type}: MD={save_result.get('markdown_path')}, JSON={save_result.get('json_path')}")
    except Exception as e:
        logger.error(f"Failed to save overall reports: {str(e)}")
        # Don't fail the request if saving fails

    return report_response


@router.get("/customer/{customer_id}/reports/check-availability")
def check_reports_availability(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_report_access)
):
    """
    Check which reports exist for today for all dimensions
    Only accessible by CXO and Sales roles
    """
    # Check if customer exists
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Check if user has access to this customer
    if current_user.user_type == models.UserType.SALES and current_user.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Access denied to this customer's reports")

    # Get all dimensions
    dimensions = db.query(models.Question.dimension).distinct().all()
    dimension_list = [d[0] for d in dimensions]
    dimension_list.append("Overall")  # Add overall report

    # Check folder path
    folder_path_exists = check_reports_path_exists()

    # Check availability for each dimension
    availability = {}
    for dimension in dimension_list:
        availability[dimension] = check_report_exists_for_today(
            customer_code=customer.customer_code,
            dimension=dimension
        )

    return {
        "customer_code": customer.customer_code,
        "customer_name": customer.name,
        "folder_path_exists": folder_path_exists,
        "reports_base_path": "/app/entrust" if folder_path_exists else None,
        "availability": availability
    }


@router.get("/customer/{customer_id}/reports/html/{dimension}")
def get_html_report(
    customer_id: int,
    dimension: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_report_access)
):
    """
    Get the HTML report for a specific dimension
    Only accessible by CXO and Sales roles
    """
    from fastapi.responses import HTMLResponse
    import os

    # Check if customer exists
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Check if user has access to this customer
    if current_user.user_type == models.UserType.SALES and current_user.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Access denied to this customer's reports")

    # Check if base path exists
    if not check_reports_path_exists():
        raise HTTPException(status_code=404, detail="Reports folder not found. Please create the folder first.")

    # Get report paths
    paths = get_report_paths(customer.customer_code, dimension)
    html_path = paths.get('html')

    # Check if HTML report exists
    if not html_path or not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail=f"HTML report not found for {dimension}. Please generate the report first.")

    # Read HTML content and return as response
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Add security headers
        return HTMLResponse(
            content=html_content,
            headers={
                "Content-Security-Policy": "default-src 'self' 'unsafe-inline'; script-src 'none'; object-src 'none';",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY"
            }
        )
    except Exception as e:
        logger.error(f"Error reading HTML report for customer {customer_id}, dimension {dimension}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reading HTML report. Please contact support.")