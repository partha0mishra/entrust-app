#!/usr/bin/env python3
"""
Script to fill test data for major tech companies (MSFT, GOOG, AAPL, AMZN).
Creates customers, users, and fills survey responses for each company.
"""
import sys
import json
import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app import models, auth

# Company configurations
COMPANIES = [
    {
        "customer_code": "MSFT",
        "name": "Microsoft Corp",
        "industry": "Software",
        "location": "Redmond, WA",
        "description": "Microsoft Corporation is an American multinational technology conglomerate headquartered in Redmond, Washington.",
        "cxo": {
            "user_id": "snadella",
            "username": "Satya Nadella",
            "password": "Welcome123!"
        },
        "participants": [
            {"user_id": "ahood", "username": "Amy Hood"},
            {"user_id": "smehta", "username": "Satya Mehta"},
            {"user_id": "jphillips", "username": "Judson Phillips"},
            {"user_id": "kscott", "username": "Kevin Scott"},
            {"user_id": "bsmith", "username": "Brad Smith"}
        ]
    },
    {
        "customer_code": "GOOG",
        "name": "Alphabet Inc Class C",
        "industry": "Software",
        "location": "Mountain View, CA",
        "description": "Alphabet Inc. is an American multinational technology conglomerate holding company headquartered in Mountain View, California. Alphabet is the world's third-largest technology company by revenue, after Amazon and Apple, the largest technology company by profit, and one of the world's most valuable companies.",
        "cxo": {
            "user_id": "spichai",
            "username": "Sundar Pichai",
            "password": "Welcome123!"
        },
        "participants": [
            {"user_id": "rporat", "username": "Ruth Porat"},
            {"user_id": "pschindler", "username": "Philipp Schindler"},
            {"user_id": "jdean", "username": "Jeff Dean"},
            {"user_id": "pbraverman", "username": "Prabhakar Raghavan"},
            {"user_id": "twalker", "username": "Thomas Kurian"}
        ]
    },
    {
        "customer_code": "AAPL",
        "name": "Apple Inc",
        "industry": "Software",
        "location": "Cupertino, CA",
        "description": "Apple Inc. is an American multinational technology company headquartered in Cupertino, California, in Silicon Valley, best known for its consumer electronics, software and online services.",
        "cxo": {
            "user_id": "tcook",
            "username": "Tim Cook",
            "password": "Welcome123!"
        },
        "participants": [
            {"user_id": "lmaestri", "username": "Luca Maestri"},
            {"user_id": "jternus", "username": "Jeff Williams"},
            {"user_id": "dgiannandrea", "username": "Deirdre O'Brien"},
            {"user_id": "kknowling", "username": "Kate Adams"},
            {"user_id": "gsrouji", "username": "Johny Srouji"}
        ]
    },
    {
        "customer_code": "AMZN",
        "name": "Amazon.com Inc",
        "industry": "eCommerce",
        "location": "Seattle, WA",
        "description": "Amazon.com, Inc., doing business as Amazon, is an American multinational technology company engaged in e-commerce, cloud computing, online advertising, digital streaming, and artificial intelligence.",
        "cxo": {
            "user_id": "ajassy",
            "username": "Andy Jassy",
            "password": "Welcome123!"
        },
        "participants": [
            {"user_id": "bolsavsky", "username": "Brian Olsavsky"},
            {"user_id": "aselipsky", "username": "Adam Selipsky"},
            {"user_id": "dclark", "username": "Dave Clark"},
            {"user_id": "aherrington", "username": "Andy Herrington"},
            {"user_id": "jsassy", "username": "Jeff Wilke"}
        ]
    }
]

# Response templates by score range
HIGH_SCORES = [
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

MEDIUM_SCORES = [
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

LOW_SCORES = [
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


def create_company_data(db: Session, company_config: dict):
    """Create data for a single company"""
    company_name = company_config["name"]
    print(f"\n{'='*70}")
    print(f"  CREATING DATA FOR {company_name.upper()}")
    print(f"{'='*70}")

    # Step 1: Create customer
    print(f"\n[1/6] Creating customer {company_config['customer_code']}...")
    customer = db.query(models.Customer).filter(
        models.Customer.customer_code == company_config["customer_code"]
    ).first()

    if not customer:
        customer = models.Customer(
            customer_code=company_config["customer_code"],
            name=company_config["name"],
            industry=company_config["industry"],
            location=company_config["location"],
            description=company_config["description"]
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"✓ Created customer: {customer.name} (ID: {customer.id})")
    else:
        print(f"✓ Customer already exists: {customer.name} (ID: {customer.id})")

    # Step 2: Create CXO user
    print(f"\n[2/6] Creating CXO user...")
    cxo_config = company_config["cxo"]
    cxo_user = db.query(models.User).filter(
        models.User.user_id == cxo_config["user_id"]
    ).first()

    if not cxo_user:
        cxo_user = models.User(
            user_id=cxo_config["user_id"],
            username=cxo_config["username"],
            password_hash=auth.get_password_hash(cxo_config["password"]),
            password=auth.encrypt_password(cxo_config["password"]),
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

    # Step 3: Create Participant users
    print(f"\n[3/6] Creating participant users...")
    participant_users = []

    for participant_config in company_config["participants"]:
        participant = db.query(models.User).filter(
            models.User.user_id == participant_config["user_id"]
        ).first()

        if not participant:
            participant = models.User(
                user_id=participant_config["user_id"],
                username=participant_config["username"],
                password_hash=auth.get_password_hash("Welcome123!"),
                password=auth.encrypt_password("Welcome123!"),
                user_type=models.UserType.PARTICIPANT,
                customer_id=customer.id
            )
            db.add(participant)
            db.commit()
            db.refresh(participant)
            print(f"✓ Created Participant: {participant.username} (ID: {participant.id})")
        else:
            participant.customer_id = customer.id
            db.commit()
            print(f"✓ Participant exists: {participant.username} (ID: {participant.id})")

        participant_users.append(participant)

    # Step 4: Create survey
    print(f"\n[4/6] Creating survey...")
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

    # Step 5: Get all questions
    print(f"\n[5/6] Loading questions...")
    all_questions = db.query(models.Question).all()
    print(f"✓ Found {len(all_questions)} questions")

    # Get CXO questions
    cxo_questions = [q for q in all_questions if q.question_type == 'CXO']
    print(f"   - CXO questions: {len(cxo_questions)}")

    # Get Participant questions (all questions)
    participant_questions = all_questions
    print(f"   - Participant questions: {len(participant_questions)}")

    # Step 6: Fill responses
    print(f"\n[6/6] Filling survey responses...")

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
                comment = f"{random.choice(HIGH_SCORES)}"
            elif score > 4:
                comment = f"{random.choice(MEDIUM_SCORES)}"
            else:
                comment = f"{random.choice(LOW_SCORES)}"

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
                    comment = f"{random.choice(HIGH_SCORES)}"
                elif score > 4:
                    comment = f"{random.choice(MEDIUM_SCORES)}"
                else:
                    comment = f"{random.choice(LOW_SCORES)}"

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

    # Step 7: Submit surveys
    print(f"\n[7/7] Submitting surveys...")

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
    print(f"\n{'='*70}")
    print(f"  SUMMARY FOR {company_name.upper()}")
    print(f"{'='*70}")
    print(f"Customer: {customer.name} (Code: {customer.customer_code})")
    print(f"Industry: {customer.industry}")
    print(f"Location: {customer.location}")
    print(f"Users: 1 CXO + {len(participant_users)} Participants")
    print(f"Total Responses: {cxo_responses_count + participant_responses_count}")
    print(f"Survey Status: {survey.status}")
    print(f"\nLogin Credentials:")
    print(f"  CXO: {cxo_config['user_id']} / {cxo_config['password']} ({cxo_config['username']})")
    for p in company_config["participants"]:
        print(f"  Participant: {p['user_id']} / Welcome123! ({p['username']})")
    print(f"\n✓ Data for {company_name} created successfully!")
    print(f"{'='*70}")


def create_all_companies_data():
    """Create data for all companies"""
    db = SessionLocal()

    try:
        print(f"\n{'='*70}")
        print(f"  CREATING DATA FOR MAJOR TECH COMPANIES")
        print(f"  Companies: MSFT, GOOG, AAPL, AMZN")
        print(f"{'='*70}")

        for company_config in COMPANIES:
            # Check if customer already exists with complete data
            existing_customer = db.query(models.Customer).filter(
                models.Customer.customer_code == company_config["customer_code"]
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
                        print(f"\n✓ {company_config['name']} data already exists and is complete!")
                        print(f"   Customer: {existing_customer.name}")
                        print(f"   Survey Status: {completed_survey.status}")
                        print(f"   Responses: {response_count}")
                        print(f"⏩ Skipping. Use --force to recreate.")
                        continue

            # Create data for this company
            create_company_data(db, company_config)

        print(f"\n{'='*70}")
        print(f"  ALL COMPANIES DATA CREATION COMPLETE")
        print(f"{'='*70}")
        print(f"\n✓ Successfully created data for all companies!")
        print(f"{'='*70}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fill database with major tech companies test data")
    parser.add_argument('--force', action='store_true',
                        help='Force recreate test data even if it already exists')
    args = parser.parse_args()

    # If force flag is set, delete existing data for all companies
    if args.force:
        db = SessionLocal()
        try:
            print(f"\n🗑️  Force mode: Deleting existing data for MSFT, GOOG, AAPL, AMZN...")

            for company_config in COMPANIES:
                customer = db.query(models.Customer).filter(
                    models.Customer.customer_code == company_config["customer_code"]
                ).first()

                if customer:
                    print(f"   Deleting data for {company_config['name']}...")

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
                    print(f"   ✓ Deleted data for {company_config['name']}")
                else:
                    print(f"   ⚠ No existing data found for {company_config['name']}")

            print("✓ All existing data deleted.\n")
        except Exception as e:
            print(f"✗ Error deleting data: {e}")
            db.rollback()
        finally:
            db.close()

    create_all_companies_data()
