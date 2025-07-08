# AI-Horizon Ed Platform v2.0 - Product Requirements Document

## 📋 **PROJECT OVERVIEW**

### **Mission Statement**
Build a robust educational platform that helps students and faculty discover and learn emerging AI-related skills needed for workforce preparedness. This platform serves as a critical tool for the NSF-funded AI-Horizon program committee to provide timely, curated learning resources.

### **Context**
- **NSF Grant Project**: Part of workforce transformation initiative
- **Target Audience**: Students, faculty, and workforce preparing for AI-driven job market
- **Deployment**: Public platform at `ed.theaihorizon.org` (Heroku)
- **Integration**: Receives skills intelligence from main AI-Horizon platform

### **Success Criteria**
✅ **Technical Success**: Clean PostgreSQL deployment with zero database corruption issues  
✅ **User Success**: Students can discover skills→find resources→learn→validate competency  
✅ **Committee Success**: Platform aids program committee in delivering timely workforce preparation

---

## 🎯 **CORE REQUIREMENTS**

### **1. PRIMARY USER FLOWS**

#### **Public User (Student/Faculty)**
1. **Skills Discovery**: Browse emerging skills ranked by urgency/demand
2. **Resource Exploration**: Find curated learning materials for specific skills
3. **Learning Path**: Follow structured progression from beginner to competent
4. **Progress Tracking**: Anonymous session-based progress monitoring
5. **Competency Validation**: Take quizzes and complete practical assignments

#### **Admin User (Program Committee)**
1. **Skills Management**: Add, edit, prioritize emerging skills
2. **Resource Curation**: Review, approve, and manage educational content
3. **Content Analysis**: Trigger AI-powered resource discovery and quality assessment
4. **Data Import**: Import skills intelligence from AI-Horizon platform
5. **Analytics Dashboard**: Monitor platform usage and learning outcomes

### **2. CORE FEATURES**

#### **A. Skills Intelligence System**
- **Skills Database**: Maintain catalog of emerging skills with metadata
- **Urgency Scoring**: Rank skills by market demand and timeframe
- **Category Classification**: Organize skills into logical groupings
- **Trend Tracking**: Monitor skill evolution over time
- **Market Evidence**: Link skills to supporting job market data

#### **B. Resource Discovery Engine**
- **Multi-Platform Search**: YouTube, course platforms, documentation, tools
- **AI-Powered Curation**: Automated content discovery using Perplexity API
- **Quality Assessment**: AI-driven scoring of educational value
- **Content Analysis**: LLM-powered understanding of what resources actually teach
- **Batch Processing**: Background processing with progress indicators

#### **C. Learning Experience Platform**
- **Structured Learning Paths**: Beginner → Intermediate → Advanced progression
- **Resource Categorization**: Videos, courses, tools, documentation, practice platforms
- **Time Estimates**: Realistic learning time commitments
- **Progress Tracking**: Anonymous user progress without accounts
- **Competency Validation**: Quizzes and practical assignments

#### **D. AI-Enhanced Content Generation**
- **Auto-Generated Quizzes**: Multiple choice questions from video/document content
- **Practical Assignments**: Coding, configuration, analysis tasks as appropriate
- **Content Comprehension**: Questions that verify understanding, not memorization
- **Adaptive Difficulty**: Assignments matched to resource complexity

#### **E. Administrative Interface**
- **Content Management**: Full CRUD operations for skills and resources
- **Bulk Operations**: Import/export capabilities for large datasets
- **Analytics Dashboard**: Usage statistics and learning outcomes
- **Background Processing**: Queue management for AI tasks
- **Quality Control**: Review and approval workflows

---

## 🏗️ **TECHNICAL ARCHITECTURE**

### **Technology Stack**
- **Backend**: Python 3.9+ with Flask web framework
- **Database**: PostgreSQL 13+ (local development + Heroku production)
- **Frontend**: HTML5, CSS3, JavaScript (responsive design)
- **APIs**: OpenAI, Claude, Perplexity, YouTube Data API v3
- **Deployment**: Heroku with PostgreSQL add-on
- **Version Control**: Git with checkpoint-based backups

### **Database Schema**

#### **Skills Management**
```sql
CREATE TABLE emerging_skills (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    urgency_score FLOAT DEFAULT 0.0,
    market_demand_evidence TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    source VARCHAR(100) -- 'ai_horizon_import', 'manual', 'discovery'
);
```

#### **Educational Resources**
```sql
CREATE TABLE educational_resources (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url VARCHAR(1000) NOT NULL,
    resource_type VARCHAR(100), -- 'video', 'course', 'documentation', 'tool'
    difficulty_level VARCHAR(50), -- 'beginner', 'intermediate', 'advanced'
    estimated_duration_minutes INTEGER,
    quality_score FLOAT DEFAULT 0.0,
    ai_analysis_summary TEXT,
    transcript TEXT, -- Full content for AI analysis
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_analyzed TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending' -- 'pending', 'approved', 'rejected'
);
```

#### **Learning Paths**
```sql
CREATE TABLE skill_learning_paths (
    id SERIAL PRIMARY KEY,
    skill_id INTEGER REFERENCES emerging_skills(id),
    resource_id INTEGER REFERENCES educational_resources(id),
    sequence_order INTEGER,
    path_type VARCHAR(50), -- 'foundation', 'intermediate', 'advanced', 'practical'
    is_required BOOLEAN DEFAULT false,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Assessment System**
```sql
CREATE TABLE quiz_questions (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES educational_resources(id),
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer CHAR(1) NOT NULL,
    explanation TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE practical_assignments (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES educational_resources(id),
    assignment_title VARCHAR(255) NOT NULL,
    assignment_description TEXT NOT NULL,
    assignment_type VARCHAR(50), -- 'coding', 'configuration', 'analysis', 'research'
    estimated_time_minutes INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Anonymous Progress Tracking**
```sql
CREATE TABLE learning_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(255) NOT NULL,
    skill_id INTEGER REFERENCES emerging_skills(id),
    resource_id INTEGER REFERENCES educational_resources(id),
    started_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP,
    progress_percentage FLOAT DEFAULT 0.0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **API Endpoints**

#### **Public API**
- `GET /api/skills` - List all active skills with metadata
- `GET /api/skills/{id}/resources` - Get resources for specific skill
- `GET /api/resources/{id}` - Get detailed resource information
- `GET /api/learning-paths/{skill_id}` - Get structured learning path
- `POST /api/progress/update` - Update anonymous learning progress

#### **Admin API**
- `POST /api/admin/skills` - Create new skill
- `PUT /api/admin/skills/{id}` - Update skill information
- `POST /api/admin/resources/discover` - Trigger resource discovery
- `POST /api/admin/resources/analyze` - Trigger AI content analysis
- `POST /api/admin/import/skills` - Bulk import skills from JSON
- `GET /api/admin/analytics` - Get platform usage statistics

### **AI Integration Architecture**

#### **Content Analysis Pipeline**
1. **Resource Discovery**: Perplexity API searches for educational content
2. **Content Extraction**: YouTube API gets video transcripts
3. **Quality Assessment**: Claude/OpenAI analyzes educational value
4. **Quiz Generation**: LLM creates comprehension questions
5. **Assignment Creation**: AI generates practical exercises
6. **Progress Tracking**: Monitor learning outcomes

#### **Background Processing**
- **Celery/Redis**: Queue management for AI tasks
- **Progress Indicators**: Real-time status updates for admin
- **Batch Processing**: Overnight processing for large discovery jobs
- **Error Handling**: Robust retry mechanisms and logging

---

## 🎨 **USER INTERFACE DESIGN**

### **Design Principles**
- **Consistency**: Match main AI-Horizon platform styling
- **Simplicity**: Clean, focused interface prioritizing learning
- **Accessibility**: Mobile-responsive, keyboard navigation
- **Performance**: Fast loading, minimal JavaScript dependencies

### **Key Pages**

#### **1. Skills Overview (`/`)**
- **Hero Section**: Platform mission and current skills count
- **Skills Grid**: Card-based display with urgency indicators
- **Filtering**: By category, urgency, and difficulty
- **Search**: Real-time skill name/description search

#### **2. Skill Detail (`/skills/{id}`)**
- **Skill Information**: Description, market evidence, urgency score
- **Learning Path**: Structured progression through resources
- **Resource Categories**: Videos, courses, tools, documentation
- **Progress Tracking**: Anonymous completion indicators

#### **3. Resource Detail (`/resources/{id}`)**
- **Resource Information**: Title, description, difficulty, duration
- **Learning Objectives**: What you'll learn from this resource
- **Assessment Options**: Quiz questions and practical assignments
- **Related Resources**: Suggested next steps

#### **4. Learning Paths (`/paths/{skill_id}`)**
- **Visual Progression**: Clear beginner → advanced pathway
- **Time Estimates**: Realistic completion timeframes
- **Prerequisites**: Required knowledge for each step
- **Checkpoint System**: Track progress through learning journey

#### **5. Admin Dashboard (`/admin`)**
- **Overview Metrics**: Skills, resources, user activity
- **Content Management**: CRUD operations for all entities
- **Discovery Queue**: Manage background AI processing
- **Analytics**: Usage patterns and learning outcomes

### **Mobile Responsiveness**
- **Progressive Web App**: Offline capabilities for resource access
- **Touch-Friendly**: Large buttons, easy navigation
- **Optimized Images**: Fast loading on mobile connections
- **Simplified Layout**: Collapsible sections for mobile viewing

---

## 🔧 **IMPLEMENTATION PHASES**

### **Phase 1: Foundation (Week 1)**
- ✅ **Database Setup**: PostgreSQL schema with all tables
- ✅ **Basic Flask App**: Routes, templates, database connections
- ✅ **Admin Authentication**: Simple login system
- ✅ **Skills CRUD**: Create, read, update, delete skills
- ✅ **Resources CRUD**: Basic resource management

### **Phase 2: Core Features (Week 2)**
- ✅ **Public Interface**: Skills browsing and resource viewing
- ✅ **Learning Paths**: Structured skill progression
- ✅ **Progress Tracking**: Anonymous session management
- ✅ **Search & Filtering**: User-friendly skill discovery
- ✅ **Responsive Design**: Mobile-friendly layouts

### **Phase 3: AI Integration (Week 3)**
- ✅ **API Integrations**: OpenAI, Claude, Perplexity, YouTube
- ✅ **Content Discovery**: Automated resource finding
- ✅ **Quality Assessment**: AI-powered content scoring
- ✅ **Quiz Generation**: Auto-created comprehension questions
- ✅ **Assignment Creation**: Practical exercise generation

### **Phase 4: Advanced Features (Week 4)**
- ✅ **Background Processing**: Queue system for AI tasks
- ✅ **Bulk Operations**: Import/export capabilities
- ✅ **Analytics Dashboard**: Usage and learning metrics
- ✅ **Error Handling**: Robust error management and logging
- ✅ **Performance Optimization**: Caching and database optimization

### **Phase 5: Deployment & Testing (Week 5)**
- ✅ **Heroku Deployment**: Production environment setup
- ✅ **Domain Configuration**: ed.theaihorizon.org setup
- ✅ **Data Migration**: Import from AI-Horizon platform
- ✅ **User Testing**: Validation with real users
- ✅ **Performance Monitoring**: Production health checks

---

## 📊 **DATA REQUIREMENTS**

### **Skills Intelligence Import**
```json
{
  "skills": [
    {
      "name": "AI-Enhanced SIEM",
      "description": "Security Information and Event Management enhanced with AI",
      "category": "Cybersecurity",
      "urgency_score": 8.5,
      "market_demand_evidence": "73% increase in job postings requiring AI-SIEM skills",
      "source": "ai_horizon_analysis_2024"
    }
  ]
}
```

### **Resource Discovery Parameters**
```json
{
  "discovery_config": {
    "platforms": ["youtube", "coursera", "udemy", "github"],
    "content_types": ["video", "course", "documentation", "tool"],
    "quality_threshold": 0.7,
    "max_results_per_skill": 20,
    "ai_analysis_enabled": true
  }
}
```

### **Learning Analytics**
```json
{
  "session_analytics": {
    "total_sessions": 1250,
    "avg_session_duration": 45,
    "completion_rate": 0.68,
    "popular_skills": ["AI-Enhanced SIEM", "Zero Trust Architecture"],
    "resource_engagement": {
      "videos": 0.78,
      "courses": 0.65,
      "documentation": 0.42
    }
  }
}
```

---

## 🔒 **SECURITY & PRIVACY**

### **Data Privacy**
- **Anonymous Learning**: No personal data collection for learners
- **Session Tokens**: Temporary, non-identifying progress tracking
- **GDPR Compliance**: Minimal data collection, user control
- **Secure API Keys**: Environment variables, no hardcoded secrets

### **Security Measures**
- **Authentication**: Secure admin login with session management
- **Input Validation**: Prevent SQL injection and XSS attacks
- **Rate Limiting**: Protect APIs from abuse
- **HTTPS**: Secure connections for all data transmission

---

## 🚀 **DEPLOYMENT STRATEGY**

### **Development Environment**
- **Local PostgreSQL**: `ai_horizon_local` database
- **Environment Variables**: `.env` file with API keys
- **Flask Development Server**: `flask run` for local testing
- **Database Migrations**: Version-controlled schema changes

### **Production Deployment**
- **Heroku Platform**: Managed PostgreSQL and web hosting
- **Custom Domain**: `ed.theaihorizon.org`
- **Environment Config**: Heroku config vars for API keys
- **Monitoring**: Application performance and error tracking

### **Backup Strategy**
- **Code Checkpoints**: Git tags for stable releases
- **Database Backups**: Automated PostgreSQL dumps
- **Configuration Snapshots**: Environment variable exports
- **Rollback Capability**: Quick restore to previous stable version

---

## 📈 **SUCCESS METRICS**

### **Technical KPIs**
- **Uptime**: 99.5% availability
- **Response Time**: <2 seconds average page load
- **Error Rate**: <1% of requests fail
- **Database Performance**: <200ms average query time

### **User Engagement KPIs**
- **Active Learning Sessions**: 500+ per month
- **Resource Discovery**: 80% of skills have 10+ resources
- **Completion Rate**: 60% of started learning paths completed
- **Quiz Accuracy**: 75% average correct answers

### **Content Quality KPIs**
- **Resource Quality**: 85% of resources score >0.7 quality rating
- **AI Analysis Coverage**: 90% of resources have AI-generated content
- **Learning Path Completeness**: All skills have beginner→advanced paths
- **Admin Efficiency**: 90% of discovered resources approved within 24 hours

---

## 🎯 **IMMEDIATE NEXT STEPS**

### **For Implementation Team**
1. **Environment Setup**: Install PostgreSQL, configure development environment
2. **Database Creation**: Run schema scripts to create all tables
3. **Flask Application**: Create basic app structure with routes and templates
4. **Admin Interface**: Build simple login and content management
5. **API Integration**: Connect to external services (OpenAI, YouTube, etc.)

### **For Project Owner**
1. **API Key Preparation**: Gather all required API keys for development
2. **Content Planning**: Prepare initial skills list for platform seeding
3. **Design Assets**: Provide any specific branding or style requirements
4. **Testing Plan**: Define acceptance criteria for each phase
5. **Deployment Access**: Ensure Heroku account and domain access

---

## 📞 **SUPPORT & MAINTENANCE**

### **Technical Support**
- **Issue Tracking**: GitHub issues for bug reports and feature requests
- **Documentation**: Comprehensive setup and usage guides
- **Code Reviews**: Quality assurance through peer review
- **Testing**: Automated tests for critical functionality

### **Content Maintenance**
- **Regular Updates**: Monthly review of resource quality and relevance
- **Community Feedback**: User reports of broken links or outdated content
- **AI Model Updates**: Periodic retraining as AI capabilities improve
- **Performance Monitoring**: Continuous optimization of discovery algorithms

---

**This PRD represents a complete, production-ready educational platform that transforms AI workforce intelligence into actionable learning experiences. The system is designed for reliability, scalability, and user success while maintaining the highest standards of technical excellence.**

---

*Document Version: 1.0*  
*Created: July 6, 2025*  
*Status: Ready for Implementation* 