import os
import asyncio
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from functools import wraps

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Fix DATABASE_URL for Heroku (postgres:// -> postgresql://)
database_url = os.getenv('DATABASE_URL', 'postgresql://vincentnestler@localhost/ai_horizon_local')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import AI services after app initialization
try:
    from ai_services import ai_orchestrator
    AI_SERVICES_AVAILABLE = True
    ai_services = ai_orchestrator.ai_services
    logger.info("AI services loaded successfully")
except ImportError as e:
    AI_SERVICES_AVAILABLE = False
    ai_services = None
    logger.warning(f"AI services not available: {e}")

# Thread pool for async AI operations
executor = ThreadPoolExecutor(max_workers=3)

# Database Models
class EmergingSkill(db.Model):
    __tablename__ = 'emerging_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    urgency_score = db.Column(db.Float, default=0.0)
    market_demand_evidence = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(50), default='active')
    source = db.Column(db.String(100))
    
    # Relationships
    learning_paths = db.relationship('SkillLearningPath', backref='skill', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'skill_name': self.skill_name,
            'description': self.description,
            'category': self.category,
            'urgency_score': self.urgency_score,
            'market_demand_evidence': self.market_demand_evidence,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'status': self.status,
            'source': self.source
        }

class EducationalResource(db.Model):
    __tablename__ = 'educational_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(1000), nullable=False)
    resource_type = db.Column(db.String(100))  # 'video', 'course', 'documentation', 'tool'
    difficulty_level = db.Column(db.String(50))  # 'beginner', 'intermediate', 'advanced'
    estimated_duration_minutes = db.Column(db.Integer)
    quality_score = db.Column(db.Float, default=0.0)
    ai_analysis_summary = db.Column(db.Text)
    transcript = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_analyzed = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'approved', 'rejected'
    
    # Relationships
    learning_paths = db.relationship('SkillLearningPath', backref='resource', lazy=True)
    quiz_questions = db.relationship('QuizQuestion', backref='resource', lazy=True)
    assignments = db.relationship('PracticalAssignment', backref='resource', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'resource_type': self.resource_type,
            'difficulty_level': self.difficulty_level,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'quality_score': self.quality_score,
            'ai_analysis_summary': self.ai_analysis_summary,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'status': self.status
        }

class SkillLearningPath(db.Model):
    __tablename__ = 'skill_learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('emerging_skills.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    sequence_order = db.Column(db.Integer)
    path_type = db.Column(db.String(50))  # 'foundation', 'intermediate', 'advanced', 'practical'
    is_required = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class PracticalAssignment(db.Model):
    __tablename__ = 'practical_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    assignment_title = db.Column(db.String(255), nullable=False)
    assignment_description = db.Column(db.Text, nullable=False)
    assignment_type = db.Column(db.String(50))  # 'coding', 'configuration', 'analysis', 'research'
    estimated_time_minutes = db.Column(db.Integer)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class ResourceAnalysis(db.Model):
    __tablename__ = 'resource_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False, unique=True)
    
    # Comprehensive Analysis Fields
    summary = db.Column(db.Text)  # What the resource is about
    key_concepts = db.Column(db.Text)  # JSON array of main concepts
    learning_objectives = db.Column(db.Text)  # What learners will achieve
    prerequisites = db.Column(db.Text)  # What knowledge is needed beforehand
    
    # Wisdom Extraction
    key_takeaways = db.Column(db.Text)  # JSON array of main insights
    actionable_insights = db.Column(db.Text)  # JSON array of practical applications
    best_practices = db.Column(db.Text)  # JSON array of recommended practices
    common_pitfalls = db.Column(db.Text)  # JSON array of things to avoid
    
    # Additional Metadata
    complexity_score = db.Column(db.Float, default=0.0)  # 0-10 complexity rating
    practical_applicability = db.Column(db.Float, default=0.0)  # 0-10 how practical it is
    industry_relevance = db.Column(db.Text)  # JSON array of relevant industries
    
    # AI Analysis Metadata
    ai_model_used = db.Column(db.String(100))
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_confidence = db.Column(db.Float, default=0.0)  # 0-1 confidence score
    analysis_version = db.Column(db.String(50), default='1.0')
    
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    resource = db.relationship('EducationalResource', backref='analysis', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'summary': self.summary,
            'key_concepts': json.loads(self.key_concepts) if self.key_concepts else [],
            'learning_objectives': self.learning_objectives,
            'prerequisites': self.prerequisites,
            'key_takeaways': json.loads(self.key_takeaways) if self.key_takeaways else [],
            'actionable_insights': json.loads(self.actionable_insights) if self.actionable_insights else [],
            'best_practices': json.loads(self.best_practices) if self.best_practices else [],
            'common_pitfalls': json.loads(self.common_pitfalls) if self.common_pitfalls else [],
            'complexity_score': self.complexity_score,
            'practical_applicability': self.practical_applicability,
            'industry_relevance': json.loads(self.industry_relevance) if self.industry_relevance else [],
            'ai_model_used': self.ai_model_used,
            'analysis_confidence': self.analysis_confidence,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class ProjectIdea(db.Model):
    __tablename__ = 'project_ideas'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    
    # Project Details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty_level = db.Column(db.String(50))  # 'beginner', 'intermediate', 'advanced'
    estimated_time_hours = db.Column(db.Integer)
    
    # Project Structure
    objectives = db.Column(db.Text)  # JSON array of project objectives
    deliverables = db.Column(db.Text)  # JSON array of expected deliverables
    success_criteria = db.Column(db.Text)  # JSON array of success metrics
    required_tools = db.Column(db.Text)  # JSON array of tools/technologies needed
    
    # Educational Value
    skills_practiced = db.Column(db.Text)  # JSON array of skills this project reinforces
    concepts_applied = db.Column(db.Text)  # JSON array of concepts from the resource
    real_world_context = db.Column(db.Text)  # How this relates to real work scenarios
    
    # Project Type and Context
    project_type = db.Column(db.String(100))  # 'individual', 'team', 'classroom'
    industry_context = db.Column(db.String(100))  # Which industry this applies to
    
    # AI Generation Metadata
    ai_generated = db.Column(db.Boolean, default=True)
    ai_model_used = db.Column(db.String(100))
    generation_confidence = db.Column(db.Float, default=0.0)
    
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    resource = db.relationship('EducationalResource', backref='project_ideas', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'title': self.title,
            'description': self.description,
            'difficulty_level': self.difficulty_level,
            'estimated_time_hours': self.estimated_time_hours,
            'objectives': json.loads(self.objectives) if self.objectives else [],
            'deliverables': json.loads(self.deliverables) if self.deliverables else [],
            'success_criteria': json.loads(self.success_criteria) if self.success_criteria else [],
            'required_tools': json.loads(self.required_tools) if self.required_tools else [],
            'skills_practiced': json.loads(self.skills_practiced) if self.skills_practiced else [],
            'concepts_applied': json.loads(self.concepts_applied) if self.concepts_applied else [],
            'real_world_context': self.real_world_context,
            'project_type': self.project_type,
            'industry_context': self.industry_context,
            'ai_generated': self.ai_generated,
            'generation_confidence': self.generation_confidence,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class LearningSession(db.Model):
    __tablename__ = 'learning_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(255), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('emerging_skills.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    started_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime)
    progress_percentage = db.Column(db.Float, default=0.0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

# Helper functions
def is_admin_logged_in():
    return 'admin_logged_in' in session

def require_admin():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_admin_logged_in():
                flash('Admin access required', 'error')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Routes
@app.route('/')
def index():
    """Home page showing skills overview"""
    skills = EmergingSkill.query.filter_by(status='active').order_by(EmergingSkill.urgency_score.desc()).all()
    return render_template('index.html', skills=skills)

def get_urgency_explanation(skill):
    """Get urgency explanation based on skill characteristics"""
    urgency_explanations = {
        'AI-Enhanced SIEM': {
            'reason': 'Critical Skills Gap in AI-Driven Security Operations',
            'explanation': 'Organizations are rapidly adopting AI-enhanced SIEM solutions to combat the growing volume and sophistication of cyber threats. The skills gap is widening as traditional security analysts lack the expertise to configure, optimize, and interpret AI-driven security insights.',
            'market_drivers': [
                '73% increase in job postings requiring AI-SIEM skills',
                'Average 40% salary premium for AI-security specialists',
                'Critical shortage of professionals who can bridge AI and security operations'
            ],
            'urgency_level': 'critical',
            'timeline': 'Skills needed immediately - most organizations are struggling to find qualified professionals'
        },
        'Prompt Engineering': {
            'reason': 'Foundation Skill for AI Integration Across All Domains',
            'explanation': 'Prompt engineering has become the universal skill for effectively leveraging AI tools across cybersecurity, development, and business operations. Without this skill, professionals cannot maximize the potential of AI-driven security tools and workflows.',
            'market_drivers': [
                'Required for effective use of AI security tools',
                'Emerging role with 67.5% confidence in new job creation',
                'Critical for AI-augmented threat analysis and response'
            ],
            'urgency_level': 'high',
            'timeline': 'Essential for staying competitive - organizations prioritizing AI-literate professionals'
        },
        'Ethical Hacking': {
            'reason': 'Escalating Cyber Threats Require Proactive Security Testing',
            'explanation': 'The increasing sophistication of cyber attacks demands skilled ethical hackers who can think like attackers to identify vulnerabilities before they are exploited. Traditional security approaches are insufficient against advanced persistent threats.',
            'market_drivers': [
                'Critical skill shortage in cybersecurity workforce',
                'High demand for professionals who can perform advanced penetration testing',
                'Essential for compliance with security frameworks'
            ],
            'urgency_level': 'critical',
            'timeline': 'Immediate need - organizations face constant threat landscape evolution'
        },
        'Zero Trust Architecture': {
            'reason': 'Fundamental Security Model for Modern Distributed Organizations',
            'explanation': 'The shift to remote work, cloud computing, and digital transformation has made traditional perimeter-based security obsolete. Zero Trust Architecture is becoming the standard security framework for organizations.',
            'market_drivers': [
                'Required for modern cloud security implementations',
                'Critical for compliance with evolving security standards',
                'Essential for securing distributed workforce'
            ],
            'urgency_level': 'high',
            'timeline': 'Organizations actively migrating to Zero Trust models'
        },
        'AI Security Engineering': {
            'reason': 'AI Systems Present New Attack Vectors and Security Challenges',
            'explanation': 'As AI systems become integral to business operations, they introduce unique security vulnerabilities. Specialized knowledge is required to secure AI models, data pipelines, and AI-driven applications.',
            'market_drivers': [
                'High demand for professionals who can secure AI systems',
                'New threat vectors emerging from AI implementations',
                'Critical for organizations deploying AI at scale'
            ],
            'urgency_level': 'high',
            'timeline': 'Growing rapidly as AI adoption accelerates'
        },
        'Threat Intelligence with AI': {
            'reason': 'AI-Enhanced Threat Detection is Becoming Standard Practice',
            'explanation': 'Traditional threat intelligence approaches cannot keep pace with the volume and sophistication of modern threats. AI-enhanced threat intelligence provides the speed and accuracy needed for effective threat detection and response.',
            'market_drivers': [
                'New roles such as AI Integration Specialist and Threat Intelligence Analyst with AI Focus',
                'Essential for staying ahead of evolving threat landscape',
                'Critical for effective incident response and prevention'
            ],
            'urgency_level': 'high',
            'timeline': 'Organizations actively seeking AI-enhanced threat capabilities'
        },
        'Vibe Coding': {
            'reason': 'AI-Assisted Development is Revolutionizing Software Creation',
            'explanation': 'Ambient development methodology leveraging AI assistance represents the future of software development. Professionals who master AI-assisted coding will be significantly more productive and valuable.',
            'market_drivers': [
                'AI-assisted development tools becoming standard practice',
                'Significant productivity gains for AI-literate developers',
                'Essential for modern software development workflows'
            ],
            'urgency_level': 'high',
            'timeline': 'AI coding tools rapidly becoming industry standard'
        },
        'Cloud Security Posture Management': {
            'reason': 'Cloud-First Organizations Need Continuous Security Monitoring',
            'explanation': 'As organizations migrate to cloud-first architectures, traditional security monitoring approaches are insufficient. CSPM provides the continuous visibility and control needed for cloud security.',
            'market_drivers': [
                'Critical for cloud transformation security',
                'Required for cloud compliance and governance',
                'Essential for managing complex multi-cloud environments'
            ],
            'urgency_level': 'high',
            'timeline': 'Immediate need for cloud security professionals'
        }
    }
    
    # Get skill-specific explanation or generate generic one
    if skill.skill_name in urgency_explanations:
        return urgency_explanations[skill.skill_name]
    else:
        # Generate generic explanation based on urgency score
        if skill.urgency_score >= 8.0:
            urgency_level = 'critical'
            timeline = 'Immediate need - high market demand'
        elif skill.urgency_score >= 6.5:
            urgency_level = 'high'
            timeline = 'Growing demand - important for career advancement'
        else:
            urgency_level = 'moderate'
            timeline = 'Emerging skill - good for future positioning'
        
        return {
            'reason': f'Emerging Skill in {skill.category or "Technology"} Domain',
            'explanation': skill.market_demand_evidence or 'This skill is showing increasing importance in the current technology landscape.',
            'market_drivers': [
                f'Urgency score: {skill.urgency_score}/10',
                'Identified through AI-powered workforce analysis',
                'Growing importance in modern technology stack'
            ],
            'urgency_level': urgency_level,
            'timeline': timeline
        }

def categorize_resources_by_cost(learning_paths):
    """Categorize resources into free and paid based on URL patterns and analysis"""
    free_resources = []
    paid_resources = []
    
    # Common free resource domains
    free_domains = [
        'youtube.com', 'youtu.be', 'github.com', 'github.io', 
        'docs.microsoft.com', 'docs.aws.amazon.com', 'docs.google.com',
        'kubernetes.io', 'docker.com', 'owasp.org', 'sans.org',
        'nist.gov', 'cisa.gov', 'medium.com', 'dev.to', 'hackernoon.com'
    ]
    
    # Common paid resource domains
    paid_domains = [
        'udemy.com', 'coursera.org', 'pluralsight.com', 'linkedin.com/learning',
        'edx.org', 'udacity.com', 'cybrary.it', 'cloudacademy.com',
        'acloud.guru', 'whizlabs.com', 'stormwind.com'
    ]
    
    for path, resource in learning_paths:
        if resource.url:
            domain = resource.url.split('/')[2].lower() if '/' in resource.url else resource.url.lower()
            
            # Check if it's a known free domain
            is_free = any(free_domain in domain for free_domain in free_domains)
            is_paid = any(paid_domain in domain for paid_domain in paid_domains)
            
            if is_free:
                free_resources.append((path, resource))
            elif is_paid:
                paid_resources.append((path, resource))
            else:
                # Default to free if uncertain (to avoid promoting paid services)
                free_resources.append((path, resource))
        else:
            free_resources.append((path, resource))
    
    return free_resources, paid_resources

@app.route('/skills/<int:skill_id>')
def skill_detail(skill_id):
    """Detailed view of a specific skill"""
    skill = EmergingSkill.query.get_or_404(skill_id)
    
    # Get learning paths for this skill
    learning_paths = db.session.query(SkillLearningPath, EducationalResource)\
        .join(EducationalResource)\
        .filter(SkillLearningPath.skill_id == skill_id)\
        .filter(EducationalResource.status == 'approved')\
        .order_by(SkillLearningPath.sequence_order)\
        .all()
    
    # Get urgency explanation
    urgency_info = get_urgency_explanation(skill)
    
    # Categorize resources by cost
    free_resources, paid_resources = categorize_resources_by_cost(learning_paths)
    
    return render_template('skill_detail.html', 
                         skill=skill, 
                         learning_paths=learning_paths,
                         free_resources=free_resources,
                         paid_resources=paid_resources,
                         urgency_info=urgency_info)

@app.route('/resources/<int:resource_id>')
def resource_detail(resource_id):
    """Detailed view of a specific resource"""
    resource = EducationalResource.query.get_or_404(resource_id)
    quiz_questions = QuizQuestion.query.filter_by(resource_id=resource_id).all()
    assignments = PracticalAssignment.query.filter_by(resource_id=resource_id).all()
    
    return render_template('resource_detail.html', resource=resource, 
                         quiz_questions=quiz_questions, assignments=assignments)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            flash('Admin login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@require_admin()
def admin_dashboard():
    """Admin dashboard"""
    # Get summary statistics
    total_skills = EmergingSkill.query.count()
    total_resources = EducationalResource.query.count()
    pending_resources = EducationalResource.query.filter_by(status='pending').count()
    
    return render_template('admin_dashboard.html', 
                         total_skills=total_skills,
                         total_resources=total_resources,
                         pending_resources=pending_resources)

@app.route('/workflow')
def workflow():
    """Display the AI-powered educational workflow"""
    return render_template('workflow.html')

@app.route('/methodology')
def methodology():
    """Display the AI methodology and decision framework"""
    return render_template('methodology.html')

@app.route('/browse/resources')
def browse_resources():
    """Browse all resources with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '')
    resource_type = request.args.get('resource_type', '')
    search = request.args.get('search', '')
    
    # Build query
    query = EducationalResource.query
    
    if category:
        # Use subquery to avoid duplicates when filtering by category
        skill_ids = db.session.query(EmergingSkill.id).filter(EmergingSkill.category == category).subquery()
        resource_ids = db.session.query(SkillLearningPath.resource_id).filter(SkillLearningPath.skill_id.in_(skill_ids)).subquery()
        query = query.filter(EducationalResource.id.in_(resource_ids))
    
    if resource_type:
        query = query.filter(EducationalResource.resource_type == resource_type)
    
    if search:
        query = query.filter(EducationalResource.title.contains(search))
    
    # Order by quality score descending, then by title for consistency
    query = query.order_by(EducationalResource.quality_score.desc(), EducationalResource.title)
    
    # Paginate
    resources = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Get filter options
    categories = db.session.query(EmergingSkill.category).distinct().all()
    resource_types = db.session.query(EducationalResource.resource_type).distinct().all()
    
    return render_template('browse_resources.html',
                         resources=resources,
                         categories=[c[0] for c in categories],
                         resource_types=[r[0] for r in resource_types],
                         current_category=category,
                         current_resource_type=resource_type,
                         current_search=search)

@app.route('/admin/prompts')
@require_admin()
def admin_prompts():
    """View AI prompts being used in the system"""
    return render_template('admin_prompts.html')

@app.route('/admin/quiz-management')
@require_admin()
def admin_quiz_management():
    """Admin page for managing quiz questions and standardization"""
    try:
        # Get quiz counts per resource
        result = db.session.execute(text(
            'SELECT resource_id, COUNT(*) as question_count FROM quiz_questions GROUP BY resource_id ORDER BY resource_id'
        )).fetchall()
        
        quiz_data = []
        total_quizzes = 0
        quizzes_with_5_questions = 0
        
        for row in result:
            resource_id = row[0]
            question_count = row[1]
            total_quizzes += 1
            
            # Get resource details
            resource = EducationalResource.query.get(resource_id)
            
            if question_count == 5:
                quizzes_with_5_questions += 1
            
            quiz_data.append({
                'resource_id': resource_id,
                'question_count': question_count,
                'title': resource.title if resource else 'Unknown',
                'resource_type': resource.resource_type if resource else 'Unknown',
                'status': 'complete' if question_count == 5 else 'needs_update'
            })
        
        stats = {
            'total_quizzes': total_quizzes,
            'quizzes_with_5_questions': quizzes_with_5_questions,
            'quizzes_needing_updates': total_quizzes - quizzes_with_5_questions
        }
        
        return render_template('admin_quiz_management.html', 
                             quiz_data=quiz_data, 
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Error loading quiz management page: {e}")
        return render_template('admin_quiz_management.html', 
                             quiz_data=[], 
                             stats={'error': str(e)})

@app.route('/api/admin/ai/prompts')
@require_admin()
def get_ai_prompts():
    """Get all AI prompts used in the system"""
    prompts = {
        'skills_discovery': {
            'name': 'Skills Discovery',
            'description': 'Discovers emerging skills using Perplexity API',
            'system_prompt': 'You are an expert workforce analyst specializing in AI and cybersecurity skills trends. Provide detailed, actionable insights about emerging skills with specific market evidence.',
            'user_prompt_template': '''What are the most critical emerging skills needed in {domain} for {timeframe}?
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
- Market demand evidence'''
        },
        'skills_parsing': {
            'name': 'Skills Response Parsing',
            'description': 'Parses Perplexity response into structured skills data',
            'system_prompt': 'You are a data parser. Return only valid JSON arrays.',
            'user_prompt_template': '''Parse this skills analysis into a JSON array of skills objects.
Each skill should have:
- skill_name: concise name
- description: 1-2 sentence description
- category: AI/ML, Cybersecurity, DevOps, etc.
- urgency_score: 1-10 numeric score
- market_demand_evidence: specific evidence mentioned
- confidence_score: 0.0-1.0 based on evidence quality

Text to parse:
{response}

Return only valid JSON array:'''
        },
        'resource_discovery': {
            'name': 'Resource Discovery',
            'description': 'Discovers educational resources for skills',
            'system_prompt': 'You are an educational resource curator specializing in AI and cybersecurity training materials. Find high-quality, current resources.',
            'user_prompt_template': '''Find the best educational resources for learning "{skill_name}" focusing on {resource_type}.

Requirements:
- Current and relevant (2023-2024)
- High quality and credible sources
- Practical and actionable content
- Suitable for professional development

For each resource, provide:
- Title
- Description
- URL
- Difficulty level (Beginner/Intermediate/Advanced)
- Estimated duration
- Why it's valuable'''
        }
    }
    return jsonify(prompts)

@app.route('/api/admin/ai/create-resource-prompt', methods=['POST'])
@require_admin()
def create_masterful_resource_prompt():
    """Create a masterful prompt for resource discovery based on discovered skills"""
    data = request.get_json()
    skills = data.get('skills', [])
    
    if not skills:
        return jsonify({'success': False, 'error': 'No skills provided'})
    
    try:
        # Use AI to create a masterful prompt
        if not ai_services.openai_client:
            return jsonify({'success': False, 'error': 'OpenAI client not available'})
        
        # Analyze the skills to create a comprehensive prompt
        skills_analysis = "\n".join([
            f"- {skill['skill_name']}: {skill['description']} (Urgency: {skill['urgency_score']}/10)"
            for skill in skills
        ])
        
        prompt_creation_request = f"""
        Based on these emerging skills analysis, create a masterful prompt that will help discover the most valuable educational resources:

        DISCOVERED SKILLS:
        {skills_analysis}

        Create a comprehensive prompt that will:
        1. Target resources that cover multiple related skills efficiently
        2. Prioritize hands-on, practical learning materials
        3. Focus on the most urgent and in-demand skills
        4. Find resources that bridge traditional and AI-enhanced approaches
        5. Identify learning paths that build from fundamentals to advanced applications

        The prompt should be detailed, specific, and designed to find resources that will truly prepare learners for these emerging roles.

        Format your response as a JSON object with:
        - "masterful_prompt": the comprehensive prompt text
        - "rationale": explanation of why this prompt will be effective
        - "target_skills": array of skill names this prompt targets
        - "expected_resource_types": array of resource types this prompt should find
        """
        
        response = executor.submit(lambda: ai_services.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert educational strategist and prompt engineer. Create prompts that will discover the most valuable learning resources."},
                {"role": "user", "content": prompt_creation_request}
            ],
            temperature=0.3,
            max_tokens=2000
        ))
        
        response_content = response.result(timeout=60).choices[0].message.content
        
        # Parse JSON response
        if '```json' in response_content:
            response_content = response_content.split('```json')[1].split('```')[0]
        elif '```' in response_content:
            response_content = response_content.split('```')[1]
        
        masterful_prompt_data = json.loads(response_content.strip())
        
        return jsonify({
            'success': True,
            'masterful_prompt': masterful_prompt_data
        })
        
    except Exception as e:
        logger.error(f"Error creating masterful prompt: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api')
def api_documentation():
    """API documentation page"""
    return render_template('api_documentation.html')

@app.route('/api/skills')
def api_skills():
    """API endpoint to get all active skills"""
    skills = EmergingSkill.query.filter_by(status='active').all()
    return jsonify([skill.to_dict() for skill in skills])

@app.route('/api/resources')
def api_resources():
    """API endpoint to get all resources - basic endpoint for frontend"""
    try:
        resources = EducationalResource.query.filter_by(status='approved').all()
        
        return jsonify({
            "resources": [resource.to_dict() for resource in resources],
            "total_count": len(resources),
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        return jsonify({"error": "Failed to get resources"}), 500

@app.route('/api/skills/<int:skill_id>/resources')
def api_skill_resources(skill_id):
    """API endpoint to get resources for a specific skill"""
    learning_paths = db.session.query(SkillLearningPath, EducationalResource)\
        .join(EducationalResource)\
        .filter(SkillLearningPath.skill_id == skill_id)\
        .filter(EducationalResource.status == 'approved')\
        .order_by(SkillLearningPath.sequence_order)\
        .all()
    
    resources = []
    for path, resource in learning_paths:
        resource_dict = resource.to_dict()
        resource_dict['path_type'] = path.path_type
        resource_dict['sequence_order'] = path.sequence_order
        resource_dict['is_required'] = path.is_required
        resources.append(resource_dict)
    
    return jsonify(resources)

@app.route('/api/resources/<int:resource_id>')
def api_resource_detail(resource_id):
    """API endpoint to get detailed resource information"""
    resource = EducationalResource.query.get_or_404(resource_id)
    return jsonify(resource.to_dict())

# AI-Powered Admin API Routes
@app.route('/api/admin/ai/discover-skills', methods=['POST'])
def api_admin_discover_skills():
    """Admin endpoint to discover emerging skills using AI"""
    redirect_response = require_admin()
    if redirect_response:
        return jsonify({'error': 'Admin access required'}), 401
    
    if not AI_SERVICES_AVAILABLE:
        return jsonify({'error': 'AI services not available'}), 503
    
    try:
        data = request.get_json() or {}
        domain = data.get('domain', 'AI and Cybersecurity')
        
        logger.info(f"Starting AI skills discovery for domain: {domain}")
        
        # Run async AI operation in thread pool
        def run_async_discovery():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    ai_orchestrator.discover_and_analyze_skills(domain)
                )
            finally:
                loop.close()
        
        future = executor.submit(run_async_discovery)
        discovered_skills = future.result(timeout=120)  # 2 minute timeout
        
        # Store discovered skills in database
        new_skills_count = 0
        for skill_data in discovered_skills:
            # Check if skill already exists
            existing_skill = EmergingSkill.query.filter_by(
                skill_name=skill_data['skill_name']
            ).first()
            
            if not existing_skill:
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
                new_skills_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Discovered {len(discovered_skills)} skills, added {new_skills_count} new skills',
            'discovered_skills': discovered_skills,
            'new_skills_count': new_skills_count
        })
        
    except Exception as e:
        logger.error(f"Error in AI skills discovery: {e}")
        db.session.rollback()
        return jsonify({'error': f'Skills discovery failed: {str(e)}'}), 500

@app.route('/api/admin/ai/discover-resources/<int:skill_id>', methods=['POST'])
def api_admin_discover_resources(skill_id):
    """Admin endpoint to discover resources for a specific skill using AI"""
    redirect_response = require_admin()
    if redirect_response:
        return jsonify({'error': 'Admin access required'}), 401
    
    if not AI_SERVICES_AVAILABLE:
        return jsonify({'error': 'AI services not available'}), 503
    
    skill = EmergingSkill.query.get_or_404(skill_id)
    
    try:
        logger.info(f"Starting AI resource discovery for skill: {skill.skill_name}")
        
        # Run async AI operation in thread pool
        def run_async_discovery():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    ai_orchestrator.discover_and_analyze_resources(skill.skill_name)
                )
            finally:
                loop.close()
        
        future = executor.submit(run_async_discovery)
        discovered_resources = future.result(timeout=180)  # 3 minute timeout
        
        # Store discovered resources in database
        new_resources_count = 0
        for resource_data in discovered_resources:
            # Check if resource already exists
            existing_resource = EducationalResource.query.filter_by(
                url=resource_data['url']
            ).first()
            
            if not existing_resource:
                new_resource = EducationalResource(
                    title=resource_data['title'],
                    description=resource_data['description'],
                    url=resource_data['url'],
                    resource_type=resource_data['resource_type'],
                    difficulty_level=resource_data['difficulty_level'],
                    estimated_duration_minutes=resource_data['estimated_duration_minutes'],
                    quality_score=resource_data['quality_score'],
                    ai_analysis_summary=resource_data['ai_analysis_summary'],
                    status='pending'  # Require admin approval
                )
                db.session.add(new_resource)
                db.session.flush()  # Get the ID
                
                # Create learning path association
                learning_path = SkillLearningPath(
                    skill_id=skill_id,
                    resource_id=new_resource.id,
                    sequence_order=new_resources_count + 1,
                    path_type=resource_data['difficulty_level'],
                    is_required=False
                )
                db.session.add(learning_path)
                new_resources_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Discovered {len(discovered_resources)} resources, added {new_resources_count} new resources',
            'discovered_resources': discovered_resources,
            'new_resources_count': new_resources_count
        })
        
    except Exception as e:
        logger.error(f"Error in AI resource discovery: {e}")
        db.session.rollback()
        return jsonify({'error': f'Resource discovery failed: {str(e)}'}), 500

@app.route('/api/admin/ai/analyze-resource/<int:resource_id>', methods=['POST'])
def api_admin_analyze_resource(resource_id):
    """Admin endpoint to analyze a resource using AI"""
    redirect_response = require_admin()
    if redirect_response:
        return jsonify({'error': 'Admin access required'}), 401
    
    if not AI_SERVICES_AVAILABLE:
        return jsonify({'error': 'AI services not available'}), 503
    
    resource = EducationalResource.query.get_or_404(resource_id)
    
    try:
        logger.info(f"Starting AI analysis for resource: {resource.title}")
        
        # Create a resource discovery result object for analysis
        from ai_services import ResourceDiscoveryResult
        resource_obj = ResourceDiscoveryResult(
            title=resource.title,
            description=resource.description,
            url=resource.url,
            resource_type=resource.resource_type,
            difficulty_level=resource.difficulty_level,
            estimated_duration_minutes=resource.estimated_duration_minutes,
            quality_score=resource.quality_score,
            ai_analysis_summary=resource.ai_analysis_summary or '',
            source='manual'
        )
        
        # Run async AI analysis in thread pool
        def run_async_analysis():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    ai_orchestrator.content_analyzer.analyze_resource_quality(resource_obj)
                )
            finally:
                loop.close()
        
        future = executor.submit(run_async_analysis)
        analysis_result = future.result(timeout=60)  # 1 minute timeout
        
        # Update resource with analysis results
        resource.quality_score = analysis_result.get('quality_score', resource.quality_score)
        resource.ai_analysis_summary = json.dumps(analysis_result)
        resource.last_analyzed = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Resource analysis completed',
            'analysis_result': analysis_result,
            'updated_resource': resource.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error in AI resource analysis: {e}")
        db.session.rollback()
        return jsonify({'error': f'Resource analysis failed: {str(e)}'}), 500

@app.route('/api/admin/resources/<int:resource_id>/approve', methods=['POST'])
def api_admin_approve_resource(resource_id):
    """Admin endpoint to approve a pending resource"""
    redirect_response = require_admin()
    if redirect_response:
        return jsonify({'error': 'Admin access required'}), 401
    
    resource = EducationalResource.query.get_or_404(resource_id)
    resource.status = 'approved'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Resource approved successfully',
        'resource': resource.to_dict()
    })

@app.route('/api/admin/resources/<int:resource_id>/reject', methods=['POST'])
def api_admin_reject_resource(resource_id):
    """Admin endpoint to reject a pending resource"""
    redirect_response = require_admin()
    if redirect_response:
        return jsonify({'error': 'Admin access required'}), 401
    
    resource = EducationalResource.query.get_or_404(resource_id)
    resource.status = 'rejected'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Resource rejected successfully',
        'resource': resource.to_dict()
    })

@app.route('/api/admin/ai/status')
def api_admin_ai_status():
    """Admin endpoint to check AI services status"""
    redirect_response = require_admin()
    if redirect_response:
        return jsonify({'error': 'Admin access required'}), 401
    
    status = {
        'ai_services_available': AI_SERVICES_AVAILABLE,
        'openai_available': bool(os.getenv('OPENAI_API_KEY')),
        'anthropic_available': bool(os.getenv('ANTHROPIC_API_KEY')),
        'perplexity_available': bool(os.getenv('PERPLEXITY_API_KEY')),
        'youtube_available': bool(os.getenv('YOUTUBE_API_KEY'))
    }
    
    return jsonify(status)

@app.route('/api/admin/check-quiz-counts')
def api_admin_check_quiz_counts():
    """Admin endpoint to check quiz question counts"""
    redirect_response = require_admin()
    if redirect_response:
        return jsonify({'error': 'Admin access required'}), 401
    
    try:
        # Check current quiz question counts using the quiz_questions table
        result = db.session.execute(text(
            'SELECT resource_id, COUNT(*) as question_count FROM quiz_questions GROUP BY resource_id ORDER BY resource_id'
        )).fetchall()
        
        quiz_counts = []
        total_quizzes = 0
        quizzes_with_5_questions = 0
        
        for row in result:
            total_quizzes += 1
            question_count = row[1]
            if question_count == 5:
                quizzes_with_5_questions += 1
            quiz_counts.append({
                'resource_id': row[0],
                'question_count': question_count
            })
        
        return jsonify({
            'quiz_counts': quiz_counts,
            'total_quizzes': total_quizzes,
            'quizzes_with_5_questions': quizzes_with_5_questions,
            'quizzes_needing_updates': total_quizzes - quizzes_with_5_questions
        })
    except Exception as e:
        logger.error(f"Error checking quiz counts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/standardize-quiz-counts', methods=['POST'])
def api_admin_standardize_quiz_counts():
    """Admin endpoint to standardize all quizzes to 5 questions"""
    redirect_response = require_admin()
    if redirect_response:
        return jsonify({'error': 'Admin access required'}), 401
    
    try:
        # Get all resources with quiz questions and their current counts
        result = db.session.execute(text(
            'SELECT resource_id, COUNT(*) as question_count FROM quiz_questions GROUP BY resource_id ORDER BY resource_id'
        )).fetchall()
        
        updated_quizzes = []
        failed_updates = []
        
        for row in result:
            resource_id = row[0]
            current_count = row[1]
            
            if current_count == 5:
                continue  # Already has 5 questions, skip
            
            try:
                # Get the resource for context
                resource = EducationalResource.query.get(resource_id)
                if not resource:
                    failed_updates.append({
                        'resource_id': resource_id,
                        'error': 'Resource not found'
                    })
                    continue
                
                # Clear existing quiz questions
                QuizQuestion.query.filter_by(resource_id=resource_id).delete()
                
                # Prepare resource data
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
                
                # Generate exactly 5 new questions
                new_questions = asyncio.run(ai_services.content_analyzer.generate_quiz_questions(
                    resource_data, analysis_data, 5
                ))
                
                if not new_questions or len(new_questions) != 5:
                    failed_updates.append({
                        'resource_id': resource_id,
                        'error': f'Failed to generate exactly 5 questions (got {len(new_questions) if new_questions else 0})'
                    })
                    continue
                
                # Store new questions in the database
                for q in new_questions:
                    quiz_question = QuizQuestion(
                        resource_id=resource_id,
                        question_text=q['question_text'],
                        option_a=q['option_a'],
                        option_b=q['option_b'],
                        option_c=q['option_c'],
                        option_d=q['option_d'],
                        correct_answer=q['correct_answer'],
                        explanation=q.get('explanation', '')
                    )
                    db.session.add(quiz_question)
                
                updated_quizzes.append({
                    'resource_id': resource_id,
                    'title': resource.title,
                    'old_count': current_count,
                    'new_count': 5
                })
                
            except Exception as e:
                failed_updates.append({
                    'resource_id': resource_id,
                    'error': str(e)
                })
        
        # Commit all updates
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_quizzes': updated_quizzes,
            'failed_updates': failed_updates,
            'total_updated': len(updated_quizzes),
            'total_failed': len(failed_updates)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error standardizing quiz counts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/resources/<int:resource_id>/analyze', methods=['POST'])
@require_admin()
def analyze_resource(resource_id):
    """Trigger comprehensive AI analysis of a resource"""
    try:
        resource = EducationalResource.query.get_or_404(resource_id)
        
        # Check if analysis already exists
        existing_analysis = ResourceAnalysis.query.filter_by(resource_id=resource_id).first()
        if existing_analysis:
            return jsonify({
                'success': False,
                'message': 'Resource already has analysis. Use update endpoint to refresh.'
            }), 400
        
        # Prepare resource data for analysis
        resource_data = {
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'url': resource.url,
            'resource_type': resource.resource_type,
            'difficulty_level': resource.difficulty_level
        }
        
        # Perform comprehensive analysis
        analysis_result = asyncio.run(ai_services.content_analyzer.analyze_resource_comprehensively(resource_data))
        
        if not analysis_result:
            return jsonify({
                'success': False,
                'message': 'Failed to analyze resource'
            }), 500
        
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
        
        return jsonify({
            'success': True,
            'message': 'Resource analysis completed successfully',
            'analysis_id': analysis.id
        })
        
    except Exception as e:
        logger.error(f"Error analyzing resource {resource_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/resources/<int:resource_id>/generate-quiz', methods=['POST'])
@require_admin()
def generate_resource_quiz(resource_id):
    """Generate quiz questions for a resource"""
    try:
        resource = EducationalResource.query.get_or_404(resource_id)
        
        # Clear existing quiz questions
        QuizQuestion.query.filter_by(resource_id=resource_id).delete()
        
        # Prepare resource data
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
        
        # Generate quiz questions (always 5 questions)
        questions = asyncio.run(ai_services.content_analyzer.generate_quiz_questions(
            resource_data, analysis_data, 5
        ))
        
        if not questions:
            return jsonify({
                'success': False,
                'message': 'Failed to generate quiz questions'
            }), 500
        
        # Store questions in database
        stored_questions = []
        for q in questions:
            quiz_question = QuizQuestion(
                resource_id=resource_id,
                question_text=q['question_text'],
                option_a=q['option_a'],
                option_b=q['option_b'],
                option_c=q['option_c'],
                option_d=q['option_d'],
                correct_answer=q['correct_answer'],
                explanation=q.get('explanation', '')
            )
            db.session.add(quiz_question)
            stored_questions.append(quiz_question)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(stored_questions)} quiz questions',
            'questions_count': len(stored_questions)
        })
        
    except Exception as e:
        logger.error(f"Error generating quiz for resource {resource_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Quiz generation failed: {str(e)}'
        }), 500

@app.route('/resources/<int:resource_id>/generate-projects', methods=['POST'])
@require_admin()
def generate_resource_projects(resource_id):
    """Generate project ideas for a resource"""
    try:
        resource = EducationalResource.query.get_or_404(resource_id)
        
        # Clear existing project ideas
        ProjectIdea.query.filter_by(resource_id=resource_id).delete()
        
        # Prepare resource data
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
        
        # Generate project ideas
        num_projects = request.json.get('num_projects', 3)
        projects = asyncio.run(ai_services.content_analyzer.generate_project_ideas(
            resource_data, analysis_data, num_projects
        ))
        
        if not projects:
            return jsonify({
                'success': False,
                'message': 'Failed to generate project ideas'
            }), 500
        
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
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(stored_projects)} project ideas',
            'projects_count': len(stored_projects)
        })
        
    except Exception as e:
        logger.error(f"Error generating projects for resource {resource_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Project generation failed: {str(e)}'
        }), 500

@app.route('/resources/<int:resource_id>/analysis')
def resource_analysis(resource_id):
    """Display comprehensive resource analysis and wisdom extraction"""
    resource = EducationalResource.query.get_or_404(resource_id)
    analysis = ResourceAnalysis.query.filter_by(resource_id=resource_id).first()
    
    # Get skill context
    skill_paths = SkillLearningPath.query.filter_by(resource_id=resource_id).all()
    skills = [path.skill for path in skill_paths]
    
    # Parse JSON fields for template rendering
    if analysis:
        try:
            analysis.key_concepts = json.loads(analysis.key_concepts) if analysis.key_concepts else []
            analysis.key_takeaways = json.loads(analysis.key_takeaways) if analysis.key_takeaways else []
            analysis.actionable_insights = json.loads(analysis.actionable_insights) if analysis.actionable_insights else []
            analysis.best_practices = json.loads(analysis.best_practices) if analysis.best_practices else []
            analysis.common_pitfalls = json.loads(analysis.common_pitfalls) if analysis.common_pitfalls else []
            analysis.industry_relevance = json.loads(analysis.industry_relevance) if analysis.industry_relevance else []
        except (json.JSONDecodeError, TypeError):
            # Handle cases where JSON parsing fails
            analysis.key_concepts = []
            analysis.key_takeaways = []
            analysis.actionable_insights = []
            analysis.best_practices = []
            analysis.common_pitfalls = []
            analysis.industry_relevance = []
    
    return render_template('resource_analysis.html', 
                         resource=resource, 
                         analysis=analysis,
                         skills=skills)

@app.route('/resources/<int:resource_id>/quiz')
def resource_quiz(resource_id):
    """Interactive quiz for a resource"""
    resource = EducationalResource.query.get_or_404(resource_id)
    questions = QuizQuestion.query.filter_by(resource_id=resource_id).all()
    
    # Get skill context
    skill_paths = SkillLearningPath.query.filter_by(resource_id=resource_id).all()
    skills = [path.skill for path in skill_paths]
    
    return render_template('resource_quiz.html', 
                         resource=resource, 
                         questions=questions,
                         skills=skills)

@app.route('/resources/<int:resource_id>/projects')
def resource_projects(resource_id):
    """Display project ideas for a resource"""
    resource = EducationalResource.query.get_or_404(resource_id)
    projects = ProjectIdea.query.filter_by(resource_id=resource_id).all()
    
    # Get skill context
    skill_paths = SkillLearningPath.query.filter_by(resource_id=resource_id).all()
    skills = [path.skill for path in skill_paths]
    
    # Parse JSON fields for template rendering
    for project in projects:
        try:
            project.objectives = json.loads(project.objectives) if project.objectives else []
            project.deliverables = json.loads(project.deliverables) if project.deliverables else []
            project.success_criteria = json.loads(project.success_criteria) if project.success_criteria else []
            project.required_tools = json.loads(project.required_tools) if project.required_tools else []
            project.skills_practiced = json.loads(project.skills_practiced) if project.skills_practiced else []
            project.concepts_applied = json.loads(project.concepts_applied) if project.concepts_applied else []
        except (json.JSONDecodeError, TypeError):
            # Handle cases where JSON parsing fails
            project.objectives = []
            project.deliverables = []
            project.success_criteria = []
            project.required_tools = []
            project.skills_practiced = []
            project.concepts_applied = []
    
    return render_template('resource_projects.html', 
                         resource=resource, 
                         projects=projects,
                         skills=skills)

@app.route('/api/quiz/<int:resource_id>/submit', methods=['POST'])
def submit_quiz(resource_id):
    """Submit quiz answers and get results"""
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        
        questions = QuizQuestion.query.filter_by(resource_id=resource_id).all()
        if not questions:
            return jsonify({'error': 'No questions found'}), 404
        
        # Score the quiz
        results = []
        correct_count = 0
        
        for question in questions:
            user_answer = answers.get(str(question.id), '')
            is_correct = user_answer.upper() == question.correct_answer.upper()
            
            if is_correct:
                correct_count += 1
            
            results.append({
                'question_id': question.id,
                'question_text': question.question_text,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'explanation': question.explanation,
                'options': {
                    'A': question.option_a,
                    'B': question.option_b,
                    'C': question.option_c,
                    'D': question.option_d
                }
            })
        
        total_questions = len(questions)
        score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Determine performance level
        if score_percentage >= 90:
            performance_level = "Excellent"
            performance_message = "Outstanding! You've mastered this material."
        elif score_percentage >= 80:
            performance_level = "Good"
            performance_message = "Well done! You have a solid understanding."
        elif score_percentage >= 70:
            performance_level = "Fair"
            performance_message = "Good effort! Review the material for better understanding."
        else:
            performance_level = "Needs Improvement"
            performance_message = "Consider reviewing the resource before retaking the quiz."
        
        return jsonify({
            'success': True,
            'score': score_percentage,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'performance_level': performance_level,
            'performance_message': performance_message,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error submitting quiz {resource_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Database initialization
def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=9000) 