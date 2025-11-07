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
        
        # Step 1: Create test customer
        print("\n[1/5] Creating test customer...")
        customer = db.query(models.Customer).filter(
            models.Customer.customer_code == "TEST001"
        ).first()
        
        if not customer:
            customer = models.Customer(
                customer_code="TEST001",
                name="Test Company Inc.",
                industry="Technology",
                location="San Francisco, CA",
                description="Test customer for report generation"
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            print(f"✓ Created customer: {customer.name} (ID: {customer.id})")
        else:
            print(f"✓ Customer already exists: {customer.name} (ID: {customer.id})")
        
        # Step 2: Create test users
        print("\n[2/5] Creating test users...")
        
        # Create CXO user
        cxo_user = db.query(models.User).filter(
            models.User.user_id == "test_cxo"
        ).first()
        
        if not cxo_user:
            cxo_password = "test123"
            cxo_user = models.User(
                user_id="test_cxo",
                username="Test CXO",
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
        for i in range(1, 4):  # Create 3 participants
            participant_id = f"test_participant_{i}"
            participant = db.query(models.User).filter(
                models.User.user_id == participant_id
            ).first()
            
            if not participant:
                part_password = "test123"
                participant = models.User(
                    user_id=participant_id,
                    username=f"Test Participant {i}",
                    password_hash=auth.get_password_hash(part_password),
                    password=auth.encrypt_password(part_password),
                    user_type=models.UserType.PARTICIPANT,
                    customer_id=customer.id
                )
                db.add(participant)
                db.commit()
                db.refresh(participant)
                print(f"✓ Created Participant {i}: {participant.username} (ID: {participant.id})")
            else:
                participant.customer_id = customer.id
                db.commit()
                print(f"✓ Participant {i} exists: {participant.username} (ID: {participant.id})")
            
            participant_users.append(participant)
        
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
                # Random score between 1-5
                score = random.choice([1, 2, 3, 4, 5])
                comment = f"CXO response: {random.choice(['Good', 'Needs improvement', 'Excellent', 'Average'])}"
                
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
                    # Random score between 1-5
                    score = random.choice([1, 2, 3, 4, 5])
                    # Some questions with comments
                    if random.random() > 0.7:  # 30% chance of comment
                        comment = f"Participant note: {random.choice(['Area needs attention', 'Working well', 'Could be improved', 'Standard practice'])}"
                    else:
                        comment = None
                    
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
        print(f"Users: 1 CXO + {len(participant_users)} Participants")
        print(f"Total Responses: {cxo_responses_count + participant_responses_count}")
        print(f"Survey Status: {survey.status}")
        print("\nLogin Credentials:")
        print(f"  CXO: test_cxo / test123")
        print(f"  Participant 1: test_participant_1 / test123")
        print(f"  Participant 2: test_participant_2 / test123")
        print(f"  Participant 3: test_participant_3 / test123")
        print("\n✓ Test data created successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()

