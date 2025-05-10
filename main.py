"""
Vibe Coding System - Main Application Entry Point
Built with Google ADK, FastAPI, and Gemini 2 Flash
"""

import os
import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
import json
import shutil

# Local imports
from agents.project_manager import ProjectManagerAgent
from agents.frontend import FrontendAgent
from agents.backend import BackendAgent
from agents.ai import AIAgent
from agents.technical_writer import TechnicalWriterAgent
from core.file_manager import FileManager
from core.config import Settings
from core.utils import setup_logging

# Initialize settings and logging
settings = Settings()
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="Vibe Coding System",
    description="An advanced coding system using Google ADK and Gemini 2 Flash for automated code generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
file_manager = FileManager(settings.projects_root_dir)
project_manager = ProjectManagerAgent(settings, file_manager)
frontend_agent = FrontendAgent(settings, file_manager)
backend_agent = BackendAgent(settings, file_manager)
ai_agent = AIAgent(settings, file_manager)
tech_writer = TechnicalWriterAgent(settings, file_manager)

# In-memory store for active projects
active_projects = {}

class ProjectRequest(BaseModel):
    project_name: str
    description: str
    frontend_framework: Optional[str] = "react"
    backend_framework: Optional[str] = "fastapi"
    database: Optional[str] = "postgresql"
    include_ai: Optional[bool] = False
    deployment_target: Optional[str] = "docker"
    
class ProjectStatus(BaseModel):
    project_id: str
    status: str
    progress: float
    details: Optional[Dict] = None

@app.get("/")
async def root():
    return {"message": "Welcome to Vibe Coding System API"}

@app.post("/project", response_model=Dict)
async def create_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    """Create a new coding project based on the description"""
    project_id = str(uuid.uuid4())
    
    # Create project record
    active_projects[project_id] = {
        "id": project_id,
        "name": request.project_name,
        "status": "initializing",
        "progress": 0.0,
        "details": {
            "description": request.description,
            "frontend_framework": request.frontend_framework,
            "backend_framework": request.backend_framework,
            "database": request.database,
            "include_ai": request.include_ai,
            "deployment_target": request.deployment_target,
            "created_files": []
        }
    }
    
    # Start project generation in background
    background_tasks.add_task(
        process_project_request,
        project_id,
        request
    )
    
    return {
        "project_id": project_id, 
        "message": "Project creation initiated",
        "status_endpoint": f"/project/{project_id}/status"
    }

@app.get("/project/{project_id}/status", response_model=ProjectStatus)
async def get_project_status(project_id: str):
    """Get the current status of a project"""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = active_projects[project_id]
    return ProjectStatus(
        project_id=project_id,
        status=project["status"],
        progress=project["progress"],
        details=project["details"]
    )

@app.get("/project/{project_id}/download")
async def download_project(project_id: str):
    """Get download link for the completed project"""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = active_projects[project_id]
    if project["status"] != "completed":
        raise HTTPException(status_code=400, detail="Project not ready for download")
    
    # In a real implementation, this would generate a download URL
    # Here we just return the path
    project_path = os.path.join(settings.projects_root_dir, project["name"])
    return {"download_path": project_path}

@app.delete("/project/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = active_projects[project_id]
    project_path = os.path.join(settings.projects_root_dir, project["name"])
    
    # Remove the project directory
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    
    # Remove from active projects
    del active_projects[project_id]
    return {"message": "Project deleted successfully"}

async def process_project_request(project_id: str, request: ProjectRequest):
    """Process a project request using the agent architecture"""
    try:
        project = active_projects[project_id]
        project_path = os.path.join(settings.projects_root_dir, request.project_name)
        
        # Set up clean project directory
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
        os.makedirs(project_path)
        
        # Update status
        project["status"] = "planning"
        project["progress"] = 0.1
        
        # Step 1: Project Manager creates plan
        logger.info(f"Project {project_id}: Creating project plan")
        project_plan = await project_manager.create_project_plan(
            project_id=project_id,
            project_name=request.project_name,
            description=request.description,
            frontend_framework=request.frontend_framework,
            backend_framework=request.backend_framework,
            database=request.database,
            include_ai=request.include_ai,
            deployment_target=request.deployment_target
        )
        
        # Update status
        project["status"] = "designing_architecture"
        project["progress"] = 0.2
        project["details"]["project_plan"] = project_plan
        
        # Step 2: Project Manager creates architecture
        logger.info(f"Project {project_id}: Creating architecture")
        architecture = await project_manager.create_architecture(
            project_id=project_id,
            project_plan=project_plan
        )
        
        # Update status
        project["status"] = "creating_frontend"
        project["progress"] = 0.3
        project["details"]["architecture"] = architecture
        
        # Step 3: Frontend Agent creates UI/UX
        logger.info(f"Project {project_id}: Creating frontend")
        frontend_tasks = project_plan.get("frontend_tasks", [])
        frontend_results = await frontend_agent.implement_frontend(
            project_id=project_id,
            project_name=request.project_name,
            tasks=frontend_tasks,
            architecture=architecture.get("frontend", {})
        )
        
        # Update status
        project["status"] = "creating_backend"
        project["progress"] = 0.5
        project["details"]["frontend_results"] = frontend_results
        
        # Step 4: Backend Agent creates server code
        logger.info(f"Project {project_id}: Creating backend")
        backend_tasks = project_plan.get("backend_tasks", [])
        backend_results = await backend_agent.implement_backend(
            project_id=project_id,
            project_name=request.project_name,
            tasks=backend_tasks,
            architecture=architecture.get("backend", {})
        )
        
        # Update status
        project["progress"] = 0.7
        project["details"]["backend_results"] = backend_results
        
        # Step 5: AI Agent creates AI components if needed
        ai_results = {}
        if request.include_ai:
            project["status"] = "creating_ai_components"
            logger.info(f"Project {project_id}: Creating AI components")
            ai_tasks = project_plan.get("ai_tasks", [])
            ai_results = await ai_agent.implement_ai_components(
                project_id=project_id,
                project_name=request.project_name,
                tasks=ai_tasks,
                architecture=architecture.get("ai", {})
            )
            project["details"]["ai_results"] = ai_results
        
        # Update status
        project["status"] = "creating_documentation"
        project["progress"] = 0.8
        
        # Step 6: Technical Writer creates documentation
        logger.info(f"Project {project_id}: Creating documentation")
        doc_results = await tech_writer.create_documentation(
            project_id=project_id,
            project_name=request.project_name,
            project_plan=project_plan,
            architecture=architecture,
            frontend_results=frontend_results,
            backend_results=backend_results,
            ai_results=ai_results
        )
        
        # Update status
        project["status"] = "finalizing"
        project["progress"] = 0.9
        project["details"]["doc_results"] = doc_results
        
        # Step 7: Project Manager finalizes project
        logger.info(f"Project {project_id}: Finalizing project")
        final_report = await project_manager.finalize_project(
            project_id=project_id,
            project_name=request.project_name
        )
        
        # Update status
        project["status"] = "completed"
        project["progress"] = 1.0
        project["details"]["final_report"] = final_report
        project["details"]["created_files"] = file_manager.get_project_files(request.project_name)
        
        logger.info(f"Project {project_id}: Completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing project {project_id}: {str(e)}")
        project = active_projects.get(project_id)
        if project:
            project["status"] = "error"
            project["details"]["error"] = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)