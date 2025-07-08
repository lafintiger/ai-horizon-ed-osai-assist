#!/usr/bin/env python3
"""
AI-Horizon Ed Platform - Sample Data Import Script
This script imports skills and resources from the AI-Horizon analysis data.
"""

import os
import re
import json
from datetime import datetime
from app import app, db, EmergingSkill, EducationalResource, SkillLearningPath

def parse_ai_horizon_data():
    """Parse the AI-Horizon analysis data from the text file."""
    try:
        with open('ai-horizon-augment-new.txt', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: ai-horizon-augment-new.txt not found")
        return None

    # Extract skills data
    skills_data = []
    
    # Parse AI AUGMENT section
    augment_match = re.search(r'🤝 AI AUGMENT.*?🎯 Key Jobs & Tasks(.*?)📚 Supporting Citations', content, re.DOTALL)
    if augment_match:
        augment_content = augment_match.group(1)
        
        # Extract individual skills
        skill_pattern = r'(\w+(?:\s+\w+)*)\s+(\d+\.\d+)%\s+(.*?)📄 Evidence from (\d+) articles'
        skills_matches = re.findall(skill_pattern, augment_content, re.DOTALL)
        
        for skill_match in skills_matches:
            skill_name, confidence, description, evidence_count = skill_match
            skills_data.append({
                'name': skill_name.strip(),
                'category': 'Cybersecurity',
                'urgency_score': float(confidence) / 10,  # Convert percentage to 0-10 scale
                'description': f"AI-enhanced {skill_name.lower()} capabilities. {description.strip()[:500]}",
                'market_demand_evidence': f"Evidence from {evidence_count} articles showing {confidence}% confidence in AI augmentation",
                'source': 'ai_horizon_augment_analysis'
            })

    # Parse AI NEW TASKS section
    new_tasks_match = re.search(r'✨ AI NEW TASKS.*?🎯 Key Jobs & Tasks(.*?)📚 Supporting Citations', content, re.DOTALL)
    if new_tasks_match:
        new_tasks_content = new_tasks_match.group(1)
        
        # Extract individual skills
        skill_pattern = r'(\w+(?:\s+\w+)*)\s+(\d+\.\d+)%\s+(.*?)📄 Evidence from (\d+) articles'
        skills_matches = re.findall(skill_pattern, new_tasks_content, re.DOTALL)
        
        for skill_match in skills_matches:
            skill_name, confidence, description, evidence_count = skill_match
            skills_data.append({
                'name': skill_name.strip(),
                'category': 'AI/ML',
                'urgency_score': float(confidence) / 10,  # Convert percentage to 0-10 scale
                'description': f"Emerging {skill_name.lower()} role. {description.strip()[:500]}",
                'market_demand_evidence': f"Evidence from {evidence_count} articles showing {confidence}% confidence in new role creation",
                'source': 'ai_horizon_new_tasks_analysis'
            })

    return skills_data

def create_sample_resources():
    """Create sample educational resources for each skill."""
    resources = [
        {
            'title': 'Introduction to AI-Enhanced Security Operations',
            'description': 'Comprehensive overview of how AI is transforming cybersecurity operations',
            'url': 'https://example.com/ai-security-ops',
            'resource_type': 'course',
            'difficulty_level': 'beginner',
            'estimated_duration_minutes': 120,
            'quality_score': 0.85,
            'ai_analysis_summary': 'High-quality introductory course covering AI applications in security operations'
        },
        {
            'title': 'Advanced Threat Hunting with AI',
            'description': 'Deep dive into AI-powered threat hunting techniques and tools',
            'url': 'https://example.com/ai-threat-hunting',
            'resource_type': 'course',
            'difficulty_level': 'advanced',
            'estimated_duration_minutes': 180,
            'quality_score': 0.92,
            'ai_analysis_summary': 'Expert-level course with hands-on AI threat hunting exercises'
        },
        {
            'title': 'Machine Learning for Security Analysts',
            'description': 'Practical guide to applying ML techniques in security analysis',
            'url': 'https://example.com/ml-security',
            'resource_type': 'video',
            'difficulty_level': 'intermediate',
            'estimated_duration_minutes': 90,
            'quality_score': 0.78,
            'ai_analysis_summary': 'Well-structured video series covering ML applications in security'
        },
        {
            'title': 'AI Security Tools and Platforms',
            'description': 'Overview of leading AI-powered security tools and platforms',
            'url': 'https://example.com/ai-tools',
            'resource_type': 'documentation',
            'difficulty_level': 'beginner',
            'estimated_duration_minutes': 45,
            'quality_score': 0.74,
            'ai_analysis_summary': 'Comprehensive documentation of AI security tools landscape'
        },
        {
            'title': 'Prompt Engineering for Security Teams',
            'description': 'Learn to craft effective prompts for AI-powered security analysis',
            'url': 'https://example.com/prompt-engineering',
            'resource_type': 'course',
            'difficulty_level': 'intermediate',
            'estimated_duration_minutes': 150,
            'quality_score': 0.88,
            'ai_analysis_summary': 'Specialized course focusing on prompt engineering for security use cases'
        }
    ]
    
    return resources

def import_skills_data():
    """Import skills data into the database."""
    skills_data = parse_ai_horizon_data()
    if not skills_data:
        print("No skills data found to import")
        return 0

    imported_count = 0
    
    for skill_data in skills_data:
        # Check if skill already exists
        existing_skill = EmergingSkill.query.filter_by(skill_name=skill_data['name']).first()
        if existing_skill:
            print(f"Skill '{skill_data['name']}' already exists, skipping...")
            continue
        
        # Create new skill
        new_skill = EmergingSkill(
            skill_name=skill_data['name'],
            description=skill_data['description'],
            category=skill_data['category'],
            urgency_score=skill_data['urgency_score'],
            market_demand_evidence=skill_data['market_demand_evidence'],
            source=skill_data['source'],
            status='active'
        )
        
        db.session.add(new_skill)
        imported_count += 1
        print(f"Added skill: {skill_data['name']}")
    
    db.session.commit()
    print(f"Successfully imported {imported_count} skills")
    return imported_count

def import_resources_data():
    """Import sample resources data into the database."""
    resources = create_sample_resources()
    skills = EmergingSkill.query.all()
    
    if not skills:
        print("No skills found. Please import skills first.")
        return 0
    
    imported_count = 0
    
    for resource_data in resources:
        # Check if resource already exists
        existing_resource = EducationalResource.query.filter_by(url=resource_data['url']).first()
        if existing_resource:
            print(f"Resource '{resource_data['title']}' already exists, skipping...")
            continue
        
        # Create new resource
        new_resource = EducationalResource(
            title=resource_data['title'],
            description=resource_data['description'],
            url=resource_data['url'],
            resource_type=resource_data['resource_type'],
            difficulty_level=resource_data['difficulty_level'],
            estimated_duration_minutes=resource_data['estimated_duration_minutes'],
            quality_score=resource_data['quality_score'],
            ai_analysis_summary=resource_data['ai_analysis_summary'],
            status='approved'
        )
        
        db.session.add(new_resource)
        db.session.flush()  # Get the ID
        
        # Create learning paths for random skills
        import random
        selected_skills = random.sample(skills, min(3, len(skills)))
        
        for i, skill in enumerate(selected_skills):
            learning_path = SkillLearningPath(
                skill_id=skill.id,
                resource_id=new_resource.id,
                sequence_order=i + 1,
                path_type='foundation' if i == 0 else 'intermediate' if i == 1 else 'advanced',
                is_required=i == 0
            )
            db.session.add(learning_path)
        
        imported_count += 1
        print(f"Added resource: {resource_data['title']}")
    
    db.session.commit()
    print(f"Successfully imported {imported_count} resources")
    return imported_count

def main():
    """Main function to run the data import."""
    print("AI-Horizon Ed Platform - Sample Data Import")
    print("=" * 50)
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Import skills
        print("\nImporting skills from AI-Horizon analysis...")
        skills_imported = import_skills_data()
        
        # Import resources
        print("\nImporting sample resources...")
        resources_imported = import_resources_data()
        
        # Summary
        print("\n" + "=" * 50)
        print("Import Summary:")
        print(f"Skills imported: {skills_imported}")
        print(f"Resources imported: {resources_imported}")
        print(f"Total skills in database: {EmergingSkill.query.count()}")
        print(f"Total resources in database: {EducationalResource.query.count()}")
        print(f"Total learning paths: {SkillLearningPath.query.count()}")
        
        if skills_imported > 0 or resources_imported > 0:
            print("\nData import completed successfully!")
        else:
            print("\nNo new data was imported (all data already exists)")

if __name__ == "__main__":
    main() 