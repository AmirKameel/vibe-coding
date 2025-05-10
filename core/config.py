"""
Vibe Coding System - Configuration Manager
Handles all configuration settings for the application
"""

import os
from pydantic import BaseSettings, Field
from typing import Dict, Any, Optional, List
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Vibe Coding System"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False)
    
    # Path Settings
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    projects_root_dir: str = Field(default=os.path.join(base_dir, "projects"))
    templates_dir: str = Field(default=os.path.join(base_dir, "templates"))
    
    # Google ADK Settings
    google_api_key: str = Field(default=os.getenv("GOOGLE_API_KEY", ""))
    
    # Gemini Model Settings
    gemini_model: str = Field(default="gemini-flash")  # The Gemini 2 Flash model
    gemini_temperature: float = Field(default=0.2)
    gemini_top_p: float = Field(default=0.8)
    gemini_top_k: int = Field(default=40)
    gemini_max_tokens: int = Field(default=8192)
    
    # Project Structure Templates
    frontend_frameworks: Dict[str, Dict[str, Any]] = {
        "react": {
            "template_dir": "frontend/react",
            "files": [
                {"path": "package.json", "template": "react/package.json"},
                {"path": "src/App.js", "template": "react/App.js"},
                {"path": "src/index.js", "template": "react/index.js"},
            ]
        },
        "vue": {
            "template_dir": "frontend/vue",
            "files": [
                {"path": "package.json", "template": "vue/package.json"},
                {"path": "src/App.vue", "template": "vue/App.vue"},
                {"path": "src/main.js", "template": "vue/main.js"},
            ]
        },
        "angular": {
            "template_dir": "frontend/angular",
            "files": [
                {"path": "package.json", "template": "angular/package.json"},
                {"path": "src/app/app.component.ts", "template": "angular/app.component.ts"},
                {"path": "src/main.ts", "template": "angular/main.ts"},
            ]
        }
    }
    
    backend_frameworks: Dict[str, Dict[str, Any]] = {
        "fastapi": {
            "template_dir": "backend/fastapi",
            "files": [
                {"path": "main.py", "template": "fastapi/main.py"},
                {"path": "requirements.txt", "template": "fastapi/requirements.txt"},
                {"path": "api/routes.py", "template": "fastapi/routes.py"},
            ]
        },
        "flask": {
            "template_dir": "backend/flask",
            "files": [
                {"path": "app.py", "template": "flask/app.py"},
                {"path": "requirements.txt", "template": "flask/requirements.txt"},
                {"path": "api/routes.py", "template": "flask/routes.py"},
            ]
        },
        "django": {
            "template_dir": "backend/django",
            "files": [
                {"path": "manage.py", "template": "django/manage.py"},
                {"path": "requirements.txt", "template": "django/requirements.txt"},
                {"path": "project/settings.py", "template": "django/settings.py"},
            ]
        }
    }
    
    database_templates: Dict[str, Dict[str, Any]] = {
        "postgresql": {
            "template_dir": "database/postgresql",
            "files": [
                {"path": "models.py", "template": "postgresql/models.py"},
                {"path": "db_config.py", "template": "postgresql/db_config.py"},
            ]
        },
        "mongodb": {
            "template_dir": "database/mongodb",
            "files": [
                {"path": "models.py", "template": "mongodb/models.py"},
                {"path": "db_config.py", "template": "mongodb/db_config.py"},
            ]
        },
        "sqlite": {
            "template_dir": "database/sqlite",
            "files": [
                {"path": "models.py", "template": "sqlite/models.py"},
                {"path": "db_config.py", "template": "sqlite/db_config.py"},
            ]
        }
    }
    
    ai_templates: Dict[str, Dict[str, Any]] = {
        "ml_basic": {
            "template_dir": "ai/ml_basic",
            "files": [
                {"path": "model.py", "template": "ml_basic/model.py"},
                {"path": "train.py", "template": "ml_basic/train.py"},
                {"path": "predict.py", "template": "ml_basic/predict.py"},
            ]
        },
        "nlp": {
            "template_dir": "ai/nlp",
            "files": [
                {"path": "model.py", "template": "nlp/model.py"},
                {"path": "processor.py", "template": "nlp/processor.py"},
                {"path": "train.py", "template": "nlp/train.py"},
            ]
        }
    }
    
    deployment_templates: Dict[str, Dict[str, Any]] = {
        "docker": {
            "template_dir": "deployment/docker",
            "files": [
                {"path": "Dockerfile", "template": "docker/Dockerfile"},
                {"path": "docker-compose.yml", "template": "docker/docker-compose.yml"},
                {"path": ".dockerignore", "template": "docker/.dockerignore"},
            ]
        },
        "kubernetes": {
            "template_dir": "deployment/kubernetes",
            "files": [
                {"path": "deployment.yaml", "template": "kubernetes/deployment.yaml"},
                {"path": "service.yaml", "template": "kubernetes/service.yaml"},
                {"path": "configmap.yaml", "template": "kubernetes/configmap.yaml"},
            ]
        }
    }
    
    # Project structure definitions
    default_project_structure: Dict[str, List[str]] = {
        "frontend": ["src", "public", "assets"],
        "backend": ["api", "models", "services", "utils"],
        "docs": ["api", "user_guide", "development"],
    }
    
    # Agent settings
    agent_prompts: Dict[str, str] = {
        "project_manager": """
        You are a Project Manager Agent that specializes in understanding user requirements,
        breaking them down into clear tasks, and coordinating the development of software projects.
        Your responsibilities include:
        
        1. Understanding user requirements comprehensively
        2. Creating detailed project plans with clear task breakdowns
        3. Designing system architecture that meets requirements
        4. Coordinating between specialized agents (Frontend, Backend, AI, Documentation)
        5. Ensuring project deliverables meet or exceed user expectations
        6. Final verification and quality assurance
        
        Approach each project methodically, considering best practices in software development,
        and ensure all components work together seamlessly.
        """,
        
        "frontend": """
        You are a Frontend Development Agent specializing in creating responsive, 
        accessible, and visually appealing user interfaces. Your responsibilities include:
        
        1. Implementing UI/UX designs with clean, semantic code
        2. Creating responsive layouts that work across devices
        3. Implementing interactive components and client-side logic
        4. Integrating with backend APIs effectively
        5. Following frontend best practices for performance and accessibility
        
        You work primarily with frameworks like React, Vue, or Angular, and you understand
        modern CSS practices, JavaScript/TypeScript, and frontend build tools.
        """,
        
        "backend": """
        You are a Backend Development Agent specializing in server-side logic, 
        APIs, databases, and infrastructure. Your responsibilities include:
        
        1. Designing and implementing API endpoints
        2. Creating data models and database schemas
        3. Implementing business logic and service layers
        4. Ensuring security, performance, and scalability
        5. Setting up authentication and authorization systems
        
        You work primarily with frameworks like FastAPI, Flask, or Django, and you understand
        database systems, API design principles, and backend security best practices.
        """,
        
        "ai": """
        You are an AI Development Agent specializing in machine learning, natural language processing,
        and data science integration into applications. Your responsibilities include:
        
        1. Designing ML/AI components that solve specific problems
        2. Implementing data processing pipelines
        3. Creating model training and inference code
        4. Integrating AI capabilities with the main application
        5. Ensuring AI components are efficient and effective
        
        You understand ML frameworks, data processing techniques, and how to integrate AI
        capabilities into software applications effectively.
        """,
        
        "technical_writer": """
        You are a Technical Documentation Agent specializing in creating clear, concise,
        and comprehensive documentation. Your responsibilities include:
        
        1. Creating system architecture documentation
        2. Writing API documentation and reference guides
        3. Creating user guides and tutorials
        4. Documenting setup and deployment procedures
        5. Ensuring documentation is accurate and accessible
        
        You understand technical concepts across frontend, backend, and AI domains,
        and can explain them clearly to both technical and non-technical audiences.
        """
    }
    
    # Configure API clients
    def setup_gemini(self):
        """Configure the Gemini API client"""
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
        else:
            raise ValueError("Google API key not set. Please set GOOGLE_API_KEY environment variable.")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"