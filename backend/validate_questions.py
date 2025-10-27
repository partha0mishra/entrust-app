"""
Validate that questions have been updated correctly
Check that process and lifecycle_stage fields are populated
Run: docker exec -it entrust_backend python validate_questions.py
"""

from app.database import SessionLocal
from app import models

def validate_questions():
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("Question Update Validation")
        print("=" * 80)
        
        total_questions = db.query(models.Question).count()
        print(f"\n📊 Total questions in database: {total_questions}\n")
        
        # Check for process field
        questions_with_process = db.query(models.Question).filter(
            models.Question.process.isnot(None)
        ).count()
        
        # Check for lifecycle_stage field
        questions_with_lifecycle = db.query(models.Question).filter(
            models.Question.lifecycle_stage.isnot(None)
        ).count()
        
        # Check for category field
        questions_with_category = db.query(models.Question).filter(
            models.Question.category.isnot(None)
        ).count()
        
        # Check for question_type field
        questions_with_type = db.query(models.Question).filter(
            models.Question.question_type.isnot(None)
        ).count()
        
        print("✅ Field Population Status:")
        print(f"   • Questions with 'category': {questions_with_category} ({questions_with_category/total_questions*100:.1f}%)")
        print(f"   • Questions with 'question_type': {questions_with_type} ({questions_with_type/total_questions*100:.1f}%)")
        print(f"   • Questions with 'process': {questions_with_process} ({questions_with_process/total_questions*100:.1f}%)")
        print(f"   • Questions with 'lifecycle_stage': {questions_with_lifecycle} ({questions_with_lifecycle/total_questions*100:.1f}%)")
        
        # Check for NULL values
        null_process = db.query(models.Question).filter(
            models.Question.process.is_(None)
        ).count()
        
        null_lifecycle = db.query(models.Question).filter(
            models.Question.lifecycle_stage.is_(None)
        ).count()
        
        print("\n⚠️  Field Gaps:")
        print(f"   • Questions with NULL 'process': {null_process}")
        print(f"   • Questions with NULL 'lifecycle_stage': {null_lifecycle}")
        
        # Show some sample questions with new fields
        print("\n📝 Sample Questions with New Fields:")
        print("-" * 80)
        samples = db.query(models.Question).filter(
            models.Question.process.isnot(None),
            models.Question.lifecycle_stage.isnot(None)
        ).limit(5).all()
        
        for q in samples:
            print(f"\nQuestion ID: {q.question_id}")
            print(f"  Text: {q.text[:80]}...")
            print(f"  Dimension: {q.dimension}")
            print(f"  Category: {q.category}")
            print(f"  Question Type: {q.question_type}")
            print(f"  Process: {q.process}")
            print(f"  Lifecycle Stage: {q.lifecycle_stage}")
        
        # Summary by dimension
        print("\n\n📈 Questions by Dimension and Type:")
        print("-" * 80)
        dimensions = db.query(models.Question.dimension).distinct().all()
        
        print("Dimension".ljust(40) + "Total".rjust(8) + "CXO".rjust(8) + "General".rjust(10))
        print("-" * 80)
        
        for (dimension,) in dimensions:
            total_count = db.query(models.Question).filter(
                models.Question.dimension == dimension
            ).count()
            
            cxo_count = db.query(models.Question).filter(
                models.Question.dimension == dimension,
                models.Question.question_type == "CXO"
            ).count()
            
            general_count = db.query(models.Question).filter(
                models.Question.dimension == dimension,
                models.Question.question_type == "General"
            ).count()
            
            print(
                dimension.ljust(40) + 
                str(total_count).rjust(8) + 
                str(cxo_count).rjust(8) + 
                str(general_count).rjust(10)
            )
        
        # Grouped query: Count questions by Dimension, Category, Process, and Lifecycle Stage
        print("\n\n📊 Questions grouped by Dimension, Category, Process, and Lifecycle Stage:")
        print("=" * 80)
        
        from sqlalchemy import func
        
        grouped_results = db.query(
            models.Question.dimension,
            models.Question.category,
            models.Question.process,
            models.Question.lifecycle_stage,
            func.count(models.Question.id).label('count')
        ).group_by(
            models.Question.dimension,
            models.Question.category,
            models.Question.process,
            models.Question.lifecycle_stage
        ).order_by(
            models.Question.dimension,
            models.Question.category,
            models.Question.process
        ).all()
        
        if grouped_results:
            print(f"\nFound {len(grouped_results)} unique combinations\n")
            print("Dimension".ljust(30) + "Category".ljust(30) + "Process".ljust(30) + "Lifecycle".ljust(25) + "Count".rjust(8))
            print("-" * 140)
            
            for dim, cat, proc, life, count in grouped_results:
                print(
                    (dim or "N/A")[:28].ljust(30) + 
                    (cat or "N/A")[:28].ljust(30) + 
                    (proc or "N/A")[:28].ljust(30) + 
                    (life or "N/A")[:23].ljust(25) + 
                    str(count).rjust(8)
                )
        else:
            print("No grouped results found.")
        
        # Final validation
        print("\n" + "=" * 80)
        if questions_with_process == total_questions and questions_with_lifecycle == total_questions:
            print("✅ VALIDATION PASSED: All questions have been updated!")
        else:
            print("⚠️  VALIDATION WARNING: Some questions may not be updated.")
            print(f"   Missing process: {null_process}")
            print(f"   Missing lifecycle_stage: {null_lifecycle}")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    validate_questions()

