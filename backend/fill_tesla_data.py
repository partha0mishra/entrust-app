#!/usr/bin/env python3
"""
Script to fill realistic EVTech (EVTC) survey responses based on their data practices.
Creates EVTech as a customer and fills comprehensive survey responses.
"""
import sys
import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app import models, auth

def create_tesla_data():
    """Create EVTech customer and fill realistic survey responses"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("  CREATING EVTECH (EVTC) SURVEY DATA")
        print("=" * 70)
        
        # Step 1: Create EVTech customer
        print("\n[1/5] Creating EVTech customer...")
        customer = db.query(models.Customer).filter(
            models.Customer.customer_code == "EVTC"
        ).first()
        
        if not customer:
            customer = models.Customer(
                customer_code="EVTC",
                name="EVTech Inc",
                industry="Automotive & Energy",
                location="Austin, Texas, USA",
                description="Electric vehicle manufacturer and energy storage company"
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            print(f"✓ Created customer: {customer.name} (ID: {customer.id})")
        else:
            print(f"✓ Customer already exists: {customer.name} (ID: {customer.id})")
        
        # Step 2: Create EVTech users
        print("\n[2/6] Creating EVTech users...")
        
        # Common password for all users (except admin)
        common_password = "Welcome123!"
        
        # Create CXO user
        cxo_user = db.query(models.User).filter(
            models.User.user_id == "ewhite"
        ).first()
        
        if not cxo_user:
            cxo_user = models.User(
                user_id="ewhite",
                username="Ethan White",
                password_hash=auth.get_password_hash(common_password),
                password=auth.encrypt_password(common_password),
                user_type=models.UserType.CXO,
                customer_id=customer.id
            )
            db.add(cxo_user)
            db.commit()
            db.refresh(cxo_user)
            print(f"✓ Created CXO user: {cxo_user.username} (ID: {cxo_user.id})")
        else:
            cxo_user.customer_id = customer.id
            cxo_user.password_hash = auth.get_password_hash(common_password)
            cxo_user.password = auth.encrypt_password(common_password)
            db.commit()
            print(f"✓ CXO user exists: {cxo_user.username} (ID: {cxo_user.id})")
        
        # Create Participant users
        participant_users = []
        participant_configs = [
            {"user_id": "mthomas", "username": "Maria Thomas"},
            {"user_id": "pjohnson", "username": "Paul Johnson"}
        ]
        
        for i, config in enumerate(participant_configs, 1):
            participant_id = config["user_id"]
            participant_name = config["username"]
            participant = db.query(models.User).filter(
                models.User.user_id == participant_id
            ).first()
            
            if not participant:
                participant = models.User(
                    user_id=participant_id,
                    username=participant_name,
                    password_hash=auth.get_password_hash(common_password),
                    password=auth.encrypt_password(common_password),
                    user_type=models.UserType.PARTICIPANT,
                    customer_id=customer.id
                )
                db.add(participant)
                db.commit()
                db.refresh(participant)
                print(f"✓ Created Participant {i}: {participant.username} (ID: {participant.id})")
            else:
                participant.customer_id = customer.id
                participant.password_hash = auth.get_password_hash(common_password)
                participant.password = auth.encrypt_password(common_password)
                db.commit()
                print(f"✓ Participant {i} exists: {participant.username} (ID: {participant.id})")
            
            participant_users.append(participant)
        
        # Create Sales user (Nagaraj)
        sales_user = db.query(models.User).filter(
            models.User.user_id == "Nagaraj"
        ).first()
        
        if not sales_user:
            sales_user = models.User(
                user_id="Nagaraj",
                username="Nagaraj",
                password_hash=auth.get_password_hash(common_password),
                password=auth.encrypt_password(common_password),
                user_type=models.UserType.SALES,
                customer_id=None  # Sales users don't belong to a specific customer
            )
            db.add(sales_user)
            db.commit()
            db.refresh(sales_user)
            print(f"✓ Created Sales user: {sales_user.username} (ID: {sales_user.id})")
        else:
            sales_user.password_hash = auth.get_password_hash(common_password)
            sales_user.password = auth.encrypt_password(common_password)
            db.commit()
            print(f"✓ Sales user exists: {sales_user.username} (ID: {sales_user.id})")
        
        # Step 3: Create survey
        print("\n[3/6] Creating survey...")
        survey = db.query(models.Survey).filter(
            models.Survey.customer_id == customer.id
        ).first()
        
        if not survey:
            survey = models.Survey(customer_id=customer.id)
            db.add(survey)
            db.commit()
            db.refresh(survey)
            print(f"✓ Created survey (ID: {survey.id})")
        else:
            print(f"✓ Survey already exists (ID: {survey.id})")
        
        # Step 4: Get all questions
        print("\n[4/6] Loading questions...")
        all_questions = db.query(models.Question).all()
        print(f"✓ Found {len(all_questions)} questions")
        
        # Get CXO questions
        cxo_questions = [q for q in all_questions if q.question_type == 'CXO']
        print(f"   - CXO questions: {len(cxo_questions)}")
        
        # Get Participant questions (all questions)
        participant_questions = all_questions
        print(f"   - Participant questions: {len(participant_questions)}")
        
        # Step 5: Fill responses with realistic EVTech answers
        print("\n[5/6] Filling survey responses with realistic EVTech data...")
        
        def get_tesla_score(question, dimension, category):
            """Get realistic score for EVTech based on their data practices"""
            dimension_lower = dimension.lower()
            category_lower = category.lower() if category else ""
            text_lower = question.text.lower()
            
            # Data Security & Access - EVTech is strong (4-5)
            if "security" in dimension_lower or "encryption" in text_lower:
                if "sensitive" in text_lower or "encrypted" in text_lower:
                    return random.choice([4, 5])  # Strong encryption practices
                return random.choice([4, 5])
            
            # Data Privacy & Compliance - Mixed (3-4)
            if "privacy" in dimension_lower or "compliance" in dimension_lower:
                if "consent" in text_lower:
                    return random.choice([3, 4])  # Some privacy concerns
                if "gdpr" in text_lower or "ccpa" in text_lower:
                    return random.choice([4, 5])  # Compliance is important
                return random.choice([3, 4])
            
            # Data Quality - Strong (4-5) - Manufacturing focus
            if "quality" in dimension_lower:
                if "validation" in text_lower or "accuracy" in text_lower:
                    return random.choice([4, 5])  # Manufacturing quality standards
                return random.choice([4, 5])
            
            # Data Lineage & Traceability - Strong (4-5) - Critical for manufacturing
            if "lineage" in dimension_lower or "traceability" in dimension_lower:
                return random.choice([4, 5])  # Supply chain tracking
            
            # Data Governance & Management - Good (3-4)
            if "governance" in dimension_lower or "management" in dimension_lower:
                if "policy" in text_lower or "documented" in text_lower:
                    return random.choice([3, 4])  # Some formalization
                return random.choice([3, 4])
            
            # Metadata & Documentation - Moderate (3-4)
            if "metadata" in dimension_lower or "documentation" in dimension_lower:
                return random.choice([3, 4])
            
            # Data Value & Lifecycle Management - Good (3-4)
            if "value" in dimension_lower or "lifecycle" in dimension_lower:
                return random.choice([3, 4])
            
            # Data Ethics & Bias - Moderate (3-4) - AI/ML focus
            if "ethics" in dimension_lower or "bias" in dimension_lower:
                if "ai" in text_lower or "ml" in text_lower or "model" in text_lower:
                    return random.choice([3, 4])  # Active area of concern
                return random.choice([3, 4])
            
            # Default: Good practices
            return random.choice([3, 4])
        
        def get_tesla_comment(question, dimension, score):
            """Get detailed, realistic comment for EVTech based on question context"""
            dimension_lower = dimension.lower()
            category_lower = question.category.lower() if question.category else ""
            text_lower = question.text.lower()
            
            # Security & Encryption - Detailed EVTech-specific comments
            if "security" in dimension_lower or "encryption" in text_lower:
                if "sensitive" in text_lower or "encrypted" in text_lower:
                    return "All vehicle telemetry data, customer PII, and manufacturing IP are encrypted using AES-256. EVTech implements end-to-end encryption for data in transit between vehicles and cloud infrastructure, with separate encryption keys for different data classifications."
                elif "access" in text_lower or "privilege" in text_lower:
                    return "Access control follows zero-trust principles. Manufacturing data access is restricted to production teams, vehicle data to engineering teams, and customer data to authorized service personnel only. Role-based access reviewed quarterly."
                else:
                    return "Multi-layer security architecture includes network segmentation, intrusion detection systems, and regular penetration testing. Security operations center monitors 24/7 for anomalies in vehicle and manufacturing systems."
            
            # Privacy & Compliance - EVTech's data collection practices
            elif "privacy" in dimension_lower or "compliance" in dimension_lower:
                if "consent" in text_lower:
                    return "Vehicle owners consent to data collection during purchase and service agreements. However, the extent of telemetry data collection (location, driving behavior, camera footage) has raised privacy concerns. Transparency improvements ongoing."
                elif "gdpr" in text_lower or "ccpa" in text_lower or "regulation" in text_lower:
                    return "Compliant with GDPR, CCPA, and automotive data protection regulations. Data processing agreements in place for EU operations. Regular compliance audits conducted. Customer data deletion requests processed within 30 days."
                elif "transparency" in text_lower or "communicated" in text_lower:
                    return "Privacy policy clearly states data collection practices, but technical details about AI training data usage could be more transparent. Customer dashboard shows what data is collected from their vehicle."
                else:
                    return "Privacy team works closely with legal and engineering. Data minimization principles applied where possible, though extensive telemetry needed for Autopilot/FSD development creates tension with privacy goals."
            
            # Data Quality - Manufacturing excellence
            elif "quality" in dimension_lower:
                if "validation" in text_lower or "accuracy" in text_lower:
                    return "Real-time data validation in Gigafactories ensures production data accuracy. Sensor data from production lines validated against quality thresholds. Anomalies trigger immediate alerts to production managers."
                elif "audit" in text_lower or "monitor" in text_lower:
                    return "Daily automated data quality checks across all manufacturing systems. Weekly manual audits of critical production metrics. Data quality dashboard visible to all production managers in real-time."
                elif "cleansing" in text_lower or "remediation" in text_lower:
                    return "Automated data cleansing pipelines run hourly for production data. Vehicle telemetry data cleaned before ingestion into analytics systems. Data quality issues tracked in JIRA and resolved within SLA."
                else:
                    return "Data quality is critical for manufacturing operations. Quality metrics defined for all production data sources. Quality scorecards reviewed in weekly production meetings. Poor data quality directly impacts vehicle quality."
            
            # Lineage & Traceability - Supply chain focus
            elif "lineage" in dimension_lower or "traceability" in dimension_lower:
                if "column" in text_lower or "detail" in text_lower:
                    return "Vehicle VIN provides complete lineage from raw materials (battery cells, steel) through assembly to final delivery. Each component has unique identifier tracked through entire supply chain. Column-level lineage available for critical manufacturing data."
                elif "history" in text_lower or "transformations" in text_lower:
                    return "Complete transformation history tracked for all vehicle production data. Data lineage tool shows how raw sensor data becomes production metrics, quality scores, and business reports. Lineage critical for quality recalls."
                elif "audit" in text_lower or "access" in text_lower:
                    return "Data lineage accessible to quality, engineering, and compliance teams. Lineage queries used daily to trace quality issues back to source systems. Audit logs show who accessed lineage data and when."
                else:
                    return "Supply chain traceability is mandatory for regulatory compliance and quality control. Every vehicle component can be traced to supplier, batch, and production line. Lineage system integrated with ERP and MES systems."
            
            # Governance & Management
            elif "governance" in dimension_lower or "management" in dimension_lower:
                if "policy" in text_lower or "documented" in text_lower:
                    return "Data governance policies documented in internal wiki. Key policies cover data classification, retention, access control, and AI/ML data usage. Policies reviewed annually, but rapid growth means some areas need updating."
                elif "role" in text_lower or "responsibility" in text_lower:
                    return "Data governance roles defined: Data Owners (VP level), Data Stewards (director level), Data Custodians (engineering managers). Roles communicated via org chart and quarterly data governance meetings."
                elif "committee" in text_lower or "body" in text_lower:
                    return "Data Governance Council meets monthly with representatives from Engineering, Legal, Privacy, Security, and Manufacturing. Council makes decisions on data classification, retention policies, and cross-functional data access."
                elif "conflict" in text_lower or "resolution" in text_lower:
                    return "Data ownership conflicts escalated to Data Governance Council. Most conflicts involve access to vehicle telemetry data between Autopilot team and Privacy team. Resolution process documented but can be slow."
                else:
                    return "Data governance structure established but still maturing. As company scales from startup to enterprise, governance processes are being formalized. Executive sponsorship strong, but implementation varies by department."
            
            # Metadata & Documentation
            elif "metadata" in dimension_lower or "documentation" in dimension_lower:
                if "search" in text_lower or "discover" in text_lower:
                    return "Internal data catalog allows search by dataset name, owner, or business domain. Catalog includes 200+ datasets but coverage incomplete. Engineering teams maintain their own documentation in Confluence."
                elif "integrated" in text_lower or "etl" in text_lower:
                    return "Metadata automatically captured from ETL pipelines using custom connectors. Data dictionary maintained in data catalog. Business metadata (definitions, owners) manually maintained and sometimes outdated."
                elif "business" in text_lower and "technical" in text_lower:
                    return "Business metadata (data definitions, business rules) linked to technical metadata (schema, data types) in data catalog. Linkage maintained manually by data stewards. Some gaps exist between business and technical views."
                else:
                    return "Metadata management improving but not comprehensive. Critical datasets well-documented, but many ad-hoc datasets lack proper metadata. Data documentation effort ongoing as part of data governance initiative."
            
            # Data Value & Lifecycle
            elif "value" in dimension_lower or "lifecycle" in dimension_lower:
                if "value" in text_lower or "assessed" in text_lower:
                    return "Business value of data assets assessed annually. Vehicle telemetry data highest value (drives Autopilot development). Manufacturing data critical for quality and cost optimization. Customer data valuable for service and sales."
                elif "lifecycle" in text_lower or "retaining" in text_lower or "disposing" in text_lower:
                    return "Data retention policies defined: Vehicle telemetry retained for 7 years, manufacturing data for 10 years, customer PII per legal requirements. Automated deletion processes in place but not fully tested for all data types."
                else:
                    return "Data lifecycle management formalized for critical datasets. Lifecycle policies documented but enforcement varies. Some legacy systems lack automated lifecycle management. Improvement project planned for next quarter."
            
            # Ethics & Bias - AI/ML focus
            elif "ethics" in dimension_lower or "bias" in text_lower:
                if "ai" in text_lower or "ml" in text_lower or "model" in text_lower:
                    return "Autopilot and FSD models undergo bias testing for different driving scenarios, weather conditions, and geographic regions. Model performance monitored for fairness across demographics. Ethical AI framework being developed with external advisors."
                elif "appeal" in text_lower or "decision" in text_lower:
                    return "No formal appeal mechanism for Autopilot decisions, but customer feedback on FSD behavior is collected and used to improve models. Safety-critical decisions (emergency braking) have override mechanisms."
                elif "reviewed" in text_lower or "practices" in text_lower:
                    return "Data collection practices reviewed quarterly by Privacy and Ethics team. Focus on minimizing unnecessary data collection while maintaining model performance. Some tension between data needs for AI development and privacy."
                else:
                    return "Ethical considerations integrated into AI development process. Bias testing mandatory before model deployment. Ethics training provided to ML engineers. External ethics advisory board consulted for major decisions."
            
            # Default - Context-aware generic comments
            else:
                if score >= 4:
                    return f"Strong practice in this area. {dimension} is well-managed with clear processes and regular monitoring. Aligned with EVTech's focus on data-driven manufacturing and AI development."
                elif score == 3:
                    return f"Standard practice in place with room for improvement. {dimension} management is adequate but could benefit from more formalization and automation as the organization scales."
                else:
                    return f"Area identified for improvement. {dimension} practices are basic and need enhancement. Planned improvements in next quarter as part of data governance maturity initiative."
        
        # Fill CXO responses
        print("   Filling CXO responses...")
        cxo_responses_count = 0
        for question in cxo_questions:
            existing = db.query(models.SurveyResponse).filter(
                models.SurveyResponse.survey_id == survey.id,
                models.SurveyResponse.user_id == cxo_user.id,
                models.SurveyResponse.question_id == question.id
            ).first()
            
            if not existing:
                score = get_tesla_score(question, question.dimension, question.category)
                comment = get_tesla_comment(question, question.dimension, score)
                
                response = models.SurveyResponse(
                    survey_id=survey.id,
                    user_id=cxo_user.id,
                    question_id=question.id,
                    score=str(score),
                    comment=comment[:200]
                )
                db.add(response)
                cxo_responses_count += 1
        
        db.commit()
        print(f"   ✓ Filled {cxo_responses_count} CXO responses")
        
        # Fill Participant responses
        print("   Filling Participant responses...")
        participant_responses_count = 0
        for participant in participant_users:
            for question in participant_questions:
                existing = db.query(models.SurveyResponse).filter(
                    models.SurveyResponse.survey_id == survey.id,
                    models.SurveyResponse.user_id == participant.id,
                    models.SurveyResponse.question_id == question.id
                ).first()
                
                if not existing:
                    score = get_tesla_score(question, question.dimension, question.category)
                    # Add some variation for participants
                    if random.random() > 0.7:
                        score = max(1, min(5, score + random.choice([-1, 0, 1])))
                    
                    # Always include a comment for detailed responses
                    comment = get_tesla_comment(question, question.dimension, score)
                    
                    response = models.SurveyResponse(
                        survey_id=survey.id,
                        user_id=participant.id,
                        question_id=question.id,
                        score=str(score),
                        comment=comment[:200] if comment else None
                    )
                    db.add(response)
                    participant_responses_count += 1
        
        db.commit()
        print(f"   ✓ Filled {participant_responses_count} Participant responses")
        
        # Step 6: Submit surveys
        print("\n[6/6] Submitting surveys...")
        
        # Submit CXO survey
        cxo_submission = db.query(models.UserSurveySubmission).filter(
            models.UserSurveySubmission.survey_id == survey.id,
            models.UserSurveySubmission.user_id == cxo_user.id
        ).first()
        
        if not cxo_submission:
            cxo_submission = models.UserSurveySubmission(
                survey_id=survey.id,
                user_id=cxo_user.id,
                submitted_at=func.now()
            )
            db.add(cxo_submission)
            print(f"   ✓ Submitted CXO survey")
        
        # Submit Participant surveys
        for participant in participant_users:
            submission = db.query(models.UserSurveySubmission).filter(
                models.UserSurveySubmission.survey_id == survey.id,
                models.UserSurveySubmission.user_id == participant.id
            ).first()
            
            if not submission:
                submission = models.UserSurveySubmission(
                    survey_id=survey.id,
                    user_id=participant.id,
                    submitted_at=func.now()
                )
                db.add(submission)
        
        # Update survey status
        survey.status = "Submitted"
        survey.submitted_at = func.now()
        
        db.commit()
        print(f"   ✓ Submitted all surveys")
        print(f"   ✓ Survey status: {survey.status}")
        
        # Summary
        print("\n" + "=" * 70)
        print("  EVTECH (EVTC) SURVEY DATA SUMMARY")
        print("=" * 70)
        print(f"Customer: {customer.name} (Code: {customer.customer_code})")
        print(f"Industry: {customer.industry}")
        print(f"Users: 1 CXO + {len(participant_users)} Participants + 1 Sales")
        print(f"Total Responses: {cxo_responses_count + participant_responses_count}")
        print(f"Survey Status: {survey.status}")
        print("\nLogin Credentials:")
        print(f"  CXO: ewhite / Welcome123!")
        print(f"  Participant 1: mthomas / Welcome123! (Maria Thomas)")
        print(f"  Participant 2: pjohnson / Welcome123! (Paul Johnson)")
        print(f"  Sales: Nagaraj / Welcome123!")
        print("\n✓ EVTech survey data created successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_tesla_data()

