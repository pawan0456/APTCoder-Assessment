import re
from typing import Dict, List
from database import DatabaseManager


class NLPToSQLConverter:
    """
    Converts natural language questions to SQL queries.
    
    Supports:
    1. LLM-based conversion (primary method)
    2. Rule-based conversion (fallback)
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.rule_patterns = self._build_rule_patterns()
    
    def convert_to_sql(self, question: str) -> str:
        """
        Convert natural language question to SQL.
        
        Strategy:
        1. Try LLM-based conversion (requires OpenAI API)
        2. Fall back to rule-based pattern matching
        3. Fall back to generic SELECT all
        """
        
        # Try rule-based conversion first (more reliable without API)
        sql = self._rule_based_conversion(question)
        
        if sql:
            return sql
        
        # If rules don't match, try LLM (optional - requires API key)
        sql = self._llm_based_conversion(question)
        
        if sql:
            return sql
        
        # Default fallback
        return "SELECT * FROM students LIMIT 10"
    
    def _rule_based_conversion(self, question: str) -> str:
        """
        Rule-based SQL conversion using pattern matching.
        Handles common queries without external API.
        """
        q = question.lower().strip()
        
        # Pattern 1: Count students by course
        # "How many students enrolled in Python courses in 2024?"
        pattern = r"how many students enrolled in (.+?) (?:courses?|course|in)? (?:in )?(\d{4})?"
        match = re.search(pattern, q)
        if match:
            course_name = match.group(1).strip()
            year = match.group(2) if match.group(2) else "2024"
            return self._count_students_by_course(course_name, year)
        
        # Pattern 2: Count courses by category
        # "How many courses are in the Programming category?"
        pattern = r"how many courses? (?:are in the |in the )?(.+?)(?: category)?\?"
        match = re.search(pattern, q)
        if match:
            category = match.group(1).strip()
            return f"""
            SELECT COUNT(*) FROM courses 
            WHERE category LIKE '%{category}%'
            """
        
        # Pattern 3: List students in a specific grade
        # "Show all students in grade 10"
        pattern = r"(?:show|list|get).*?students? (?:in )?grade (\d+)"
        match = re.search(pattern, q)
        if match:
            grade = match.group(1)
            return f"""
            SELECT name, grade FROM students 
            WHERE grade = {grade}
            ORDER BY name
            """
        
        # Pattern 4: Count total students
        # "How many total students?"
        if re.search(r"how many (?:total )?students", q):
            return "SELECT COUNT(*) FROM students"
        
        # Pattern 5: Count total courses
        # "How many courses exist?"
        if re.search(r"how many courses? (?:exist|do we have)", q):
            return "SELECT COUNT(*) FROM courses"
        
        # Pattern 6: Get course details
        # "What are all the courses in AI/ML category?"
        pattern = r"(?:list|show|get).*?courses? (?:in|from) (?:the )?(.+?)(?: category)?\?"
        match = re.search(pattern, q)
        if match:
            category = match.group(1).strip()
            return f"""
            SELECT name, category FROM courses 
            WHERE category LIKE '%{category}%'
            ORDER BY name
            """
        
        # Pattern 7: Enrollments count
        # "How many total enrollments?"
        if re.search(r"how many (?:total )?enrollments?", q):
            return "SELECT COUNT(*) FROM enrollments"
        
        # Pattern 8: Student with most enrollments
        # "Which student has the most courses?"
        pattern = r"which student (?:has|took) (?:the most|the most|most) courses?"
        if re.search(pattern, q):
            return """
            SELECT s.name, COUNT(e.id) as course_count 
            FROM students s
            LEFT JOIN enrollments e ON s.id = e.student_id
            GROUP BY s.id
            ORDER BY course_count DESC
            LIMIT 1
            """
        
        # Pattern 9: Courses with most enrollments
        # "Which course is most popular?"
        pattern = r"(?:which course|what course) (?:is most|has the most) (?:popular|enrollments|students)"
        if re.search(pattern, q):
            return """
            SELECT c.name, COUNT(e.id) as enrollment_count 
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id
            GROUP BY c.id
            ORDER BY enrollment_count DESC
            LIMIT 1
            """
        
        # Pattern 10: Average students per course
        # "What's the average number of students per course?"
        if re.search(r"average (?:number of )?students per course", q):
            return """
            SELECT ROUND(AVG(enrollment_count), 2) as avg_students_per_course
            FROM (
                SELECT COUNT(*) as enrollment_count 
                FROM enrollments 
                GROUP BY course_id
            )
            """
        
        # Pattern 11: List students and their courses
        # "Show me students with their courses"
        pattern = r"(?:show|list).*?students? (?:with|and) their courses?"
        if re.search(pattern, q):
            return """
            SELECT DISTINCT s.name, c.name as course_name
            FROM students s
            LEFT JOIN enrollments e ON s.id = e.student_id
            LEFT JOIN courses c ON e.course_id = c.id
            WHERE c.id IS NOT NULL
            ORDER BY s.name, c.name
            """
        
        # Pattern 12: Grade distribution
        # "What's the distribution of students by grade?"
        pattern = r"(?:distribution|count) (?:of students )?by grade"
        if re.search(pattern, q):
            return """
            SELECT grade, COUNT(*) as student_count
            FROM students
            GROUP BY grade
            ORDER BY grade
            """
        
        return None
    
    def _count_students_by_course(self, course_name: str, year: str) -> str:
        """Build SQL to count students enrolled in specific course"""
        return f"""
        SELECT COUNT(DISTINCT e.student_id) 
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE c.name LIKE '%{course_name}%'
        AND strftime('%Y', e.enrolled_at) = '{year}'
        """
    
    def _llm_based_conversion(self, question: str) -> str:
        """
        Use OpenAI LLM to convert question to SQL (optional).
        Requires OPENAI_API_KEY environment variable.
        
        Fallback to rule-based if API unavailable.
        """
        try:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                return None
            
            import openai
            openai.api_key = api_key
            
            schema_info = self._get_schema_description()
            
            prompt = f"""
Convert this natural language question to a SQL query.

Database schema:
{schema_info}

Question: {question}

Respond with ONLY the SQL query, no explanation.
Make sure the query is valid SQL.
Only use SELECT statements.
Do not use DELETE, DROP, UPDATE, INSERT, or ALTER.
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Convert natural language to SQL."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=200
            )
            
            sql = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            sql = re.sub(r'^```sql\n?', '', sql)
            sql = re.sub(r'\n?```$', '', sql)
            
            return sql
        
        except ImportError:
            # OpenAI library not installed
            return None
        except Exception as e:
            # API error or other issues
            print(f"⚠️ LLM conversion failed: {e}")
            return None
    
    def _get_schema_description(self) -> str:
        """Get human-readable schema description"""
        schema = {
            "students": {
                "id": "INTEGER PRIMARY KEY",
                "name": "TEXT - Student name",
                "grade": "INTEGER - Grade level (9-11)",
                "created_at": "TIMESTAMP"
            },
            "courses": {
                "id": "INTEGER PRIMARY KEY",
                "name": "TEXT - Course name",
                "category": "TEXT - Programming, AI/ML, etc"
            },
            "enrollments": {
                "id": "INTEGER PRIMARY KEY",
                "student_id": "INTEGER - FK to students",
                "course_id": "INTEGER - FK to courses",
                "enrolled_at": "TIMESTAMP"
            }
        }
        
        desc = "Tables:\n"
        for table_name, columns in schema.items():
            desc += f"\n{table_name}:\n"
            for col_name, col_type in columns.items():
                desc += f"  - {col_name}: {col_type}\n"
        
        return desc
    
    def _build_rule_patterns(self) -> List[Dict]:
        """Build list of regex patterns for rule-based conversion"""
        # Already defined in _rule_based_conversion
        return []
