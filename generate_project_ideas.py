#!/usr/bin/env python3
"""
Generate project ideas for all resources that don't have them
"""

import os
import sys
import asyncio
import json
from datetime import datetime
import logging

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, EducationalResource, ResourceAnalysis, ProjectIdea, AI_SERVICES_AVAILABLE, ai_services

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def generate_projects_for_resource(resource_id):
    """Generate project ideas for a single resource"""
    try:
        resource = EducationalResource.query.get(resource_id)
        if not resource:
            logger.error(f"Resource {resource_id} not found")
            return False
        
        # Check if projects already exist
        existing_projects = ProjectIdea.query.filter_by(resource_id=resource_id).count()
        if existing_projects > 0:
            logger.info(f"Projects already exist for resource {resource_id}: {resource.title} ({existing_projects} projects)")
            return True
        
        # Prepare resource data for analysis
        resource_data = {
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'url': resource.url,
            'resource_type': resource.resource_type,
            'difficulty_level': resource.difficulty_level
        }
        
        # Get analysis data if available
        analysis = ResourceAnalysis.query.filter_by(resource_id=resource_id).first()
        analysis_data = analysis.to_dict() if analysis else None
        
        logger.info(f"Generating project ideas for resource {resource_id}: {resource.title}")
        
        # Generate project ideas (3 projects)
        projects = await ai_services.content_analyzer.generate_project_ideas(
            resource_data, analysis_data, 3
        )
        
        if not projects:
            logger.error(f"Failed to generate projects for resource {resource_id}")
            return False
        
        # Store projects in database
        stored_projects = []
        for p in projects:
            project_idea = ProjectIdea(
                resource_id=resource_id,
                title=p['title'],
                description=p['description'],
                difficulty_level=p['difficulty_level'],
                estimated_time_hours=p['estimated_time_hours'],
                objectives=json.dumps(p.get('objectives', [])),
                deliverables=json.dumps(p.get('deliverables', [])),
                success_criteria=json.dumps(p.get('success_criteria', [])),
                required_tools=json.dumps(p.get('required_tools', [])),
                skills_practiced=json.dumps(p.get('skills_practiced', [])),
                concepts_applied=json.dumps(p.get('concepts_applied', [])),
                real_world_context=p.get('real_world_context'),
                project_type=p.get('project_type'),
                industry_context=p.get('industry_context'),
                ai_model_used=p.get('ai_model_used'),
                generation_confidence=p.get('generation_confidence', 0.8)
            )
            db.session.add(project_idea)
            stored_projects.append(project_idea)
        
        db.session.commit()
        
        logger.info(f"Successfully generated {len(stored_projects)} project ideas for resource {resource_id}: {resource.title}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating projects for resource {resource_id}: {e}")
        db.session.rollback()
        return False

async def main():
    """Generate project ideas for all resources"""
    if not AI_SERVICES_AVAILABLE:
        print("❌ AI services not available. Cannot generate project ideas.")
        return
    
    with app.app_context():
        print("🚀 Starting project ideas generation for all resources...")
        
        # Get all resources
        resources = EducationalResource.query.all()
        print(f"📊 Found {len(resources)} total resources")
        
        # Check which resources don't have projects
        resources_without_projects = []
        for resource in resources:
            project_count = ProjectIdea.query.filter_by(resource_id=resource.id).count()
            if project_count == 0:
                resources_without_projects.append(resource)
        
        print(f"📋 Found {len(resources_without_projects)} resources without project ideas")
        
        if len(resources_without_projects) == 0:
            print("✅ All resources already have project ideas!")
            return
        
        # Generate projects for resources that don't have them
        success_count = 0
        for i, resource in enumerate(resources_without_projects, 1):
            print(f"\n🔄 Processing resource {i}/{len(resources_without_projects)}: {resource.title}")
            
            success = await generate_projects_for_resource(resource.id)
            if success:
                success_count += 1
                print(f"   ✅ Successfully generated projects")
            else:
                print(f"   ❌ Failed to generate projects")
        
        print(f"\n🎉 Project generation complete!")
        print(f"   ✅ Successfully generated projects for {success_count} resources")
        print(f"   ❌ Failed for {len(resources_without_projects) - success_count} resources")
        print(f"   📊 Total project ideas in database: {ProjectIdea.query.count()}")

if __name__ == "__main__":
    asyncio.run(main()) 