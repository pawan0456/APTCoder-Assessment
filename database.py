import sqlite3
from typing import List, Union
from datetime import datetime, timedelta
import random


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_path: str = "edtech.db"):
        self.db_path = db_path
        self.conn = None
    
    def init_database(self):
        """Initialize database with tables and sample data"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                grade INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
        ''')
        
        # Seed data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM students")
        if cursor.fetchone()[0] == 0:
            self._seed_data(cursor)
        
        self.conn.commit()
        print(f"✅ Database initialized at {self.db_path}")
    
    def _seed_data(self, cursor):
        """Seed database with sample data"""
        
        # Sample students
        students = [
            ("Alice Johnson", 10),
            ("Bob Smith", 9),
            ("Charlie Davis", 11),
            ("Diana Martinez", 10),
            ("Ethan Brown", 9),
            ("Fiona Wilson", 10),
            ("George Lee", 11),
            ("Hannah Taylor", 9),
            ("Isaac Anderson", 10),
            ("Julia Thomas", 10),
        ]
        
        cursor.executemany(
            "INSERT INTO students (name, grade) VALUES (?, ?)",
            students
        )
        
        # Sample courses
        courses = [
            ("Python Basics", "Programming"),
            ("Advanced Python", "Programming"),
            ("Data Science", "AI/ML"),
            ("Web Development", "Programming"),
            ("Machine Learning", "AI/ML"),
        ]
        
        cursor.executemany(
            "INSERT INTO courses (name, category) VALUES (?, ?)",
            courses
        )
        
        # Create enrollments with varied dates
        student_ids = list(range(1, 11))
        course_ids = list(range(1, 6))
        
        enrollments = []
        for student_id in student_ids:
            # Each student takes 2-3 courses
            num_courses = random.randint(2, 3)
            selected_courses = random.sample(course_ids, num_courses)
            
            for course_id in selected_courses:
                # Mix of 2023 and 2024 enrollments
                year = random.choice([2023, 2024])
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                
                enrolled_at = f"{year}-{month:02d}-{day:02d} {random.randint(8, 18):02d}:00:00"
                enrollments.append((student_id, course_id, enrolled_at))
        
        cursor.executemany(
            "INSERT INTO enrollments (student_id, course_id, enrolled_at) VALUES (?, ?, ?)",
            enrollments
        )
        
        print(f"✅ Seeded {len(students)} students, {len(courses)} courses, and {len(enrollments)} enrollments")
    
    def execute_query(self, sql: str) -> Union[List, int]:
        """
        Execute a SELECT query safely.
        Returns: scalar value, list of tuples, or list of dicts
        """
        if not self.conn:
            self.init_database()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            
            # Fetch results
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            # If single column and single value, return scalar
            if len(columns) == 1 and len(rows) == 1:
                return rows[0][0]
            
            # If single column, return list of values
            if len(columns) == 1:
                return [row[0] for row in rows]
            
            # Return list of dicts
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            return result if result else []
        
        except sqlite3.Error as e:
            raise Exception(f"Database error: {str(e)}")
    
    def is_select_query(self, sql: str) -> bool:
        """Validate that query is a safe SELECT query"""
        sql_upper = sql.strip().upper()
        
        # Only allow SELECT
        if not sql_upper.startswith("SELECT"):
            return False
        
        # Forbid dangerous operations
        forbidden = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        for keyword in forbidden:
            if keyword in sql_upper:
                return False
        
        return True
    
    def get_schema(self) -> dict:
        """Get database schema information"""
        if not self.conn:
            self.init_database()
        
        cursor = self.conn.cursor()
        schema = {}
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            schema[table] = {
                col[1]: col[2] for col in columns  # name: type
            }
        
        return schema
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
