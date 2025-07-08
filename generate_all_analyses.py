#!/usr/bin/env python3
"""
Generate comprehensive analyses for all resources that don't have them
"""

import os
import sys
import asyncio
import json
from datetime import datetime
import logging

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, EducationalResource, ResourceAnalysis, AI_SERVICES_AVAILABLE, ai_services

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def generate_analysis_for_resource(resource_id):
    """Generate comprehensive analysis for a single resource"""
    try:
        resource = EducationalResource.query.get(resource_id)
        if not resource:
            logger.error(f"Resource {resource_id} not found")
            return False
        
        # Check if analysis already exists
        existing_analysis = ResourceAnalysis.query.filter_by(resource_id=resource_id).first()
        if existing_analysis:
            logger.info(f"Analysis already exists for resource {resource_id}: {resource.title}")
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
        
        logger.info(f"Generating analysis for resource {resource_id}: {resource.title}")
        
        # Perform comprehensive analysis
        analysis_result = await ai_services.content_analyzer.analyze_resource_comprehensively(resource_data)
        
        if not analysis_result:
            logger.error(f"Failed to analyze resource {resource_id}")
            return False
        
        # Store analysis in database
        analysis = ResourceAnalysis(
            resource_id=resource_id,
            summary=analysis_result.get('summary'),
            key_concepts=json.dumps(analysis_result.get('key_concepts', [])),
            learning_objectives=analysis_result.get('learning_objectives'),
            prerequisites=analysis_result.get('prerequisites'),
            key_takeaways=json.dumps(analysis_result.get('key_takeaways', [])),
            actionable_insights=json.dumps(analysis_result.get('actionable_insights', [])),
            best_practices=json.dumps(analysis_result.get('best_practices', [])),
            common_pitfalls=json.dumps(analysis_result.get('common_pitfalls', [])),
            complexity_score=analysis_result.get('complexity_score', 0.0),
            practical_applicability=analysis_result.get('practical_applicability', 0.0),
            industry_relevance=json.dumps(analysis_result.get('industry_relevance', [])),
            ai_model_used=analysis_result.get('ai_model_used'),
            analysis_confidence=analysis_result.get('analysis_confidence', 0.0),
            analysis_version='2.0'
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        logger.info(f"✅ Analysis generated for resource {resource_id}: {resource.title}")
        return True
        
    except Exception as e:
        logger.error(f"Error analyzing resource {resource_id}: {e}")
        db.session.rollback()
        return False

async def main():
    """Generate analyses for all resources without them"""
    
    if not AI_SERVICES_AVAILABLE:
        logger.error("AI services not available - cannot generate analyses")
        return
    
    with app.app_context():
        # Get all resources
        resources = EducationalResource.query.all()
        logger.info(f"Found {len(resources)} total resources")
        
        # Find resources without analysis
        resources_without_analysis = []
        for resource in resources:
            existing_analysis = ResourceAnalysis.query.filter_by(resource_id=resource.id).first()
            if not existing_analysis:
                resources_without_analysis.append(resource)
        
        logger.info(f"Found {len(resources_without_analysis)} resources without analysis")
        
        if not resources_without_analysis:
            logger.info("All resources already have analyses!")
            return
        
        # Generate analyses
        success_count = 0
        total_count = len(resources_without_analysis)
        
        for i, resource in enumerate(resources_without_analysis):
            logger.info(f"Processing {i+1}/{total_count}: {resource.title}")
            
            success = await generate_analysis_for_resource(resource.id)
            if success:
                success_count += 1
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(2)
        
        logger.info(f"✅ Analysis generation complete!")
        logger.info(f"Successfully generated {success_count}/{total_count} analyses")
        
        # Verify results
        final_count = ResourceAnalysis.query.count()
        logger.info(f"Total analyses in database: {final_count}")

if __name__ == "__main__":
    asyncio.run(main()) 