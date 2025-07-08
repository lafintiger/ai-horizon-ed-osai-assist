#!/usr/bin/env python3
"""
Test script to verify production data deployment
"""
import os
from app import app, db, QuizQuestion, EducationalResource, EmergingSkill

def test_production_data():
    with app.app_context():
        # Get data counts
        quiz_count = QuizQuestion.query.count()
        resource_count = EducationalResource.query.count()
        skill_count = EmergingSkill.query.count()
        resource_49_quiz = QuizQuestion.query.filter_by(resource_id=49).count()
        
        print(f"📊 Total Quiz Questions: {quiz_count}")
        print(f"📚 Total Resources: {resource_count}")
        print(f"🎯 Total Skills: {skill_count}")
        print(f"✅ Resource 49 Quiz Questions: {resource_49_quiz}")
        
        # Test if our key features exist
        if resource_49_quiz == 5:
            print("✅ Resource 49 quiz successfully fixed!")
        else:
            print(f"❌ Resource 49 quiz issue: expected 5, got {resource_49_quiz}")
        
        if quiz_count >= 46:
            print("✅ Quiz standardization appears successful!")
        else:
            print(f"❌ Quiz count issue: expected 46+, got {quiz_count}")

if __name__ == "__main__":
    test_production_data() 