#!/usr/bin/env python3
"""
Comprehensive data synchronization script for AI-Horizon Ed Platform
Exports all local data and imports it to production (Heroku)
"""

import json
import sys
from datetime import datetime
from app import app, db, EmergingSkill, EducationalResource, SkillLearningPath, QuizQuestion, PracticalAssignment, LearningSession

def export_all_data():
    """Export all data from local database"""
    
    with app.app_context():
        print("🔄 Exporting all local data...")
        
        # Export skills
        skills = EmergingSkill.query.all()
        skills_data = []
        for skill in skills:
            skills_data.append({
                'id': skill.id,
                'skill_name': skill.skill_name,
                'description': skill.description,
                'category': skill.category,
                'urgency_score': skill.urgency_score,
                'market_demand_evidence': skill.market_demand_evidence,
                'created_date': skill.created_date.isoformat() if skill.created_date else None,
                'last_updated': skill.last_updated.isoformat() if skill.last_updated else None,
                'status': skill.status,
                'source': skill.source
            })
        
        # Export resources
        resources = EducationalResource.query.all()
        resources_data = []
        for resource in resources:
            resources_data.append({
                'id': resource.id,
                'title': resource.title,
                'description': resource.description,
                'url': resource.url,
                'resource_type': resource.resource_type,
                'difficulty_level': resource.difficulty_level,
                'estimated_duration_minutes': resource.estimated_duration_minutes,
                'quality_score': resource.quality_score,
                'ai_analysis_summary': resource.ai_analysis_summary,
                'transcript': resource.transcript,
                'created_date': resource.created_date.isoformat() if resource.created_date else None,
                'last_analyzed': resource.last_analyzed.isoformat() if resource.last_analyzed else None,
                'status': resource.status
            })
        
        # Export learning paths
        learning_paths = SkillLearningPath.query.all()
        learning_paths_data = []
        for path in learning_paths:
            learning_paths_data.append({
                'id': path.id,
                'skill_id': path.skill_id,
                'resource_id': path.resource_id,
                'sequence_order': path.sequence_order,
                'path_type': path.path_type,
                'is_required': path.is_required,
                'created_date': path.created_date.isoformat() if path.created_date else None
            })
        
        # Export quiz questions
        quiz_questions = QuizQuestion.query.all()
        quiz_data = []
        for question in quiz_questions:
            quiz_data.append({
                'id': question.id,
                'resource_id': question.resource_id,
                'question_text': question.question_text,
                'option_a': question.option_a,
                'option_b': question.option_b,
                'option_c': question.option_c,
                'option_d': question.option_d,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation,
                'created_date': question.created_date.isoformat() if question.created_date else None
            })
        
        # Export practical assignments
        assignments = PracticalAssignment.query.all()
        assignments_data = []
        for assignment in assignments:
            assignments_data.append({
                'id': assignment.id,
                'resource_id': assignment.resource_id,
                'assignment_title': assignment.assignment_title,
                'assignment_description': assignment.assignment_description,
                'assignment_type': assignment.assignment_type,
                'estimated_time_minutes': assignment.estimated_time_minutes,
                'created_date': assignment.created_date.isoformat() if assignment.created_date else None
            })
        
        # Compile all data
        export_data = {
            'export_date': datetime.now().isoformat(),
            'source': 'local_database',
            'version': '2.0.0',
            'skills': skills_data,
            'resources': resources_data,
            'learning_paths': learning_paths_data,
            'quiz_questions': quiz_data,
            'practical_assignments': assignments_data,
            'summary': {
                'total_skills': len(skills_data),
                'total_resources': len(resources_data),
                'total_learning_paths': len(learning_paths_data),
                'total_quiz_questions': len(quiz_data),
                'total_assignments': len(assignments_data)
            }
        }
        
        # Save to file
        filename = f"production_sync_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Data exported to {filename}")
        print(f"📊 Summary:")
        print(f"   - Skills: {len(skills_data)}")
        print(f"   - Resources: {len(resources_data)}")
        print(f"   - Learning Paths: {len(learning_paths_data)}")
        print(f"   - Quiz Questions: {len(quiz_data)}")
        print(f"   - Assignments: {len(assignments_data)}")
        
        return filename

def import_data_from_file(filename):
    """Import data from exported file"""
    
    with app.app_context():
        print(f"🔄 Importing data from {filename}...")
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Clear existing data (careful!)
            print("⚠️  Clearing existing data...")
            LearningSession.query.delete()
            PracticalAssignment.query.delete()
            QuizQuestion.query.delete()
            SkillLearningPath.query.delete()
            EducationalResource.query.delete()
            EmergingSkill.query.delete()
            db.session.commit()
            
            # Import skills
            print("📝 Importing skills...")
            for skill_data in data['skills']:
                skill = EmergingSkill(
                    skill_name=skill_data['skill_name'],
                    description=skill_data['description'],
                    category=skill_data['category'],
                    urgency_score=skill_data['urgency_score'],
                    market_demand_evidence=skill_data['market_demand_evidence'],
                    status=skill_data['status'],
                    source=skill_data['source']
                )
                db.session.add(skill)
            
            # Import resources
            print("📚 Importing resources...")
            for resource_data in data['resources']:
                resource = EducationalResource(
                    title=resource_data['title'],
                    description=resource_data['description'],
                    url=resource_data['url'],
                    resource_type=resource_data['resource_type'],
                    difficulty_level=resource_data['difficulty_level'],
                    estimated_duration_minutes=resource_data['estimated_duration_minutes'],
                    quality_score=resource_data['quality_score'],
                    ai_analysis_summary=resource_data['ai_analysis_summary'],
                    transcript=resource_data['transcript'],
                    status=resource_data['status']
                )
                db.session.add(resource)
            
            # Commit skills and resources first to get IDs
            db.session.commit()
            
            # Create ID mappings for foreign keys
            skill_id_map = {}
            skills = EmergingSkill.query.all()
            for i, skill in enumerate(skills):
                original_id = data['skills'][i]['id']
                skill_id_map[original_id] = skill.id
            
            resource_id_map = {}
            resources = EducationalResource.query.all()
            for i, resource in enumerate(resources):
                original_id = data['resources'][i]['id']
                resource_id_map[original_id] = resource.id
            
            # Import learning paths
            print("🛤️  Importing learning paths...")
            for path_data in data['learning_paths']:
                if path_data['skill_id'] in skill_id_map and path_data['resource_id'] in resource_id_map:
                    path = SkillLearningPath(
                        skill_id=skill_id_map[path_data['skill_id']],
                        resource_id=resource_id_map[path_data['resource_id']],
                        sequence_order=path_data['sequence_order'],
                        path_type=path_data['path_type'],
                        is_required=path_data['is_required']
                    )
                    db.session.add(path)
            
            # Import quiz questions
            print("❓ Importing quiz questions...")
            for quiz_data in data['quiz_questions']:
                if quiz_data['resource_id'] in resource_id_map:
                    question = QuizQuestion(
                        resource_id=resource_id_map[quiz_data['resource_id']],
                        question_text=quiz_data['question_text'],
                        option_a=quiz_data['option_a'],
                        option_b=quiz_data['option_b'],
                        option_c=quiz_data['option_c'],
                        option_d=quiz_data['option_d'],
                        correct_answer=quiz_data['correct_answer'],
                        explanation=quiz_data['explanation']
                    )
                    db.session.add(question)
            
            # Import practical assignments
            print("📋 Importing practical assignments...")
            for assignment_data in data['practical_assignments']:
                if assignment_data['resource_id'] in resource_id_map:
                    assignment = PracticalAssignment(
                        resource_id=resource_id_map[assignment_data['resource_id']],
                        assignment_title=assignment_data['assignment_title'],
                        assignment_description=assignment_data['assignment_description'],
                        assignment_type=assignment_data['assignment_type'],
                        estimated_time_minutes=assignment_data['estimated_time_minutes']
                    )
                    db.session.add(assignment)
            
            db.session.commit()
            
            print("✅ Data import completed successfully!")
            print(f"📊 Imported:")
            print(f"   - Skills: {len(data['skills'])}")
            print(f"   - Resources: {len(data['resources'])}")
            print(f"   - Learning Paths: {len(data['learning_paths'])}")
            print(f"   - Quiz Questions: {len(data['quiz_questions'])}")
            print(f"   - Assignments: {len(data['practical_assignments'])}")
            
        except Exception as e:
            print(f"❌ Error importing data: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'export':
            export_all_data()
        elif sys.argv[1] == 'import' and len(sys.argv) > 2:
            import_data_from_file(sys.argv[2])
        else:
            print("Usage:")
            print("  python sync_data_to_production.py export")
            print("  python sync_data_to_production.py import <filename>")
    else:
        print("Usage:")
        print("  python sync_data_to_production.py export")
        print("  python sync_data_to_production.py import <filename>") 