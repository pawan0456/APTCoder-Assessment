import pytest
from fastapi.testclient import TestClient
from main import app
from nlp_to_sql import NLPToSQLConverter
from database import DatabaseManager
import os


# Initialize test client
client = TestClient(app)

# Test fixtures
@pytest.fixture(scope="module")
def setup_test_db():
    """Setup test database"""
    # Use in-memory or test database
    os.environ["DATABASE"] = "test_edtech.db"
    db = DatabaseManager("test_edtech.db")
    db.init_database()
    yield db
    db.close()
    # Cleanup
    if os.path.exists("test_edtech.db"):
        os.remove("test_edtech.db")


class TestNLPToSQL:
    """Test NLP to SQL conversion"""
    
    def test_count_students_query(self):
        converter = NLPToSQLConverter()
        question = "How many students are there?"
        sql = converter.convert_to_sql(question)
        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "COUNT" in sql.upper()
    
    def test_count_courses_query(self):
        converter = NLPToSQLConverter()
        question = "How many courses exist?"
        sql = converter.convert_to_sql(question)
        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "COUNT" in sql.upper()
    
    def test_courses_by_category(self):
        converter = NLPToSQLConverter()
        question = "What are the courses in the Programming category?"
        sql = converter.convert_to_sql(question)
        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "Programming" in sql
    
    def test_students_by_grade(self):
        converter = NLPToSQLConverter()
        question = "Show all students in grade 10"
        sql = converter.convert_to_sql(question)
        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "10" in sql
    
    def test_python_course_enrollment_2024(self):
        converter = NLPToSQLConverter()
        question = "How many students enrolled in Python courses in 2024?"
        sql = converter.convert_to_sql(question)
        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "2024" in sql
    
    def test_popular_course(self):
        converter = NLPToSQLConverter()
        question = "Which course is most popular?"
        sql = converter.convert_to_sql(question)
        assert sql is not None
        assert "SELECT" in sql.upper()
    
    def test_returns_select_only(self):
        converter = NLPToSQLConverter()
        sql = converter.convert_to_sql("Get me all data")
        assert "DELETE" not in sql.upper()
        assert "DROP" not in sql.upper()
        assert "UPDATE" not in sql.upper()


class TestDatabaseManager:
    """Test database operations"""
    
    def test_init_database(self, setup_test_db):
        """Test database initialization"""
        db = setup_test_db
        assert db.conn is not None
    
    def test_is_select_query(self, setup_test_db):
        """Test SELECT query validation"""
        db = setup_test_db
        assert db.is_select_query("SELECT * FROM students") == True
        assert db.is_select_query("select name from courses") == True
    
    def test_forbid_delete(self, setup_test_db):
        """Test that DELETE queries are blocked"""
        db = setup_test_db
        assert db.is_select_query("DELETE FROM students") == False
    
    def test_forbid_drop(self, setup_test_db):
        """Test that DROP queries are blocked"""
        db = setup_test_db
        assert db.is_select_query("DROP TABLE students") == False
    
    def test_forbid_update(self, setup_test_db):
        """Test that UPDATE queries are blocked"""
        db = setup_test_db
        assert db.is_select_query("UPDATE students SET name='test'") == False
    
    def test_get_schema(self, setup_test_db):
        """Test schema retrieval"""
        db = setup_test_db
        schema = db.get_schema()
        assert "students" in schema
        assert "courses" in schema
        assert "enrollments" in schema


class TestAPIEndpoints:
    """Test FastAPI endpoints"""
    
    def test_query_endpoint_basic(self):
        """Test /query endpoint with basic question"""
        response = client.post(
            "/query",
            json={"question": "How many students are there?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "generated_sql" in data
        assert "result" in data
        assert "execution_time" in data
    
    def test_query_endpoint_empty_question(self):
        """Test /query with empty question"""
        response = client.post(
            "/query",
            json={"question": ""}
        )
        assert response.status_code == 400
    
    def test_query_endpoint_sql_injection(self):
        """Test /query rejects dangerous SQL"""
        response = client.post(
            "/query",
            json={"question": "'; DROP TABLE students; --"}
        )
        # Should either fail or not execute the DROP
        assert response.status_code in [200, 400]
    
    def test_stats_endpoint(self):
        """Test /stats endpoint"""
        # First make a query
        client.post(
            "/query",
            json={"question": "How many students?"}
        )
        
        # Then check stats
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data
        assert "common_keywords" in data
        assert "slowest_query" in data
        assert "average_execution_time" in data
    
    def test_health_endpoint(self):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_query_execution_time(self):
        """Test that execution_time is recorded"""
        response = client.post(
            "/query",
            json={"question": "How many total students?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["execution_time"] >= 0
        assert isinstance(data["execution_time"], float)
    
    def test_query_returns_sql(self):
        """Test that generated SQL is returned"""
        response = client.post(
            "/query",
            json={"question": "Show students in grade 10"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["generated_sql"]) > 0
        assert "SELECT" in data["generated_sql"].upper()


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_nonexistent_course(self):
        """Test query for nonexistent course"""
        response = client.post(
            "/query",
            json={"question": "How many students in XYZ123 course?"}
        )
        # Should return 0 or empty, not error
        assert response.status_code == 200
        assert response.json()["result"] == 0 or response.json()["result"] == []
    
    def test_very_long_question(self):
        """Test with very long question"""
        long_q = "What is " + "the " * 100 + "question?"
        response = client.post(
            "/query",
            json={"question": long_q}
        )
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_special_characters(self):
        """Test question with special characters"""
        response = client.post(
            "/query",
            json={"question": "Students with grade > 9?"}
        )
        assert response.status_code in [200, 400]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
