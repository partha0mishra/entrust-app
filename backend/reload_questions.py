"""
Update question fields from questions.json
This will update category, question_type, process, and lifecycle_stage based on question_id
Run: docker exec -it entrust_backend python reload_questions.py
"""

import json
from app.database import SessionLocal
from app import models

def update_questions():
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("Update Questions from questions.json")
        print("=" * 80)
        
        # Check current question count
        current_count = db.query(models.Question).count()
        print(f"\n📊 Current questions in database: {current_count}")
        
        # Load questions from JSON
        print("\n📥 Loading questions from questions.json...")
        try:
            with open('questions.json', 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
            
            print(f"Found {len(questions_data)} questions in file.")
            
            updated_count = 0
            not_found_count = 0
            
            for q in questions_data:
                # Find existing question by question_id
                existing = db.query(models.Question).filter(
                    models.Question.question_id == q['id']
                ).first()
                
                if existing:
                    # Update the fields
                    existing.category = q.get('category')
                    existing.question_type = q.get('question_type')
                    existing.process = q.get('process')
                    existing.lifecycle_stage = q.get('lifecycle_stage')
                    
                    updated_count += 1
                    
                    # Commit in batches of 100
                    if updated_count % 100 == 0:
                        db.commit()
                        print(f"   Processed {updated_count} questions...")
                else:
                    not_found_count += 1
            
            db.commit()
            print(f"\n✅ Updated {updated_count} questions!")
            
            if not_found_count > 0:
                print(f"⚠️  {not_found_count} questions from JSON not found in database.")
            
            # Show summary
            total = db.query(models.Question).count()
            print(f"\n📊 Total questions in database: {total}")
            
            # Show dimension summary
            print("\n📈 Questions by Dimension:")
            dimensions = db.query(models.Question.dimension).distinct().all()
            for dim in dimensions:
                count = db.query(models.Question).filter(
                    models.Question.dimension == dim[0]
                ).count()
                print(f"   • {dim[0]}: {count} questions")
            
            # Show question type summary
            print("\n📊 Questions by Type:")
            types = db.query(models.Question.question_type).distinct().all()
            for qtype in types:
                if qtype[0]:  # Skip None values
                    count = db.query(models.Question).filter(
                        models.Question.question_type == qtype[0]
                    ).count()
                    print(f"   • {qtype[0]}: {count} questions")
            
        except FileNotFoundError:
            print("❌ ERROR: questions.json file not found!")
            print("   Please place questions.json in the backend directory.")
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Invalid JSON in questions.json: {e}")
        except Exception as e:
            print(f"❌ ERROR loading questions: {e}")
            db.rollback()
            raise
        
        print("\n" + "=" * 80)
        print("✅ Questions update completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error updating questions: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_questions()

