"""
Vibe Coding System - Backend Agent
Responsible for generating backend code based on project requirements
"""

import os
import json
import logging
import google.generativeai as genai
from typing import Dict, List, Any, Optional
import asyncio

from core.config import Settings
from core.file_manager import FileManager
from core.utils import clean_json_string, parse_json_string

logger = logging.getLogger(__name__)

class BackendAgent:
    """
    Backend Agent is responsible for:
    1. Creating API endpoints
    2. Implementing database models and schema
    3. Building authentication and authorization
    4. Implementing business logic and services
    """
    
    def __init__(self, settings: Settings, file_manager: FileManager):
        self.settings = settings
        self.file_manager = file_manager
        self.settings.setup_gemini()
        self.model = genai.GenerativeModel(
            model_name=self.settings.gemini_model,
            generation_config={
                "temperature": self.settings.gemini_temperature,
                "top_p": self.settings.gemini_top_p,
                "top_k": self.settings.gemini_top_k,
                "max_output_tokens": self.settings.gemini_max_tokens,
            }
        )
    
    async def implement_backend(
        self,
        project_id: str,
        project_name: str,
        tasks: List[Dict[str, Any]],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Implement backend code based on tasks and architecture"""
        
        logger.info(f"Implementing backend for project {project_id}")
        
        # Ensure backend directory exists
        backend_dir = os.path.join(self.settings.projects_root_dir, project_name, "backend")
        if not os.path.exists(backend_dir):
            os.makedirs(backend_dir)
        
        results = {
            "completed_tasks": [],
            "created_files": []
        }
        
        # Map priority to order of execution
        priority_map = {"high": 0, "medium": 1, "low": 2}
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: priority_map.get(t.get("priority", "medium"), 1))
        
        # Create project setup first
        setup_result = await self._setup_project_structure(project_name, architecture)
        results["created_files"].extend(setup_result.get("created_files", []))
        
        # Process tasks sequentially
        for task in sorted_tasks:
            task_result = await self._process_task(task, project_name, architecture)
            if task_result:
                results["completed_tasks"].append(task)
                results["created_files"].extend(task_result.get("created_files", []))
        
        # Generate any remaining necessary files
        finalizing_result = await self._finalize_backend(project_name, architecture, sorted_tasks)
        results["created_files"].extend(finalizing_result.get("created_files", []))
        
        return results
    
    async def _setup_project_structure(
        self, 
        project_name: str, 
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set up the initial backend project structure"""
        
        logger.info(f"Setting up backend project structure for {project_name}")
        
        backend_structure = architecture.get("backend", {}).get("file_structure", {})
        technical_stack = architecture.get("technical_stack", {})
        backend_framework = technical_stack.get("backend", ["Express.js"])[0] if technical_stack.get("backend") else "Express.js"
        database_system = technical_stack.get("database", ["MongoDB"])[0] if technical_stack.get("database") else "MongoDB"
        
        created_files = []
        
        # Generate initial project files based on framework
        if "express" in backend_framework.lower() or "node" in backend_framework.lower():
            # Create package.json
            package_json = {
                "name": f"{project_name}-backend",
                "version": "1.0.0",
                "description": f"Backend for {project_name} project",
                "main": "server.js",
                "scripts": {
                    "start": "node server.js",
                    "dev": "nodemon server.js",
                    "test": "jest"
                },
                "dependencies": {
                    "express": "^4.18.2",
                    "mongoose": "^7.0.0" if "mongo" in database_system.lower() else None,
                    "pg": "^8.9.0" if "postgres" in database_system.lower() else None,
                    "mysql2": "^3.1.0" if "mysql" in database_system.lower() else None,
                    "sqlite3": "^5.1.4" if "sqlite" in database_system.lower() else None,
                    "cors": "^2.8.5",
                    "dotenv": "^16.0.3",
                    "jsonwebtoken": "^9.0.0",
                    "bcryptjs": "^2.4.3",
                    "helmet": "^6.0.1",
                    "morgan": "^1.10.0"
                },
                "devDependencies": {
                    "nodemon": "^2.0.20",
                    "jest": "^29.4.3",
                    "supertest": "^6.3.3"
                }
            }
            
            # Remove None values from dependencies
            package_json["dependencies"] = {k: v for k, v in package_json["dependencies"].items() if v is not None}
            
            self.file_manager.write_json(project_name, "backend/package.json", package_json)
            created_files.append("backend/package.json")
            
            # Create server.js
            server_js_content = """const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Import routers
const apiRoutes = require('./routes');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Connect to database
require('./config/database');

// Routes
app.use('/api', apiRoutes);

// Error handling middleware
app.use((err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  res.status(statusCode).json({
    status: 'error',
    statusCode,
    message: err.message
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
"""
            self.file_manager.write_file(project_name, "backend/server.js", server_js_content)
            created_files.append("backend/server.js")
            
            # Create folders structure
            folders = ["routes", "controllers", "models", "middleware", "config", "utils", "tests"]
            for folder in folders:
                folder_path = os.path.join(self.settings.projects_root_dir, project_name, "backend", folder)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    created_files.append(f"backend/{folder}")
            
            # Create index.js in routes folder
            routes_index_content = """const express = require('express');
const router = express.Router();

// Import route modules
// Example: const userRoutes = require('./user.routes');

// Define routes
// Example: router.use('/users', userRoutes);

// Default route
router.get('/', (req, res) => {
  res.json({ message: 'API is working' });
});

module.exports = router;
"""
            self.file_manager.write_file(project_name, "backend/routes/index.js", routes_index_content)
            created_files.append("backend/routes/index.js")
            
            # Create database configuration
            db_config_content = ""
            if "mongo" in database_system.lower():
                db_config_content = """const mongoose = require('mongoose');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/app_database';

mongoose.connect(MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => {
    console.error('Failed to connect to MongoDB', err);
    process.exit(1);
  });

module.exports = mongoose;
"""
            elif "postgres" in database_system.lower():
                db_config_content = """const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/app_database',
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

pool.on('connect', () => {
  console.log('Connected to PostgreSQL');
});

pool.on('error', (err) => {
  console.error('PostgreSQL connection error', err);
  process.exit(1);
});

module.exports = {
  query: (text, params) => pool.query(text, params)
};
"""
            elif "mysql" in database_system.lower():
                db_config_content = """const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'app_database',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// Test connection
pool.getConnection()
  .then(connection => {
    console.log('Connected to MySQL');
    connection.release();
  })
  .catch(err => {
    console.error('Failed to connect to MySQL', err);
    process.exit(1);
  });

module.exports = pool;
"""
            elif "sqlite" in database_system.lower():
                db_config_content = """const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = process.env.DB_PATH || path.resolve(__dirname, '../database.sqlite');

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Failed to connect to SQLite database', err);
    process.exit(1);
  }
  console.log('Connected to SQLite database');
});

// Helper for performing queries
const query = (sql, params = []) => {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
};

module.exports = {
  db,
  query
};
"""
            
            if db_config_content:
                self.file_manager.write_file(project_name, "backend/config/database.js", db_config_content)
                created_files.append("backend/config/database.js")
            
            # Create .env file
            env_content = """# Server Configuration
PORT=5000
NODE_ENV=development

# JWT Secret
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRES_IN=90d

# Database Configuration
"""
            
            if "mongo" in database_system.lower():
                env_content += "MONGODB_URI=mongodb://localhost:27017/app_database\n"
            elif "postgres" in database_system.lower():
                env_content += "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app_database\n"
            elif "mysql" in database_system.lower():
                env_content += """DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=app_database
"""
            elif "sqlite" in database_system.lower():
                env_content += "DB_PATH=./database.sqlite\n"
                
            self.file_manager.write_file(project_name, "backend/.env", env_content)
            created_files.append("backend/.env")
            
            # Create .gitignore
            gitignore_content = """# Dependency directories
node_modules/

# Environment variables
.env

# Logs
logs
*.log
npm-debug.log*

# Coverage directory used by testing tools
coverage/

# SQLite database files
*.sqlite
*.sqlite3

# Editor directories and files
.idea
.vscode
*.swp
*.swo
"""
            self.file_manager.write_file(project_name, "backend/.gitignore", gitignore_content)
            created_files.append("backend/.gitignore")
            
        elif "flask" in backend_framework.lower() or "python" in backend_framework.lower():
            # Create requirements.txt
            requirements_content = """flask==2.3.2
flask-cors==4.0.0
python-dotenv==1.0.0
"""
            
            if "postgres" in database_system.lower():
                requirements_content += "psycopg2-binary==2.9.6\n"
                requirements_content += "SQLAlchemy==2.0.16\n"
            elif "mysql" in database_system.lower():
                requirements_content += "mysql-connector-python==8.0.33\n"
                requirements_content += "SQLAlchemy==2.0.16\n"
            elif "sqlite" in database_system.lower():
                requirements_content += "SQLAlchemy==2.0.16\n"
            elif "mongo" in database_system.lower():
                requirements_content += "pymongo==4.3.3\n"
                
            requirements_content += """pytest==7.3.1
gunicorn==20.1.0
PyJWT==2.7.0
"""
            
            self.file_manager.write_file(project_name, "backend/requirements.txt", requirements_content)
            created_files.append("backend/requirements.txt")
            
            # Create app.py
            app_py_content = """from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from routes import register_routes

# Create Flask app
app = Flask(__name__)
CORS(app)

# Register routes
register_routes(app)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
"""
            self.file_manager.write_file(project_name, "backend/app.py", app_py_content)
            created_files.append("backend/app.py")
            
            # Create folders structure
            folders = ["routes", "controllers", "models", "middlewares", "config", "utils", "tests"]
            for folder in folders:
                folder_path = os.path.join(self.settings.projects_root_dir, project_name, "backend", folder)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    created_files.append(f"backend/{folder}")
                
                # Create __init__.py in each folder
                self.file_manager.write_file(project_name, f"backend/{folder}/__init__.py", "")
                created_files.append(f"backend/{folder}/__init__.py")
            
            # Create routes/__init__.py
            routes_init_content = """from flask import Blueprint, jsonify

# Import route modules
# Example: from .user_routes import user_bp

def register_routes(app):
    # Register all blueprints
    # Example: app.register_blueprint(user_bp, url_prefix='/api/users')
    
    # Default route
    @app.route('/api', methods=['GET'])
    def index():
        return jsonify({"message": "API is working"})
"""
            self.file_manager.write_file(project_name, "backend/routes/__init__.py", routes_init_content)
            created_files.append("backend/routes/__init__.py")
            
            # Create database configuration
            if "mongo" in database_system.lower():
                db_config_content = """from pymongo import MongoClient
import os

# MongoDB connection
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("DB_NAME", "app_database")

try:
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    print("Connected to MongoDB")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    raise

def get_db():
    return db
"""
                self.file_manager.write_file(project_name, "backend/config/database.py", db_config_content)
                created_files.append("backend/config/database.py")
            
            elif "postgres" in database_system.lower() or "mysql" in database_system.lower() or "sqlite" in database_system.lower():
                db_config_content = """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database connection URL
if '""" + database_system.lower() + """' == 'postgresql':
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/app_database")
elif '""" + database_system.lower() + """' == 'mysql':
    DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+mysqlconnector://root:@localhost/app_database")
elif '""" + database_system.lower() + """' == 'sqlite':
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./database.sqlite")

# Create engine
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
"""
                self.file_manager.write_file(project_name, "backend/config/database.py", db_config_content)
                created_files.append("backend/config/database.py")
            
            # Create .env file
            env_content = """# Server Configuration
PORT=5000
FLASK_ENV=development

# JWT Secret
JWT_SECRET=your_jwt_secret_key_here

# Database Configuration
"""
            
            if "mongo" in database_system.lower():
                env_content += """MONGODB_URI=mongodb://localhost:27017/
DB_NAME=app_database
"""
            elif "postgres" in database_system.lower():
                env_content += "DATABASE_URL=postgresql://postgres:postgres@localhost/app_database\n"
            elif "mysql" in database_system.lower():
                env_content += "DATABASE_URL=mysql+mysqlconnector://root:@localhost/app_database\n"
            elif "sqlite" in database_system.lower():
                env_content += "DATABASE_URL=sqlite:///./database.sqlite\n"
                
            self.file_manager.write_file(project_name, "backend/.env", env_content)
            created_files.append("backend/.env")
            
            # Create .gitignore
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# Environment variables
.env

# Logs
logs/
*.log

# SQLite database files
*.sqlite
*.sqlite3

# Editor directories and files
.idea/
.vscode/
*.swp
*.swo
"""
            self.file_manager.write_file(project_name, "backend/.gitignore", gitignore_content)
            created_files.append("backend/.gitignore")
            
        elif "django" in backend_framework.lower():
            # Create requirements.txt
            requirements_content = """django==4.2.2
djangorestframework==3.14.0
django-cors-headers==4.1.0
python-dotenv==1.0.0
gunicorn==20.1.0
"""
            
            if "postgres" in database_system.lower():
                requirements_content += "psycopg2-binary==2.9.6\n"
            elif "mysql" in database_system.lower():
                requirements_content += "mysqlclient==2.1.1\n"
            
            requirements_content += """pytest==7.3.1
pytest-django==4.5.2
PyJWT==2.7.0
"""
            
            self.file_manager.write_file(project_name, "backend/requirements.txt", requirements_content)
            created_files.append("backend/requirements.txt")
            
            # We'll need to create a Django project structure
            # This would typically be done with django-admin startproject
            # For now, we'll simulate the basic structure
            
            django_project_name = project_name.replace("-", "_").lower()
            
           