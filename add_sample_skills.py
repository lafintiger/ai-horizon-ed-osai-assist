#!/usr/bin/env python3
"""
Simple script to add sample skills to the database
"""

from app import app, db, EmergingSkill

def add_sample_skills():
    """Add sample skills from the AI-Horizon analysis"""
    
    skills_data = [
        {
            'skill_name': 'AI-Enhanced SIEM',
            'description': 'Security Information and Event Management enhanced with AI capabilities for improved threat detection and response',
            'category': 'Cybersecurity',
            'urgency_score': 8.5,
            'market_demand_evidence': '73% increase in job postings requiring AI-SIEM skills',
            'source': 'ai_horizon_analysis'
        },
        {
            'skill_name': 'Prompt Engineering',
            'description': 'Crafting effective prompts for AI systems to optimize security analysis and automation',
            'category': 'AI/ML',
            'urgency_score': 7.2,
            'market_demand_evidence': 'Emerging role with 67.5% confidence in AI-driven job creation',
            'source': 'ai_horizon_new_tasks'
        },
        {
            'skill_name': 'AI Security Engineering',
            'description': 'Specialized engineering role for securing AI systems and applications',
            'category': 'AI/ML',
            'urgency_score': 6.8,
            'market_demand_evidence': 'High demand for professionals who can secure AI systems and manage AI-driven incidents',
            'source': 'ai_horizon_new_tasks'
        },
        {
            'skill_name': 'MLSecOps',
            'description': 'Machine Learning Security Operations - managing AI/ML security pipelines and operations',
            'category': 'AI/ML',
            'urgency_score': 6.5,
            'market_demand_evidence': 'Emerging role for professionals who can secure AI systems and manage AI-driven incidents',
            'source': 'ai_horizon_new_tasks'
        },
        {
            'skill_name': 'Threat Intelligence with AI',
            'description': 'Advanced threat intelligence analysis enhanced with AI for pattern recognition and prediction',
            'category': 'Cybersecurity',
            'urgency_score': 7.8,
            'market_demand_evidence': 'New roles such as AI Integration Specialist and Threat Intelligence Analyst with AI Focus',
            'source': 'ai_horizon_augment'
        },
        {
            'skill_name': 'AI Governance',
            'description': 'Expertise in AI governance and compliance for organizations navigating evolving AI standards',
            'category': 'AI/ML',
            'urgency_score': 6.2,
            'market_demand_evidence': 'Essential for organizations to navigate evolving AI regulatory standards',
            'source': 'ai_horizon_new_tasks'
        }
    ]
    
    added_count = 0
    
    for skill_data in skills_data:
        # Check if skill already exists
        existing_skill = EmergingSkill.query.filter_by(skill_name=skill_data['skill_name']).first()
        if existing_skill:
            print(f"Skill '{skill_data['skill_name']}' already exists, skipping...")
            continue
        
        # Create new skill
        new_skill = EmergingSkill(
            skill_name=skill_data['skill_name'],
            description=skill_data['description'],
            category=skill_data['category'],
            urgency_score=skill_data['urgency_score'],
            market_demand_evidence=skill_data['market_demand_evidence'],
            source=skill_data['source'],
            status='active'
        )
        
        db.session.add(new_skill)
        added_count += 1
        print(f"Added skill: {skill_data['skill_name']}")
    
    db.session.commit()
    print(f"\nSuccessfully added {added_count} skills")
    print(f"Total skills in database: {EmergingSkill.query.count()}")

if __name__ == "__main__":
    with app.app_context():
        add_sample_skills() 