# EdTech NLP-to-SQL Backend Service

A modern AI-powered backend service that converts natural language questions into SQL queries and returns results from an EdTech database. Perfect for enabling non-technical users to query educational data without knowing SQL.

## 🎯 Features

- **Natural Language Processing**: Convert English questions to SQL queries
- **LLM Integration**: Optional OpenAI integration for advanced queries
- **Rule-Based Fallback**: Works without API keys using pattern matching
- **Safe Query Execution**: Only SELECT queries allowed, no DELETE/DROP/UPDATE
- **Analytics Dashboard**: Track query patterns, popular keywords, and performance
- **Docker & Kubernetes Ready**: Complete containerization setup
- **Comprehensive Testing**: Unit tests for all components
- **RESTful API**: Clean FastAPI endpoints

## 🏗️ Architecture

```
┌─────────────┐
│ Client App  │
└──────┬──────┘
       │ POST /query
       ▼
┌──────────────────┐
│   FastAPI App    │─── Validates ──────┐
│  /query /stats   │                     │
└──────┬───────────┘                     │
       │                                 │
       ▼                                 │
┌─────────────────────────────────────────┐
│  NLP to SQL Converter                    │
│  • LLM-based (OpenAI)                   │
│  • Rule-based (Pattern matching)        │
└──────────┬──────────────────────────────┘
           │ Generate SQL
           ▼
┌──────────────────────────────────────────┐
│  SQL Executor                             │
│  • Safety validation                      │
│  • Query execution                        │
│  • Error handling                         │
└──────────┬────────────────────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐  ┌──────────────┐
│Database │  │ Analytics    │
│ (SQLite)│  │ Query Logger │
└─────────┘  └──────────────┘
```

### Database Schema

```
students
├── id (PRIMARY KEY)
├── name
├── grade
└── created_at

courses
├── id (PRIMARY KEY)
├── name
└── category

enrollments
├── id (PRIMARY KEY)
├── student_id (FK)
├── course_id (FK)
└── enrolled_at
```

## 📋 Supported Queries

The system handles these natural language patterns out of the box:

1. **Count Students**: "How many students are there?"
2. **Count Courses**: "How many courses exist?"
3. **Filter by Category**: "Show courses in the Programming category"
4. **Filter by Grade**: "Show all students in grade 10"
5. **Count Enrollments**: "How many students enrolled in Python courses in 2024?"
6. **Popular Content**: "Which course is most popular?"
7. **Distribution**: "What's the grade distribution of students?"
8. **Relationships**: "Show me students with their courses"

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)
- Kubernetes cluster (optional)

### Local Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd edtech-nlp-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Run the application**:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

3. **Access API documentation**:
```
http://localhost:8000/docs  (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

### Using Docker

1. **Build image**:
```bash
docker build -t edtech-nlp-api:latest .
```

2. **Run container**:
```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  edtech-nlp-api:latest
```

3. **Health check**:
```bash
curl http://localhost:8000/health
```

### Kubernetes Deployment

1. **Build and push image** (use your registry):
```bash
docker build -t your-registry/edtech-nlp-api:latest .
docker push your-registry/edtech-nlp-api:latest
```

2. **Update image in kubernetes.yaml**:
```yaml
image: your-registry/edtech-nlp-api:latest
```

3. **Deploy**:
```bash
kubectl apply -f kubernetes.yaml
kubectl get pods -n edtech-app
kubectl logs -f deployment/edtech-nlp-api -n edtech-app
```

4. **Access service**:
```bash
kubectl port-forward -n edtech-app svc/edtech-api-service 8000:80
```

## 📡 API Usage

### 1. POST /query - Convert Question to SQL and Execute

**Request**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many students enrolled in Python courses in 2024?"}'
```

**Response**:
```json
{
  "question": "How many students enrolled in Python courses in 2024?",
  "generated_sql": "SELECT COUNT(DISTINCT e.student_id) FROM enrollments e JOIN courses c ON e.course_id = c.id WHERE c.name LIKE '%Python%' AND strftime('%Y', e.enrolled_at) = '2024'",
  "result": 8,
  "execution_time": 0.0234,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### 2. GET /stats - Get Query Analytics

**Request**:
```bash
curl http://localhost:8000/stats
```

**Response**:
```json
{
  "total_queries": 42,
  "common_keywords": {
    "students": 15,
    "courses": 12,
    "python": 8,
    "programming": 6
  },
  "slowest_query": {
    "question": "Show me students with their courses",
    "execution_time": 0.0456,
    "timestamp": "2024-01-15T10:20:15.000000"
  },
  "average_execution_time": 0.0123,
  "recent_queries": [...]
}
```

### 3. GET /health - Health Check

**Request**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest test_main.py -v

# Run specific test class
pytest test_main.py::TestNLPToSQL -v

# Run with coverage
pytest test_main.py --cov=. --cov-report=html
```

**Test Coverage**:
- ✅ NLP to SQL conversion patterns
- ✅ Database query validation
- ✅ API endpoint functionality
- ✅ Edge cases and error handling
- ✅ SQL injection prevention

## 🔐 NLP-to-SQL Approach

### Hybrid Strategy

The system uses a **two-tier approach** for maximum reliability:

#### Tier 1: Rule-Based Conversion (Primary)
- **Pros**: No API calls, instant, no rate limits, works offline
- **Method**: Regex pattern matching for common query types
- **Coverage**: ~80% of typical use cases
- **Examples**:
  - "How many students in grade 10?" → Pattern matched and converted
  - "Show Python courses" → Regex extracts course name

#### Tier 2: LLM-Based Conversion (Fallback)
- **Pros**: Handles complex/novel questions, more flexible
- **Cons**: Requires API key, adds latency, costs money
- **Provider**: OpenAI (GPT-3.5-turbo)
- **Cost**: ~$0.0005-0.001 per query

### Setup LLM Integration (Optional)

1. **Get OpenAI API key**:
   - Visit https://platform.openai.com/api-keys
   - Create new secret key

2. **Set environment variable**:
```bash
export OPENAI_API_KEY="sk-..."
```

Or in `.env` file:
```
OPENAI_API_KEY=sk-...
```

3. **Test LLM integration**:
```python
from nlp_to_sql import NLPToSQLConverter
converter = NLPToSQLConverter()
sql = converter.convert_to_sql("Complex query here...")
print(sql)
```

## 🛡️ Security Features

1. **SQL Injection Prevention**:
   - Only SELECT queries allowed
   - DELETE, DROP, UPDATE, INSERT, ALTER blocked
   - Query validation before execution

2. **Input Validation**:
   - Question length limits
   - Special character handling
   - Type checking with Pydantic

3. **Rate Limiting** (Recommended):
   ```python
   # Add to requirements.txt
   slowapi==0.1.8
   ```

4. **CORS Configuration** (Optional):
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

## 📊 Performance Optimization

### Database Indexing
```sql
-- Recommended indexes for better query performance
CREATE INDEX idx_students_grade ON students(grade);
CREATE INDEX idx_courses_category ON courses(category);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_date ON enrollments(enrolled_at);
```

### Caching Strategy
For high-traffic scenarios, add Redis caching:

```python
# Cache frequently asked questions
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_query_conversion(question: str) -> str:
    return nlp_converter.convert_to_sql(question)
```

## 🐛 Troubleshooting

### Issue: "Database file not found"
**Solution**:
```bash
# Database initializes automatically on first request
# Or manually initialize:
from database import DatabaseManager
db = DatabaseManager()
db.init_database()
```

### Issue: "OpenAI API key not found"
**Solution**:
```bash
# Check if key is set
echo $OPENAI_API_KEY

# System will fallback to rule-based conversion automatically
# No errors - graceful degradation
```

### Issue: Slow queries
**Solution**:
```python
# Check execution_time in response
# Add database indexes
# Monitor with /stats endpoint for slowest queries
```

## 📈 Monitoring

### Analytics Endpoints

The `/stats` endpoint provides:
- **total_queries**: How many queries processed
- **common_keywords**: Most frequently asked topics
- **slowest_query**: Performance bottleneck
- **average_execution_time**: Overall performance
- **recent_queries**: Last 5 queries for debugging

### Logging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

## 🤝 Contributing

Areas for enhancement:
- [ ] Add more NLP patterns for edge cases
- [ ] Implement Redis caching
- [ ] Add query result pagination
- [ ] Support for JOIN optimization
- [ ] Machine learning-based pattern detection
- [ ] GraphQL endpoint
- [ ] WebSocket support for live queries

## 📄 Project Structure

```
edtech-nlp-api/
├── main.py                 # FastAPI application
├── database.py            # Database management
├── nlp_to_sql.py         # NLP conversion logic
├── test_main.py          # Unit tests
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── kubernetes.yaml       # Kubernetes manifest
├── README.md            # This file
└── edtech.db           # SQLite database (auto-created)
```

## 📝 Example Queries

```bash
# Basic counting
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many total students?"}'

# With filtering
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show all students in grade 10"}'

# Complex with joins
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which course is most popular?"}'

# With date filtering
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many students enrolled in Python in 2024?"}'

# Analytics
curl http://localhost:8000/stats | jq .
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_PATH=/app/data/edtech.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# LLM (Optional)
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-3.5-turbo

# Logging
LOG_LEVEL=INFO
```

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLite Docs](https://www.sqlite.org/docs.html)
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review test cases for examples
3. Check API logs: `kubectl logs -f deployment/edtech-nlp-api -n edtech-app`
4. Review error messages in API responses

## ✅ Submission Checklist

- [x] GitHub repository (implementation files provided)
- [x] Working FastAPI app with /query and /stats endpoints
- [x] NLP2SQL logic (rule-based + LLM fallback)
- [x] Database setup with 10+ students, 5+ courses, 20+ enrollments
- [x] Dockerfile for containerization
- [x] Kubernetes YAML with resource limits
- [x] Unit tests with pytest
- [x] Comprehensive README
- [x] Error handling and validation
- [x] Analytics tracking

---

**Created**: January 2024  
**Version**: 1.0.0  
**Status**: Production Ready ✅
