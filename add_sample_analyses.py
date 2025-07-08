#!/usr/bin/env python3
"""
Add sample analyses for resources to populate the analysis pages
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, EducationalResource, ResourceAnalysis

def create_sample_analysis(resource_id, title):
    """Create a sample analysis for a resource"""
    
    sample_analyses = {
        "AI For Ethical Hackers Full Course | AI in Cybersecurity | ChatGPT": {
            "summary": "This comprehensive course teaches how to leverage AI and ChatGPT tools for ethical hacking and cybersecurity practices. It covers practical applications of artificial intelligence in penetration testing, vulnerability assessment, and security automation.",
            "key_concepts": ["AI-assisted penetration testing", "ChatGPT for cybersecurity", "Automated vulnerability scanning", "Machine learning in security", "Ethical hacking methodologies"],
            "learning_objectives": "Students will learn to integrate AI tools into their cybersecurity workflow, use ChatGPT for security research and report generation, automate common penetration testing tasks, and understand the ethical implications of AI in security testing.",
            "prerequisites": "Basic understanding of cybersecurity concepts, familiarity with penetration testing fundamentals, and introductory knowledge of AI/ML concepts.",
            "key_takeaways": [
                "AI can significantly enhance the efficiency of security testing",
                "ChatGPT can assist in vulnerability research and documentation",
                "Automation reduces manual effort in repetitive security tasks",
                "Ethical considerations are crucial when using AI for security testing"
            ],
            "actionable_insights": [
                "Implement AI-powered reconnaissance tools in your testing methodology",
                "Use ChatGPT to generate custom payloads and test cases",
                "Automate report generation and documentation processes",
                "Develop AI-assisted threat modeling approaches"
            ],
            "best_practices": [
                "Always validate AI-generated results manually",
                "Maintain ethical boundaries when using AI for security testing",
                "Keep AI tools updated and understand their limitations",
                "Document AI-assisted findings thoroughly for compliance"
            ],
            "common_pitfalls": [
                "Over-relying on AI without understanding underlying techniques",
                "Failing to validate AI-generated security findings",
                "Ignoring privacy implications of AI-assisted testing",
                "Not considering false positives from automated AI tools"
            ],
            "complexity_score": 7.5,
            "practical_applicability": 9.0,
            "industry_relevance": ["cybersecurity", "penetration_testing", "ai_security", "ethical_hacking"]
        },
        "default": {
            "summary": "This educational resource provides comprehensive coverage of AI and cybersecurity topics, offering practical insights and hands-on learning opportunities for security professionals.",
            "key_concepts": ["AI in cybersecurity", "Security automation", "Threat detection", "Machine learning applications", "Security best practices"],
            "learning_objectives": "Learners will gain practical skills in applying AI technologies to cybersecurity challenges, understand current industry trends, and develop expertise in modern security practices.",
            "prerequisites": "Basic understanding of cybersecurity fundamentals and introductory knowledge of AI/ML concepts.",
            "key_takeaways": [
                "AI is transforming the cybersecurity landscape",
                "Automation enhances security operations efficiency",
                "Continuous learning is essential in evolving threat environments",
                "Practical application solidifies theoretical knowledge"
            ],
            "actionable_insights": [
                "Implement AI-powered security tools in your organization",
                "Develop automation workflows for routine security tasks",
                "Stay updated with emerging AI security technologies",
                "Practice hands-on exercises to reinforce learning"
            ],
            "best_practices": [
                "Validate AI-generated results with human expertise",
                "Maintain security awareness and continuous monitoring",
                "Follow industry standards and compliance requirements",
                "Document processes and maintain audit trails"
            ],
            "common_pitfalls": [
                "Over-reliance on automated tools without human oversight",
                "Neglecting to update security measures regularly",
                "Insufficient testing of security implementations",
                "Ignoring the human element in security operations"
            ],
            "complexity_score": 6.5,
            "practical_applicability": 8.0,
            "industry_relevance": ["cybersecurity", "artificial_intelligence", "information_security", "technology"]
        }
    }
    
    # Select appropriate analysis template
    analysis_template = sample_analyses.get(title, sample_analyses["default"])
    
    return ResourceAnalysis(
        resource_id=resource_id,
        summary=analysis_template["summary"],
        key_concepts=json.dumps(analysis_template["key_concepts"]),
        learning_objectives=analysis_template["learning_objectives"],
        prerequisites=analysis_template["prerequisites"],
        key_takeaways=json.dumps(analysis_template["key_takeaways"]),
        actionable_insights=json.dumps(analysis_template["actionable_insights"]),
        best_practices=json.dumps(analysis_template["best_practices"]),
        common_pitfalls=json.dumps(analysis_template["common_pitfalls"]),
        complexity_score=analysis_template["complexity_score"],
        practical_applicability=analysis_template["practical_applicability"],
        industry_relevance=json.dumps(analysis_template["industry_relevance"]),
        ai_model_used="manual_sample",
        analysis_confidence=0.8,
        analysis_version="sample_1.0"
    )

def main():
    """Add sample analyses for all resources"""
    
    with app.app_context():
        # Get all resources
        resources = EducationalResource.query.all()
        print(f"Found {len(resources)} resources")
        
        # Add sample analyses
        added_count = 0
        
        for resource in resources:
            # Check if analysis already exists
            existing_analysis = ResourceAnalysis.query.filter_by(resource_id=resource.id).first()
            if existing_analysis:
                print(f"Analysis already exists for resource {resource.id}: {resource.title}")
                continue
            
            # Create sample analysis
            analysis = create_sample_analysis(resource.id, resource.title)
            
            try:
                db.session.add(analysis)
                db.session.commit()
                added_count += 1
                print(f"✅ Added analysis for resource {resource.id}: {resource.title}")
            except Exception as e:
                print(f"❌ Error adding analysis for resource {resource.id}: {e}")
                db.session.rollback()
        
        print(f"\n✅ Sample analysis generation complete!")
        print(f"Successfully added {added_count} sample analyses")
        
        # Verify results
        total_analyses = ResourceAnalysis.query.count()
        print(f"Total analyses in database: {total_analyses}")

if __name__ == "__main__":
    main() 