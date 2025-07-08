#!/usr/bin/env python3
"""
AI Services Module for AI-Horizon Ed Platform
Provides comprehensive AI-powered skills discovery and resource curation
"""

import os
import json
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import openai
from anthropic import Anthropic
import requests
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SkillDiscoveryResult:
    """Result from skills discovery"""
    skill_name: str
    description: str
    category: str
    urgency_score: float
    market_demand_evidence: str
    source: str
    confidence_score: float

@dataclass
class ResourceDiscoveryResult:
    """Result from resource discovery"""
    title: str
    description: str
    url: str
    resource_type: str
    difficulty_level: str
    estimated_duration_minutes: Optional[int]
    quality_score: float
    ai_analysis_summary: str
    source: str

class AIServicesManager:
    """Main AI services manager orchestrating all AI integrations"""
    
    def __init__(self):
        self.openai_client = self._init_openai()
        self.anthropic_client = self._init_anthropic()
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not found - skills discovery will be limited")
        if not self.youtube_api_key:
            logger.warning("YouTube API key not found - video discovery will be limited")
        
        # Initialize content analyzer after all other properties are set
        self.content_analyzer = ContentAnalyzer(self)
    
    def _init_openai(self) -> Optional[openai.OpenAI]:
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                # Initialize with minimal configuration to avoid compatibility issues
                return openai.OpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                return None
        logger.warning("OpenAI API key not found")
        return None
    
    def _init_anthropic(self) -> Optional[Anthropic]:
        """Initialize Anthropic client"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            return Anthropic(api_key=api_key)
        logger.warning("Anthropic API key not found")
        return None

class SkillsDiscoveryEngine:
    """AI-powered skills discovery using Perplexity and other sources"""
    
    def __init__(self, ai_services: AIServicesManager):
        self.ai_services = ai_services
        self.perplexity_api_key = ai_services.perplexity_api_key
    
    async def discover_emerging_skills(self, 
                                     domain: str = "AI and Cybersecurity",
                                     timeframe: str = "2024-2025",
                                     limit: int = 10) -> List[SkillDiscoveryResult]:
        """Discover emerging skills using Perplexity API"""
        
        if not self.perplexity_api_key:
            logger.error("Perplexity API key not available for skills discovery")
            return []
        
        logger.info(f"Discovering emerging skills in {domain} for {timeframe}")
        
        # Construct search query
        query = f"""
        What are the most critical emerging skills needed in {domain} for {timeframe}?
        Focus on:
        1. AI-enhanced cybersecurity roles
        2. New technologies requiring specialized knowledge
        3. Skills with high market demand and urgency
        4. Roles that combine AI with traditional cybersecurity
        
        For each skill, provide:
        - Skill name
        - Brief description
        - Category (AI/ML, Cybersecurity, etc.)
        - Urgency score (1-10)
        - Market demand evidence
        """
        
        try:
            # Make request to Perplexity API
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert workforce analyst specializing in AI and cybersecurity skills trends. Provide detailed, actionable insights about emerging skills with specific market evidence.'
                    },
                    {
                        'role': 'user',
                        'content': query
                    }
                ],
                'temperature': 0.2,
                'max_tokens': 4000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.perplexity.ai/chat/completions',
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        raw_response = data['choices'][0]['message']['content']
                        
                        # Parse response into structured results
                        return await self._parse_skills_response(raw_response)
                    else:
                        logger.error(f"Perplexity API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error discovering skills: {e}")
            return []
    
    async def _parse_skills_response(self, response: str) -> List[SkillDiscoveryResult]:
        """Parse Perplexity response into structured skills data"""
        
        # Use OpenAI to parse the response into structured format
        if not self.ai_services.openai_client:
            return []
        
        try:
            parsing_prompt = f"""
            Parse this skills analysis into a JSON array of skills objects.
            Each skill should have:
            - skill_name: concise name
            - description: 1-2 sentence description
            - category: AI/ML, Cybersecurity, DevOps, etc.
            - urgency_score: 1-10 numeric score
            - market_demand_evidence: specific evidence mentioned
            - confidence_score: 0.0-1.0 based on evidence quality
            
            Text to parse:
            {response}
            
            Return only valid JSON array:
            """
            
            response_obj = self.ai_services.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data parser. Return only valid JSON arrays."},
                    {"role": "user", "content": parsing_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            parsed_content = response_obj.choices[0].message.content
            
            # Clean up the response to extract JSON
            if '```json' in parsed_content:
                parsed_content = parsed_content.split('```json')[1].split('```')[0]
            elif '```' in parsed_content:
                parsed_content = parsed_content.split('```')[1]
            
            skills_data = json.loads(parsed_content.strip())
            
            # Convert to SkillDiscoveryResult objects
            results = []
            for skill_data in skills_data:
                result = SkillDiscoveryResult(
                    skill_name=skill_data.get('skill_name', 'Unknown Skill'),
                    description=skill_data.get('description', 'No description available'),
                    category=skill_data.get('category', 'General'),
                    urgency_score=float(skill_data.get('urgency_score', 5.0)),
                    market_demand_evidence=skill_data.get('market_demand_evidence', 'No evidence provided'),
                    source='perplexity_discovery',
                    confidence_score=float(skill_data.get('confidence_score', 0.5))
                )
                results.append(result)
            
            logger.info(f"Successfully parsed {len(results)} skills from discovery")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing skills response: {e}")
            return []

class ResourceDiscoveryEngine:
    """AI-powered resource discovery using multiple APIs"""
    
    def __init__(self, ai_services: AIServicesManager):
        self.ai_services = ai_services
        self.perplexity_api_key = ai_services.perplexity_api_key
        self.youtube_api_key = ai_services.youtube_api_key
    
    async def discover_resources_for_skill(self, 
                                         skill_name: str,
                                         resource_types: List[str] = None,
                                         limit: int = 20) -> List[ResourceDiscoveryResult]:
        """Discover educational resources for a specific skill"""
        
        if resource_types is None:
            resource_types = ['videos', 'courses', 'documentation', 'tools']
        
        logger.info(f"Discovering resources for skill: {skill_name}")
        
        all_resources = []
        
        # Discover resources from multiple sources
        for resource_type in resource_types:
            try:
                if resource_type == 'videos' and self.youtube_api_key:
                    videos = await self._discover_youtube_videos(skill_name, limit=5)
                    all_resources.extend(videos)
                
                elif resource_type in ['courses', 'documentation', 'tools']:
                    resources = await self._discover_web_resources(skill_name, resource_type, limit=5)
                    all_resources.extend(resources)
                    
            except Exception as e:
                logger.error(f"Error discovering {resource_type} for {skill_name}: {e}")
        
        # Sort by quality score and return top results
        all_resources.sort(key=lambda x: x.quality_score, reverse=True)
        return all_resources[:limit]
    
    async def _discover_youtube_videos(self, skill_name: str, limit: int = 5) -> List[ResourceDiscoveryResult]:
        """Discover YouTube videos for a skill"""
        
        search_query = f"{skill_name} tutorial course training"
        
        try:
            # YouTube Data API v3 search
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': search_query,
                'key': self.youtube_api_key,
                'type': 'video',
                'maxResults': limit,
                'order': 'relevance',
                'videoDuration': 'medium',  # 4-20 minutes
                'videoEmbeddable': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        videos = []
                        for item in data.get('items', []):
                            video_id = item['id']['videoId']
                            snippet = item['snippet']
                            
                            # Get video details for duration
                            video_details = await self._get_youtube_video_details(video_id)
                            
                            video_result = ResourceDiscoveryResult(
                                title=snippet['title'],
                                description=snippet['description'][:500],
                                url=f"https://www.youtube.com/watch?v={video_id}",
                                resource_type='video',
                                difficulty_level='intermediate',  # Default, can be analyzed
                                estimated_duration_minutes=video_details.get('duration_minutes'),
                                quality_score=0.7,  # Default, will be analyzed
                                ai_analysis_summary='YouTube video - analysis pending',
                                source='youtube'
                            )
                            videos.append(video_result)
                        
                        return videos
                    else:
                        logger.error(f"YouTube API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error discovering YouTube videos: {e}")
            return []
    
    async def _get_youtube_video_details(self, video_id: str) -> Dict[str, Any]:
        """Get detailed video information from YouTube API"""
        
        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'contentDetails,statistics',
                'id': video_id,
                'key': self.youtube_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('items'):
                            item = data['items'][0]
                            duration_str = item['contentDetails']['duration']
                            
                            # Parse ISO 8601 duration (PT15M33S)
                            duration_minutes = self._parse_youtube_duration(duration_str)
                            
                            return {
                                'duration_minutes': duration_minutes,
                                'view_count': int(item['statistics'].get('viewCount', 0)),
                                'like_count': int(item['statistics'].get('likeCount', 0))
                            }
                    
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting YouTube video details: {e}")
            return {}
    
    def _parse_youtube_duration(self, duration_str: str) -> int:
        """Parse YouTube ISO 8601 duration to minutes"""
        
        try:
            # Parse PT15M33S format
            duration_str = duration_str.replace('PT', '')
            
            minutes = 0
            if 'M' in duration_str:
                minutes = int(duration_str.split('M')[0].split('H')[-1])
            
            if 'H' in duration_str:
                hours = int(duration_str.split('H')[0])
                minutes += hours * 60
            
            return minutes
            
        except Exception:
            return 0
    
    async def _discover_web_resources(self, skill_name: str, resource_type: str, limit: int = 5) -> List[ResourceDiscoveryResult]:
        """Discover web resources using Perplexity API"""
        
        if not self.perplexity_api_key:
            return []
        
        # Construct search query based on resource type
        query_templates = {
            'courses': f"Best online courses for learning {skill_name}. Include course platforms, duration, and difficulty level.",
            'documentation': f"Official documentation, guides, and technical resources for {skill_name}. Include authoritative sources.",
            'tools': f"Essential tools, software, and platforms for {skill_name}. Include free and paid options."
        }
        
        query = query_templates.get(resource_type, f"Educational resources for {skill_name}")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are an educational resource curator. Find the best {resource_type} for learning specific skills. Provide URLs, descriptions, and quality assessments.'
                    },
                    {
                        'role': 'user',
                        'content': query
                    }
                ],
                'temperature': 0.2,
                'max_tokens': 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.perplexity.ai/chat/completions',
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        raw_response = data['choices'][0]['message']['content']
                        
                        # Parse response into structured resources
                        return await self._parse_web_resources_response(raw_response, resource_type)
                    else:
                        logger.error(f"Perplexity API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error discovering web resources: {e}")
            return []
    
    async def _parse_web_resources_response(self, response: str, resource_type: str) -> List[ResourceDiscoveryResult]:
        """Parse Perplexity response into structured resource data"""
        
        if not self.ai_services.openai_client:
            return []
        
        try:
            parsing_prompt = f"""
            Parse this {resource_type} analysis into a JSON array of resource objects.
            Each resource should have:
            - title: resource name
            - description: 1-2 sentence description
            - url: full URL if available (or "URL not provided")
            - difficulty_level: beginner, intermediate, or advanced
            - estimated_duration_minutes: numeric estimate or null
            - quality_score: 0.0-1.0 based on reputation/reviews
            
            Text to parse:
            {response}
            
            Return only valid JSON array:
            """
            
            response_obj = self.ai_services.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data parser. Return only valid JSON arrays."},
                    {"role": "user", "content": parsing_prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            parsed_content = response_obj.choices[0].message.content
            
            # Clean up the response to extract JSON
            if '```json' in parsed_content:
                parsed_content = parsed_content.split('```json')[1].split('```')[0]
            elif '```' in parsed_content:
                parsed_content = parsed_content.split('```')[1]
            
            resources_data = json.loads(parsed_content.strip())
            
            # Convert to ResourceDiscoveryResult objects
            results = []
            for resource_data in resources_data:
                result = ResourceDiscoveryResult(
                    title=resource_data.get('title', 'Unknown Resource'),
                    description=resource_data.get('description', 'No description available'),
                    url=resource_data.get('url', 'URL not provided'),
                    resource_type=resource_type,
                    difficulty_level=resource_data.get('difficulty_level', 'intermediate'),
                    estimated_duration_minutes=resource_data.get('estimated_duration_minutes'),
                    quality_score=float(resource_data.get('quality_score', 0.5)),
                    ai_analysis_summary='Discovered via Perplexity API',
                    source='perplexity_web'
                )
                results.append(result)
            
            logger.info(f"Successfully parsed {len(results)} {resource_type} resources")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing web resources response: {e}")
            return []

class ContentAnalyzer:
    """Advanced AI-powered content analysis and educational enhancement"""
    
    def __init__(self, ai_services: AIServicesManager):
        self.ai_services = ai_services
    
    async def analyze_resource_quality(self, resource: ResourceDiscoveryResult) -> Dict[str, Any]:
        """Analyze resource quality and generate quality score"""
        
        logger.info(f"Analyzing quality of resource: {resource.title}")
        
        # Try Anthropic first, fallback to OpenAI
        analysis = await self._analyze_with_anthropic(resource)
        if not analysis:
            analysis = await self._analyze_with_openai(resource)
        
        return analysis or self._default_analysis()
    
    async def analyze_resource_comprehensively(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis including summary, wisdom extraction, and educational enhancements"""
        
        logger.info(f"Performing comprehensive analysis of resource: {resource_data.get('title', 'Unknown')}")
        
        # Use GPT-4 for comprehensive analysis
        if not self.ai_services.openai_client:
            logger.error("OpenAI client not available for comprehensive analysis")
            return {}
        
        try:
            analysis_prompt = f"""
            Analyze this educational resource comprehensively and provide detailed insights:
            
            RESOURCE DETAILS:
            Title: {resource_data.get('title', 'N/A')}
            Description: {resource_data.get('description', 'N/A')}
            URL: {resource_data.get('url', 'N/A')}
            Type: {resource_data.get('resource_type', 'N/A')}
            Difficulty: {resource_data.get('difficulty_level', 'N/A')}
            
            Provide a comprehensive analysis in JSON format with these sections:
            
            {{
                "summary": "Clear 2-3 sentence summary of what this resource covers",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "learning_objectives": "What learners will be able to do after completing this resource",
                "prerequisites": "What knowledge/skills are needed before starting this resource",
                "key_takeaways": [
                    "Most important insight 1",
                    "Most important insight 2",
                    "Most important insight 3"
                ],
                "actionable_insights": [
                    "Practical application 1",
                    "Practical application 2",
                    "Practical application 3"
                ],
                "best_practices": [
                    "Best practice 1 from the resource",
                    "Best practice 2 from the resource",
                    "Best practice 3 from the resource"
                ],
                "common_pitfalls": [
                    "Common mistake to avoid 1",
                    "Common mistake to avoid 2",
                    "Common mistake to avoid 3"
                ],
                "complexity_score": 7.5,
                "practical_applicability": 8.0,
                "industry_relevance": ["cybersecurity", "software_development", "cloud_computing"],
                "analysis_confidence": 0.85
            }}
            
            Base your analysis on the resource details provided. If information is limited, indicate lower confidence scores.
            Complexity score: 0-10 (0=very basic, 10=highly advanced)
            Practical applicability: 0-10 (0=purely theoretical, 10=immediately actionable)
            Analysis confidence: 0.0-1.0 (how confident you are in this analysis)
            """
            
            response = self.ai_services.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert educational content analyst specializing in technology and cybersecurity resources. Provide detailed, actionable analysis."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            analysis_content = response.choices[0].message.content
            
            # Clean and parse JSON response
            if '```json' in analysis_content:
                analysis_content = analysis_content.split('```json')[1].split('```')[0]
            elif '```' in analysis_content:
                analysis_content = analysis_content.split('```')[1]
            
            analysis_result = json.loads(analysis_content.strip())
            analysis_result['ai_model_used'] = 'gpt-4o'
            analysis_result['analysis_date'] = datetime.utcnow().isoformat()
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {
                'summary': 'Analysis failed - unable to process resource content',
                'analysis_confidence': 0.0,
                'error': str(e)
            }
    
    async def generate_quiz_questions(self, resource_data: Dict[str, Any], 
                                    analysis_data: Dict[str, Any] = None,
                                    num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generate multiple choice quiz questions based on resource content"""
        
        logger.info(f"Generating {num_questions} quiz questions for: {resource_data.get('title', 'Unknown')}")
        
        if not self.ai_services.openai_client:
            logger.error("OpenAI client not available for quiz generation")
            return []
        
        try:
            # Use analysis data if available, but handle potential issues
            key_concepts = []
            key_takeaways = []
            
            if analysis_data:
                try:
                    key_concepts = analysis_data.get('key_concepts', [])
                    key_takeaways = analysis_data.get('key_takeaways', [])
                    # Ensure they are lists, not strings
                    if isinstance(key_concepts, str):
                        key_concepts = []
                    if isinstance(key_takeaways, str):
                        key_takeaways = []
                except Exception as e:
                    logger.warning(f"Error processing analysis data: {e}")
                    key_concepts = []
                    key_takeaways = []
            
            quiz_prompt = f"""
            Create {num_questions} multiple choice questions for this educational resource:
            
            RESOURCE:
            Title: {resource_data.get('title', 'N/A')}
            Description: {resource_data.get('description', 'N/A')}
            Type: {resource_data.get('resource_type', 'N/A')}
            Difficulty: {resource_data.get('difficulty_level', 'N/A')}
            
            KEY CONCEPTS: {', '.join(key_concepts) if key_concepts else 'Not available'}
            KEY TAKEAWAYS: {', '.join(key_takeaways) if key_takeaways else 'Not available'}
            
            Create questions that test:
            1. Conceptual understanding
            2. Practical application
            3. Critical thinking about the topic
            
            Return as JSON array:
            [
                {{
                    "question_text": "Clear, specific question",
                    "option_a": "First option",
                    "option_b": "Second option", 
                    "option_c": "Third option",
                    "option_d": "Fourth option",
                    "correct_answer": "A",
                    "explanation": "Why this answer is correct and others are wrong",
                    "difficulty": "beginner|intermediate|advanced",
                    "concept_tested": "Main concept being tested"
                }}
            ]
            
            Make questions practical and relevant to real-world application.
            Ensure explanations provide educational value.
            """
            
            response = self.ai_services.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert educational assessment designer specializing in technology and cybersecurity. Create high-quality, practical quiz questions."},
                    {"role": "user", "content": quiz_prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            quiz_content = response.choices[0].message.content
            
            # Clean and parse JSON response
            if '```json' in quiz_content:
                quiz_content = quiz_content.split('```json')[1].split('```')[0]
            elif '```' in quiz_content:
                quiz_content = quiz_content.split('```')[1]
            
            questions = json.loads(quiz_content.strip())
            
            # Add metadata to each question
            for i, question in enumerate(questions):
                question['id'] = i + 1
                question['resource_id'] = resource_data.get('id')
                question['ai_generated'] = True
                question['created_date'] = datetime.utcnow().isoformat()
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating quiz questions: {e}")
            return []
    
    async def generate_project_ideas(self, resource_data: Dict[str, Any],
                                   analysis_data: Dict[str, Any] = None,
                                   num_projects: int = 3) -> List[Dict[str, Any]]:
        """Generate practical project ideas based on resource content"""
        
        logger.info(f"Generating {num_projects} project ideas for: {resource_data.get('title', 'Unknown')}")
        
        if not self.ai_services.openai_client:
            logger.error("OpenAI client not available for project generation")
            return []
        
        try:
            # Use analysis data if available
            skills_from_analysis = analysis_data.get('key_concepts', []) if analysis_data else []
            actionable_insights = analysis_data.get('actionable_insights', []) if analysis_data else []
            
            projects_prompt = f"""
            Create {num_projects} practical project ideas based on this educational resource:
            
            RESOURCE:
            Title: {resource_data.get('title', 'N/A')}
            Description: {resource_data.get('description', 'N/A')}
            Type: {resource_data.get('resource_type', 'N/A')}
            Difficulty: {resource_data.get('difficulty_level', 'N/A')}
            
            KEY CONCEPTS: {', '.join(skills_from_analysis) if skills_from_analysis else 'Not available'}
            ACTIONABLE INSIGHTS: {', '.join(actionable_insights) if actionable_insights else 'Not available'}
            
            Create projects that:
            1. Apply concepts from the resource
            2. Have clear, achievable deliverables
            3. Provide hands-on learning experience
            4. Scale from beginner to advanced difficulty
            
            Return as JSON array:
            [
                {{
                    "title": "Clear, engaging project title",
                    "description": "2-3 sentence description of what the project involves",
                    "difficulty_level": "beginner|intermediate|advanced",
                    "estimated_time_hours": 8,
                    "objectives": [
                        "Learning objective 1",
                        "Learning objective 2",
                        "Learning objective 3"
                    ],
                    "deliverables": [
                        "Deliverable 1",
                        "Deliverable 2", 
                        "Deliverable 3"
                    ],
                    "success_criteria": [
                        "Success metric 1",
                        "Success metric 2",
                        "Success metric 3"
                    ],
                    "required_tools": [
                        "Tool/technology 1",
                        "Tool/technology 2"
                    ],
                    "skills_practiced": [
                        "Skill 1",
                        "Skill 2"
                    ],
                    "concepts_applied": [
                        "Concept from resource 1",
                        "Concept from resource 2"
                    ],
                    "real_world_context": "How this project relates to real professional scenarios",
                    "project_type": "individual|team|classroom",
                    "industry_context": "cybersecurity|software_development|cloud_computing"
                }}
            ]
            
            Make projects practical and professionally relevant.
            Include one beginner, one intermediate, and one advanced project.
            """
            
            response = self.ai_services.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert educational project designer specializing in technology and cybersecurity. Create engaging, practical projects that reinforce learning."},
                    {"role": "user", "content": projects_prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            projects_content = response.choices[0].message.content
            
            # Clean and parse JSON response
            if '```json' in projects_content:
                projects_content = projects_content.split('```json')[1].split('```')[0]
            elif '```' in projects_content:
                projects_content = projects_content.split('```')[1]
            
            projects = json.loads(projects_content.strip())
            
            # Add metadata to each project
            for i, project in enumerate(projects):
                project['id'] = i + 1
                project['resource_id'] = resource_data.get('id')
                project['ai_generated'] = True
                project['ai_model_used'] = 'gpt-4o'
                project['generation_confidence'] = 0.8  # Default confidence
                project['created_date'] = datetime.utcnow().isoformat()
            
            return projects
            
        except Exception as e:
            logger.error(f"Error generating project ideas: {e}")
            return []

    async def _analyze_with_anthropic(self, resource: ResourceDiscoveryResult) -> Optional[Dict[str, Any]]:
        """Analyze resource using Anthropic Claude"""
        
        if not self.ai_services.anthropic_client:
            return None
        
        try:
            analysis_prompt = f"""
            Analyze this educational resource and provide a quality assessment:
            
            Title: {resource.title}
            Description: {resource.description}
            URL: {resource.url}
            Type: {resource.resource_type}
            Difficulty: {resource.difficulty_level}
            
            Provide analysis in JSON format:
            {{
                "quality_score": 8.5,
                "educational_value": "High - covers practical skills",
                "content_accuracy": "Well-researched and current",
                "target_audience": "Intermediate professionals",
                "strengths": ["Clear explanations", "Practical examples"],
                "weaknesses": ["Could use more examples"],
                "recommendations": "Excellent for professionals learning X"
            }}
            """
            
            message = self.ai_services.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            content = message.content[0].text
            
            # Parse JSON from response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1]
            
            return json.loads(content.strip())
            
        except Exception as e:
            logger.error(f"Error analyzing with Anthropic: {e}")
            return None

    async def _analyze_with_openai(self, resource: ResourceDiscoveryResult) -> Optional[Dict[str, Any]]:
        """Analyze resource using OpenAI GPT"""
        
        if not self.ai_services.openai_client:
            return None
        
        try:
            analysis_prompt = f"""
            Analyze this educational resource for quality and educational value:
            
            Title: {resource.title}
            Description: {resource.description}
            URL: {resource.url}
            Type: {resource.resource_type}
            Difficulty: {resource.difficulty_level}
            
            Provide a JSON analysis with quality score (0-10) and detailed assessment:
            """
            
            response = self.ai_services.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an educational content quality analyst. Provide objective, detailed assessments."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON from response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1]
            
            return json.loads(content.strip())
            
        except Exception as e:
            logger.error(f"Error analyzing with OpenAI: {e}")
            return None
    
    def _default_analysis(self) -> Dict[str, Any]:
        """Default analysis when AI services are unavailable"""
        return {
            'quality_score': 5.0,
            'educational_value': 'Unable to analyze - AI services unavailable',
            'content_accuracy': 'Not analyzed',
            'target_audience': 'General',
            'analysis_method': 'default_fallback'
        }

# Main AI orchestrator
class AIOrchestrator:
    """Main orchestrator for all AI services"""
    
    def __init__(self):
        self.ai_services = AIServicesManager()
        self.skills_engine = SkillsDiscoveryEngine(self.ai_services)
        self.resource_engine = ResourceDiscoveryEngine(self.ai_services)
        self.content_analyzer = ContentAnalyzer(self.ai_services)
    
    async def discover_and_analyze_skills(self, domain: str = "AI and Cybersecurity") -> List[Dict[str, Any]]:
        """Discover emerging skills and analyze them"""
        
        logger.info(f"Starting comprehensive skills discovery for {domain}")
        
        # Discover skills
        skills = await self.skills_engine.discover_emerging_skills(domain)
        
        # Convert to dict format for database storage
        skills_data = []
        for skill in skills:
            skills_data.append({
                'skill_name': skill.skill_name,
                'description': skill.description,
                'category': skill.category,
                'urgency_score': skill.urgency_score,
                'market_demand_evidence': skill.market_demand_evidence,
                'source': skill.source,
                'status': 'active'
            })
        
        logger.info(f"Discovered {len(skills_data)} skills")
        return skills_data
    
    async def discover_and_analyze_resources(self, skill_name: str) -> List[Dict[str, Any]]:
        """Discover and analyze resources for a specific skill"""
        
        logger.info(f"Starting comprehensive resource discovery for {skill_name}")
        
        # Discover resources
        resources = await self.resource_engine.discover_resources_for_skill(skill_name)
        
        # Analyze each resource
        analyzed_resources = []
        for resource in resources:
            analysis = await self.content_analyzer.analyze_resource_quality(resource)
            
            resource_data = {
                'title': resource.title,
                'description': resource.description,
                'url': resource.url,
                'resource_type': resource.resource_type,
                'difficulty_level': resource.difficulty_level,
                'estimated_duration_minutes': resource.estimated_duration_minutes,
                'quality_score': analysis.get('quality_score', resource.quality_score),
                'ai_analysis_summary': json.dumps(analysis),
                'status': 'pending'
            }
            analyzed_resources.append(resource_data)
        
        logger.info(f"Discovered and analyzed {len(analyzed_resources)} resources")
        return analyzed_resources

# Global AI orchestrator instance
ai_orchestrator = AIOrchestrator() 