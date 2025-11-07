#!/usr/bin/env python3
"""
Script to fill test Q&A data for report generation testing.
Creates a customer, users, and fills survey responses.
"""
import sys
import json
import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app import models, auth

def create_test_data():
    """Create test customer, users, and fill survey responses"""
    db = SessionLocal()

    try:
        print("=" * 70)
        print("  CREATING TEST DATA FOR REPORT GENERATION")
        print("=" * 70)

        # Quick check: if NVIDIA customer exists and has a completed survey, skip
        existing_customer = db.query(models.Customer).filter(
            models.Customer.customer_code == "NVDA"
        ).first()

        if existing_customer:
            completed_survey = db.query(models.Survey).filter(
                models.Survey.customer_id == existing_customer.id,
                models.Survey.status == "Submitted"
            ).first()

            if completed_survey:
                response_count = db.query(models.SurveyResponse).filter(
                    models.SurveyResponse.survey_id == completed_survey.id
                ).count()

                if response_count > 0:
                    print("\n✓ NVIDIA test data already exists and is complete!")
                    print(f"   Customer: {existing_customer.name}")
                    print(f"   Survey Status: {completed_survey.status}")
                    print(f"   Responses: {response_count}")
                    print("\n⏩ Skipping test data creation. Use --force to recreate.")
                    print("=" * 70)
                    return

        # Step 1: Create test customer
        print("\n[1/5] Creating test customer...")
        customer = db.query(models.Customer).filter(
            models.Customer.customer_code == "NVDA"
        ).first()

        if not customer:
            customer = models.Customer(
                customer_code="NVDA",
                name="NVIDIA",
                industry="High Tech",
                location="Santa Clara, CA",
                description="Nvidia Corporation is an American technology company headquartered in Santa Clara, California. Founded in 1993 by Jensen Huang, Chris Malachowsky, and Curtis Priem"
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            print(f"✓ Created customer: {customer.name} (ID: {customer.id})")
        else:
            print(f"✓ Customer already exists: {customer.name} (ID: {customer.id})")
        
        # Step 2: Create test users
        print("\n[2/5] Creating test users...")

        # Create CXO user (Jensen Huang)
        cxo_user = db.query(models.User).filter(
            models.User.user_id == "jhuang"
        ).first()

        if not cxo_user:
            cxo_password = "Welcome123!"
            cxo_user = models.User(
                user_id="jhuang",
                username="Jensen Huang",
                password_hash=auth.get_password_hash(cxo_password),
                password=auth.encrypt_password(cxo_password),
                user_type=models.UserType.CXO,
                customer_id=customer.id
            )
            db.add(cxo_user)
            db.commit()
            db.refresh(cxo_user)
            print(f"✓ Created CXO user: {cxo_user.username} (ID: {cxo_user.id})")
        else:
            cxo_user.customer_id = customer.id
            db.commit()
            print(f"✓ CXO user exists: {cxo_user.username} (ID: {cxo_user.id})")
        
        # Create Participant users
        participant_users = []

        # Participant 1: Partha Mishra
        partha = db.query(models.User).filter(
            models.User.user_id == "Partha"
        ).first()

        if not partha:
            partha_password = "Welcome123!"
            partha = models.User(
                user_id="Partha",
                username="Partha Mishra",
                password_hash=auth.get_password_hash(partha_password),
                password=auth.encrypt_password(partha_password),
                user_type=models.UserType.PARTICIPANT,
                customer_id=customer.id
            )
            db.add(partha)
            db.commit()
            db.refresh(partha)
            print(f"✓ Created Participant: {partha.username} (ID: {partha.id})")
        else:
            partha.customer_id = customer.id
            db.commit()
            print(f"✓ Participant exists: {partha.username} (ID: {partha.id})")

        participant_users.append(partha)

        # Participant 2: Madhu Ivaturi
        madhu = db.query(models.User).filter(
            models.User.user_id == "Madhu"
        ).first()

        if not madhu:
            madhu_password = "Welcome123!"
            madhu = models.User(
                user_id="Madhu",
                username="Madhu Ivaturi",
                password_hash=auth.get_password_hash(madhu_password),
                password=auth.encrypt_password(madhu_password),
                user_type=models.UserType.PARTICIPANT,
                customer_id=customer.id
            )
            db.add(madhu)
            db.commit()
            db.refresh(madhu)
            print(f"✓ Created Participant: {madhu.username} (ID: {madhu.id})")
        else:
            madhu.customer_id = customer.id
            db.commit()
            print(f"✓ Participant exists: {madhu.username} (ID: {madhu.id})")

        participant_users.append(madhu)

        # Sales user: Nagaraj Sastry (no customer association)
        nagaraj = db.query(models.User).filter(
            models.User.user_id == "Nagaraj"
        ).first()

        if not nagaraj:
            nagaraj_password = "Welcome123!"
            nagaraj = models.User(
                user_id="Nagaraj",
                username="Nagaraj Sastry",
                password_hash=auth.get_password_hash(nagaraj_password),
                password=auth.encrypt_password(nagaraj_password),
                user_type=models.UserType.SALES,
                customer_id=None  # Sales users are not tied to a specific customer
            )
            db.add(nagaraj)
            db.commit()
            db.refresh(nagaraj)
            print(f"✓ Created Sales user: {nagaraj.username} (ID: {nagaraj.id})")
        else:
            print(f"✓ Sales user exists: {nagaraj.username} (ID: {nagaraj.id})")
        
        # Step 3: Create survey
        print("\n[3/5] Creating survey...")
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
        print("\n[4/5] Loading questions...")
        all_questions = db.query(models.Question).all()
        print(f"✓ Found {len(all_questions)} questions")
        
        # Get CXO questions
        cxo_questions = [q for q in all_questions if q.question_type == 'CXO']
        print(f"   - CXO questions: {len(cxo_questions)}")
        
        # Get Participant questions (all questions)
        participant_questions = all_questions
        print(f"   - Participant questions: {len(participant_questions)}")
        
        # Step 5: Fill responses
        print("\n[5/5] Filling survey responses...")

        # Scores > 7  (Strong performance — mature and effective governance)
        high_scores = [
            "Operating effectively and aligned with data governance standards",
            "Practices are well-established and consistently applied across domains",
            "Strong evidence of mature data management and oversight",
            "Demonstrates adherence to enterprise and regulatory requirements",
            "Processes are stable, repeatable, and continuously improved",
            "Governance controls are well-defined and actively monitored",
            "Data quality and security frameworks are fully operational",
            "Roles and responsibilities are clearly defined and enforced",
            "Policies are effectively communicated and integrated in operations",
            "High compliance with data privacy and protection standards",
            "Data lineage is transparent, complete, and routinely validated",
            "Metadata management practices are standardized and reliable",
            "Governance framework is embedded into business-as-usual activities",
            "Decision-making is supported by trusted and well-governed data",
            "Demonstrates proactive data stewardship across business units",
            "Evidence of continuous improvement and governance maturity",
            "Risk management practices are effective and consistently applied",
            "Audit results indicate strong control performance and documentation",
            "Processes align well with industry best practices and frameworks",
            "Cross-functional collaboration on governance is strong and sustained",
            "Performance metrics are tracked, reported, and acted upon regularly",
            "Governance tools and technologies are fully leveraged and maintained",
            "Stakeholder awareness and engagement are high and sustained",
            "Data governance culture is mature and well-integrated",
            "Governance capabilities are scalable and adaptable to new domains",
            "Governance documentation is comprehensive and up to date",
            "Performance reflects accountability and ownership at all levels",
            "Data governance objectives are met or exceeded consistently",
            "Well-positioned to serve as a reference model for other domains",
            "Overall governance performance is strong and sustainable"
        ]

        # Scores between 5 and 7  (Moderate performance — improvement opportunities)
        medium_scores = [
            "Governance practices are functional but inconsistently applied",
            "Some policies are documented, but enforcement varies across units",
            "Processes meet basic standards but lack maturity in execution",
            "Governance framework is emerging but not yet enterprise-wide",
            "Operational practices require further standardization and clarity",
            "Roles and responsibilities are defined but not consistently followed",
            "Monitoring and reporting mechanisms could be more robust",
            "Data quality controls are implemented but lack comprehensive coverage",
            "Privacy and security compliance are generally maintained but need tightening",
            "Lineage tracking exists but requires greater completeness and automation",
            "Metadata standards are partially implemented across systems",
            "Evidence of governance awareness, though adoption is uneven",
            "Processes rely heavily on manual intervention or local practices",
            "Audit findings suggest room for procedural refinement",
            "Governance-related KPIs are defined but not consistently measured",
            "Policy updates and version control could be better managed",
            "Cross-departmental collaboration is present but needs reinforcement",
            "Technology enablement is partial and underutilized",
            "Communication of governance priorities could be improved",
            "Data stewardship roles are defined but lack full engagement",
            "Governance practices are reactive rather than proactive",
            "Training and awareness programs need broader participation",
            "Data lifecycle management could be more systematically enforced",
            "Evidence of improvement initiatives, though progress is incremental",
            "Process documentation exists but lacks sufficient depth or accuracy",
            "Data issue resolution is effective but not timely in all cases",
            "Governance alignment with business strategy is partial",
            "Some legacy practices limit full governance effectiveness",
            "Better integration between governance and technology platforms is needed",
            "Overall performance is adequate but not optimized"
        ]

        # Scores < 5  (Weak performance — requires focused remediation)
        low_scores = [
            "Area requires significant improvement to meet governance objectives",
            "Governance framework is largely informal or ad hoc in nature",
            "Limited ownership or accountability for data management practices",
            "Policies are missing, outdated, or inconsistently applied",
            "Insufficient documentation and unclear process definitions",
            "High variability in governance maturity across departments",
            "Evidence of compliance gaps and unmanaged risks",
            "Weak alignment between governance goals and operational practices",
            "Controls are either absent or ineffective in key areas",
            "Data quality issues are frequent and unresolved over time",
            "Privacy and security measures do not meet baseline expectations",
            "Metadata is incomplete or not maintained systematically",
            "Lineage visibility is poor or nonexistent across critical systems",
            "No formal mechanism for monitoring or continuous improvement",
            "Governance reporting is irregular or not data-driven",
            "Training and awareness efforts are minimal or nonexistent",
            "Roles and responsibilities are unclear or unassigned",
            "Significant reliance on manual processes with limited oversight",
            "Audit findings indicate critical nonconformities or control failures",
            "Stakeholder engagement in governance is limited or absent",
            "Technology tools for governance are not implemented or outdated",
            "Governance processes lack scalability and adaptability",
            "Data ownership and accountability are not well established",
            "Risk and issue management processes are informal and undocumented",
            "No structured approach to policy enforcement or compliance validation",
            "Governance culture is weak and lacks organizational commitment",
            "Information silos hinder consistent governance application",
            "Remediation activities are reactive and lack sustainability",
            "Lack of centralized governance structure or steering oversight",
            "Immediate action required to establish foundational governance controls"
        ]
        
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
                # Random score between 1-10
                score = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
                if score > 7:  
                    comment = f"{random.choice(high_scores)}"
                elif score > 4:
                    comment = f"{random.choice(medium_scores)}"
                else:
                    comment = f"{random.choice(low_scores)}"
                
                response = models.SurveyResponse(
                    survey_id=survey.id,
                    user_id=cxo_user.id,
                    question_id=question.id,
                    score=score,
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
                    # Random score between 1-10
                    score = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
                    if score > 7:  
                        comment = f"{random.choice(high_scores)}"
                    elif score > 4:
                        comment = f"{random.choice(medium_scores)}"
                    else:
                        comment = f"{random.choice(low_scores)}"
                    
                    response = models.SurveyResponse(
                        survey_id=survey.id,
                        user_id=participant.id,
                        question_id=question.id,
                        score=score,
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
        print("  TEST DATA SUMMARY")
        print("=" * 70)
        print(f"Customer: {customer.name} (Code: {customer.customer_code})")
        print(f"Industry: {customer.industry}")
        print(f"Location: {customer.location}")
        print(f"Users: 1 CXO + {len(participant_users)} Participants + 1 Sales")
        print(f"Total Responses: {cxo_responses_count + participant_responses_count}")
        print(f"Survey Status: {survey.status}")
        print("\nLogin Credentials:")
        print(f"  CXO: jhuang / Welcome123! (Jensen Huang)")
        print(f"  Participant: Partha / Welcome123! (Partha Mishra)")
        print(f"  Participant: Madhu / Welcome123! (Madhu Ivaturi)")
        print(f"  Sales: Nagaraj / Welcome123! (Nagaraj Sastry)")
        print("\n✓ Test data created successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fill database with NVIDIA test data")
    parser.add_argument('--force', action='store_true',
                        help='Force recreate test data even if it already exists')
    args = parser.parse_args()

    # If force flag is set, delete existing NVIDIA data
    if args.force:
        db = SessionLocal()
        try:
            print("\n🗑️  Force mode: Deleting existing NVIDIA data...")
            customer = db.query(models.Customer).filter(
                models.Customer.customer_code == "NVDA"
            ).first()

            if customer:
                # Delete surveys (cascade will delete responses)
                surveys = db.query(models.Survey).filter(
                    models.Survey.customer_id == customer.id
                ).all()
                for survey in surveys:
                    db.delete(survey)

                # Delete users
                users = db.query(models.User).filter(
                    models.User.customer_id == customer.id
                ).all()
                for user in users:
                    db.delete(user)

                # Delete customer
                db.delete(customer)
                db.commit()
                print("✓ Existing NVIDIA data deleted.\n")
            else:
                print("⚠ No existing NVIDIA data found.\n")
        except Exception as e:
            print(f"✗ Error deleting data: {e}")
            db.rollback()
        finally:
            db.close()

    create_test_data()

