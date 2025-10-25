from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import markdown
from .. import models, schemas, auth
from ..database import get_db
from ..llm_service import LLMService

router = APIRouter()

# Ensure output directory exists
OUTPUT_DIR = Path("/app/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def markdown_to_text(md_text: str) -> str:
    """Convert markdown to plain text for PDF"""
    # Simple conversion - remove markdown formatting
    text = md_text.replace('**', '').replace('*', '')
    text = text.replace('###', '').replace('##', '').replace('#', '')
    text = text.replace('```', '')
    return text

def create_dimension_pdf(customer_code: str, dimension: str, report_data: Dict) -> str:
    """Create PDF for dimension report"""
    # Create customer directory
    customer_dir = OUTPUT_DIR / customer_code
    customer_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename
    safe_dimension = dimension.replace(' ', '_').replace('&', 'and')
    filename = f"{safe_dimension}_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = customer_dir / filename
    
    # Create PDF
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#00B74F'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"{dimension} Report", title_style))
    story.append(Paragraph(f"Customer: {customer_code}", styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # LLM Summary
    if report_data.get('llm_summary'):
        story.append(Paragraph("AI-Generated Summary & Suggestions", styles['Heading2']))
        summary_text = markdown_to_text(report_data['llm_summary'])
        for para in summary_text.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.strip(), styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        story.append(Spacer(1, 0.3*inch))
    
    # Questions Table
    story.append(Paragraph("Survey Results", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    # Table data
    table_data = [['Question', 'Responses', 'Min', 'Max', 'Avg']]
    for q in report_data.get('questions', []):
        table_data.append([
            Paragraph(q['question'][:100] + '...' if len(q['question']) > 100 else q['question'], styles['Normal']),
            q['responded'],
            str(q['min_score']) if q['min_score'] is not None else '-',
            str(q['max_score']) if q['max_score'] is not None else '-',
            str(q['avg_score']) if q['avg_score'] is not None else '-'
        ])
    
    # Create table
    table = Table(table_data, colWidths=[3.5*inch, 0.8*inch, 0.5*inch, 0.5*inch, 0.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00B74F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)
    
    return str(filepath)

def create_overall_pdf(customer_code: str, report_data: Dict) -> str:
    """Create PDF for overall report"""
    # Create customer directory
    customer_dir = OUTPUT_DIR / customer_code
    customer_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename
    filename = f"Overall_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = customer_dir / filename
    
    # Create PDF
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#00B74F'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Overall Data Governance Report", title_style))
    story.append(Paragraph(f"Customer: {customer_code}", styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    if report_data.get('executive_summary'):
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_text = markdown_to_text(report_data['executive_summary'])
        for para in summary_text.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.strip(), styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        story.append(Spacer(1, 0.3*inch))
    
    # Dimension Summaries
    story.append(Paragraph("Dimension Analysis", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    for dim_report in report_data.get('dimensions', []):
        story.append(Paragraph(dim_report['dimension'], styles['Heading3']))
        
        # Statistics
        stats_text = f"Average Score: {dim_report.get('avg_score', 'N/A')} | "
        stats_text += f"Response Rate: {dim_report.get('response_rate', 'N/A')}"
        story.append(Paragraph(stats_text, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Summary
        if dim_report.get('summary'):
            summary_text = markdown_to_text(dim_report['summary'])
            for para in summary_text.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    # Build PDF
    doc.build(story)
    
    return str(filepath)

@router.get("/customer/{customer_id}/dimensions")
def get_dimension_reports(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_report_access)
):
    """Get list of available dimension reports"""
    if current_user.user_type == models.UserType.CXO and current_user.customer_id != customer_id:
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
    current_user: models.User = Depends(auth.require_report_access)
):
    """Get detailed report for a specific dimension"""
    if current_user.user_type == models.UserType.CXO and current_user.customer_id != customer_id:
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
                llm_config.model_name
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
    current_user: models.User = Depends(auth.require_report_access)
):
    """Get overall report aggregating all dimensions"""
    if current_user.user_type == models.UserType.CXO and current_user.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Can only view your own customer's reports")
    
    survey = db.query(models.Survey).filter(
        models.Survey.customer_id == customer_id
    ).first()
    
    if not survey:
        return {"error": "No survey data available"}
    
    # Get all dimensions
    dimensions = db.query(models.Question.dimension).distinct().all()
    dimension_summaries = {}
    dimension_reports = []
    
    total_users = db.query(models.User).filter(
        models.User.customer_id == customer_id,
        models.User.user_type.in_([models.UserType.CXO, models.UserType.PARTICIPANT]),
        models.User.is_deleted == False
    ).count()
    
    # Generate summary for each dimension
    for (dimension,) in dimensions:
        questions = db.query(models.Question).filter(
            models.Question.dimension == dimension
        ).all()
        
        all_scores = []
        total_questions = len(questions)
        answered_questions = 0
        
        for question in questions:
            responses = db.query(models.SurveyResponse).filter(
                models.SurveyResponse.survey_id == survey.id,
                models.SurveyResponse.question_id == question.id,
                models.SurveyResponse.score.isnot(None)
            ).all()
            
            if responses:
                answered_questions += 1
                numeric_scores = [float(r.score) for r in responses if r.score and r.score != 'NA']
                all_scores.extend(numeric_scores)
        
        avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else None
        response_rate = f"{answered_questions}/{total_questions}"
        
        # Try to get LLM summary for this dimension
        try:
            llm_config = db.query(models.LLMConfig).filter(
                models.LLMConfig.purpose == dimension
            ).first()
            
            if not llm_config:
                llm_config = db.query(models.LLMConfig).filter(
                    models.LLMConfig.purpose == "Default"
                ).first()
            
            if llm_config and llm_config.status == "Success":
                questions_for_llm = []
                for question in questions:
                    responses = db.query(models.SurveyResponse).filter(
                        models.SurveyResponse.survey_id == survey.id,
                        models.SurveyResponse.question_id == question.id
                    ).all()
                    
                    numeric_scores = [float(r.score) for r in responses if r.score and r.score != 'NA']
                    comments = [r.comment for r in responses if r.comment]
                    q_avg = sum(numeric_scores) / len(numeric_scores) if numeric_scores else None
                    
                    questions_for_llm.append({
                        "text": question.text,
                        "avg_score": round(q_avg, 2) if q_avg else "N/A",
                        "comments": comments
                    })
                
                summary = await LLMService.generate_dimension_summary(
                    llm_config.api_url,
                    llm_config.api_key,
                    dimension,
                    questions_for_llm,
                    llm_config.model_name
                )
                dimension_summaries[dimension] = summary
            else:
                dimension_summaries[dimension] = f"Average Score: {avg_score}, Response Rate: {response_rate}"
        except Exception as e:
            dimension_summaries[dimension] = f"Average Score: {avg_score}, Response Rate: {response_rate} (LLM Error: {str(e)})"
        
        dimension_reports.append({
            "dimension": dimension,
            "avg_score": avg_score,
            "response_rate": response_rate,
            "summary": dimension_summaries[dimension]
        })
    
    # Generate overall executive summary using Orchestrate or Default LLM
    executive_summary = None
    llm_error = None
    
    try:
        orchestrate_llm = db.query(models.LLMConfig).filter(
            models.LLMConfig.purpose == "Orchestrate"
        ).first()
        
        if not orchestrate_llm:
            orchestrate_llm = db.query(models.LLMConfig).filter(
                models.LLMConfig.purpose == "Default"
            ).first()
        
        if orchestrate_llm and orchestrate_llm.status == "Success":
            executive_summary = await LLMService.generate_overall_summary(
                orchestrate_llm.api_url,
                orchestrate_llm.api_key,
                dimension_summaries,
                orchestrate_llm.model_name
            )
    except Exception as e:
        llm_error = str(e)
    
    return {
        "dimensions": dimension_reports,
        "executive_summary": executive_summary,
        "llm_error": llm_error
    }

@router.get("/customer/{customer_id}/dimension/{dimension}/download")
async def download_dimension_report(
    customer_id: int,
    dimension: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_report_access)
):
    """Download dimension report as PDF"""
    if current_user.user_type == models.UserType.CXO and current_user.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Can only view your own customer's reports")
    
    # Get customer code
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get report data
    report_response = await get_dimension_report(customer_id, dimension, db, current_user)
    
    # Create PDF
    pdf_path = create_dimension_pdf(customer.customer_code, dimension, report_response)
    
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=os.path.basename(pdf_path)
    )

@router.get("/customer/{customer_id}/overall/download")
async def download_overall_report(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_report_access)
):
    """Download overall report as PDF"""
    if current_user.user_type == models.UserType.CXO and current_user.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Can only view your own customer's reports")
    
    # Get customer code
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get report data
    report_response = await get_overall_report(customer_id, db, current_user)
    
    # Create PDF
    pdf_path = create_overall_pdf(customer.customer_code, report_response)
    
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=os.path.basename(pdf_path)
    )