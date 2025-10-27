"""
Query script to get question counts by dimension and question_type
Run: docker exec -it entrust_backend python query_questions.py
"""

from sqlalchemy import func
from app.database import SessionLocal
from app import models

def query_questions():
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("Question Analysis by Dimension and Type")
        print("=" * 80)
        
        # Get total questions count
        total = db.query(models.Question).count()
        print(f"\n📊 Total Questions: {total}\n")
        
        # Get all unique dimensions
        dimensions = db.query(models.Question.dimension).distinct().all()
        
        # Create header
        print("Dimension".ljust(40) + "Total".rjust(8) + "CXO".rjust(8) + "General".rjust(10))
        print("-" * 80)
        
        # Query each dimension
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
            
            # Print formatted row
            print(
                dimension.ljust(40) + 
                str(total_count).rjust(8) + 
                str(cxo_count).rjust(8) + 
                str(general_count).rjust(10)
            )
        
        print("-" * 80)
        
        # Summary statistics
        total_cxo = db.query(models.Question).filter(
            models.Question.question_type == "CXO"
        ).count()
        
        total_general = db.query(models.Question).filter(
            models.Question.question_type == "General"
        ).count()
        
        other_types = db.query(models.Question).filter(
            ~models.Question.question_type.in_(["CXO", "General"])
        ).count()
        
        print(
            "SUMMARY".ljust(40) + 
            str(total).rjust(8) + 
            str(total_cxo).rjust(8) + 
            str(total_general).rjust(10)
        )
        
        print("\n" + "=" * 80)
        print("📈 Summary Statistics:")
        print(f"   Total Questions: {total}")
        print(f"   CXO Questions: {total_cxo}")
        print(f"   General Questions: {total_general}")
        print(f"   Other Types: {other_types}")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    query_questions()

