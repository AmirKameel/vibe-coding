"""
Vibe Coding System - Project Manager Agent
The central coordinator for the entire system
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

class ProjectManagerAgent:
    """
    Project Manager Agent is responsible for:
    1. Understanding user requirements
    2. Creating project plans
    3. Designing system architecture
    4. Coordinating with other specialized agents
    5. Final verification of the project
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
        
    async def create_project_plan(
        self,
        project_id: str,
        project_name: str,
        description: str,
        frontend_framework: str,
        backend_framework: str,
        database: str,
        include_ai: bool,
        deployment_target: str
    ) -> Dict[str, Any]:
        """Create a detailed project plan based on user requirements"""
        
        logger.info(f"Creating project plan for {project_name}")
        
        prompt = f"""
        Act as an expert Project Manager for a software development team.
        
        I need a detailed project plan for a software application with the following details:
        
        Project Name: {project_name}
        Description: {description}
        Frontend Framework: {frontend_framework}
        Backend Framework: {backend_framework}
        Database: {database}
        Include AI Components: {"Yes" if include_ai else "No"}
        Deployment Target: {deployment_target}
        
        Create a comprehensive project plan with the following components:
        
        1. Project Overview - A brief summary of the project
        2. Core Features - List of key features to be implemented
        3. Technical Stack - Detailed breakdown of the technologies to be used
        4. Frontend Tasks - Specific tasks for the frontend agent
        5. Backend Tasks - Specific tasks for the backend agent
        6. AI Tasks (if applicable) - Specific tasks for the AI agent
        7. Documentation Requirements - What should be documented
        
        Return your response as a JSON object with the following structure:
        
        ```json
        {{
            "project_overview": "string",
            "core_features": ["string"],
            "technical_stack": {{
                "frontend": ["string"],
                "backend": ["string"],
                "database": ["string"],
                "ai": ["string"],  // Only if include_ai is true
                "deployment": ["string"]
            }},
            "frontend_tasks": [
                {{
                    "task_id": "string",
                    "description": "string",
                    "priority": "high|medium|low",
                    "dependencies": ["task_id"]  // Optional
                }}
            ],
            "backend_tasks": [
                {{
                    "task_id": "string",
                    "description": "string",
                    "priority": "high|medium|low",
                    "dependencies": ["task_id"]  // Optional
                }}
            ],
            "ai_tasks": [  // Only if include_ai is true
                {{
                    "task_id": "string",
                    "description": "string",
                    "priority": "high|medium|low",
                    "dependencies": ["task_id"]  // Optional
                }}
            ],
            "documentation_requirements": ["string"]
        }}
        ```
        
        Be specific, detailed, and practical in your task descriptions.
        """
        
        response = await self.model.generate_content_async(prompt)
        response_text = response.text
        
        # Extract and parse JSON from response
        json_string = clean_json_string(response_text)
        project_plan = parse_json_string(json_string)
        
        # Save the project plan to a file
        project_dir = os.path.join(self.settings.projects_root_dir, project_name)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            
        self.file_manager.write_json(project_name, "project_plan.json", project_plan)
        
        return project_plan
    
    async def create_architecture(
        self,
        project_id: str,
        project_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create system architecture based on the project plan"""
        
        logger.info(f"Creating architecture for project {project_id}")
        
        # Convert project plan to string for the prompt
        project_plan_str = json.dumps(project_plan, indent=2)
        
        prompt = f"""
        Act as an expert Software Architect. Based on the following project plan, 
        create a detailed system architecture:
        
        {project_plan_str}
        
        Create a comprehensive architecture document with the following components:
        
        1. System Overview - Overall architectural approach
        2. Component Diagram - Description of main components and their interactions
        3. Data Flow - How data moves through the system
        4. Frontend Architecture - Component structure, state management, routing
        5. Backend Architecture - API structure, service layers, middleware
        6. Database Schema - Tables/collections, relationships, indexes
        7. AI Components (if applicable) - Machine learning models, data pipelines
        8. Deployment Architecture - Container strategy, services, scaling
        
        Return your response as a JSON object with the following structure:
        
        ```json
        {{
            "system_overview": "string",
            "components": [
                {{
                    "name": "string",
                    "description": "string",
                    "responsibilities": ["string"]
                }}
            ],
            "data_flow": [
                {{
                    "step": "string",
                    "description": "string",
                    "from_component": "string",
                    "to_component": "string",
                    "data": "string"
                }}
            ],
            "frontend": {{
                "components": ["string"],
                "state_management": "string",
                "routing": "string",
                "api_integration": "string",
                "file_structure": {{
                    "directory_name": "string",
                    "description": "string",
                    "files": [
                        {{
                            "file_name": "string",
                            "description": "string"
                        }}
                    ],
                    "subdirectories": [
                        // Recursive structure of the same form
                    ]
                }}
            }},
            "backend": {{
                "api_structure": ["string"],
                "services": ["string"],
                "middleware": ["string"],
                "file_structure": {{
                    "directory_name": "string",
                    "description": "string",
                    "files": [
                        {{
                            "file_name": "string",
                            "description": "string"
                        }}
                    ],
                    "subdirectories": [
                        // Recursive structure of the same form
                    ]
                }}
            }},
            "database": {{
                "schema": [
                    {{
                        "table_name": "string",
                        "description": "string",
                        "fields": [
                            {{
                                "name": "string",
                                "type": "string",
                                "description": "string",
                                "constraints": ["string"]
                            }}
                        ],
                        "relationships": [
                            {{
                                "related_table": "string",
                                "type": "string",
                                "through": "string"  // For many-to-many
                            }}
                        ]
                    }}
                ]
            }},
            "ai": {{ // Only if AI components are included
                "models": [
                    {{
                        "name": "string",
                        "purpose": "string",
                        "inputs": ["string"],
                        "outputs": ["string"],
                        "training_data": "string"
                    }}
                ],
                "data_pipelines": [
                    {{
                        "name": "string",
                        "description": "string",
                        "steps": ["string"]
                    }}
                ],
                "file_structure": {{
                    "directory_name": "string",
                    "description": "string",
                    "files": [
                        {{
                            "file_name": "string",
                            "description": "string"
                        }}
                    ],
                    "subdirectories": [
                        // Recursive structure of the same form
                    ]
                }}
            }},
            "deployment": {{
                "containers": ["string"],
                "services": ["string"],
                "infrastructure": ["string"],
                "scaling_strategy": "string",
                "file_structure": {{
                    "directory_name": "string",
                    "description": "string",
                    "files": [
                        {{
                            "file_name": "string",
                            "description": "string"
                        }}
                    ]
                }}
            }}
        }}
        ```
        
        Be specific and ensure the architecture is implementable with the specified technologies.
        Focus on practical file structures that our agents can create.
        """
        
        response = await self.model.generate_content_async(prompt)
        response_text = response.text
        
        # Extract and parse JSON from response
        json_string = clean_json_string(response_text)
        architecture = parse_json_string(json_string)
        
        # Save the architecture to a file
        self.file_manager.write_json(project_plan.get("project_name", f"project_{project_id}"), "architecture.json", architecture)
        
        return architecture
    
    async def finalize_project(
        self,
        project_id: str,
        project_name: str
    ) -> Dict[str, Any]:
        """Finalize the project and create a summary report"""
        
        logger.info(f"Finalizing project {project_id}")
        
        # Load project plan and architecture
        project_plan = self.file_manager.read_json(project_name, "project_plan.json")
        architecture = self.file_manager.read_json(project_name, "architecture.json")
        
        # Get list of all files created
        files = self.file_manager.get_project_files(project_name)
        
        prompt = f"""
        Act as a Project Manager conducting a final review of a completed software project.
        
        Project Name: {project_name}
        Project ID: {project_id}
        
        The project has been completed. The files generated include:
        
        {json.dumps(files, indent=2)}
        
        Based on the original project plan and architecture, create a final project report with the following:
        
        1. Executive Summary - Brief overview of what was accomplished
        2. Features Implemented - List of features successfully implemented
        3. Technical Overview - Brief description of the technical stack used
        4. Project Structure - Overview of the directory structure
        5. Setup Instructions - How to set up and run the project
        6. Next Steps - Recommendations for future development
        
        Return your response as a JSON object with the following structure:
        
        ```json
        {{
            "executive_summary": "string",
            "features_implemented": ["string"],
            "technical_overview": "string",
            "project_structure": "string",
            "setup_instructions": "string",
            "next_steps": ["string"]
        }}
        ```
        
        Be concise but comprehensive in your report.
        """
        
        response = await self.model.generate_content_async(prompt)
        response_text = response.text
        
        # Extract and parse JSON from response
        json_string = clean_json_string(response_text)
        final_report = parse_json_string(json_string)
        
        # Generate README.md based on the final report
        readme_content = f"""# {project_name}

## Executive Summary
{final_report.get('executive_summary', '')}

## Features Implemented
{"".join([f"- {feature}\\n" for feature in final_report.get('features_implemented', [])])}

## Technical Overview
{final_report.get('technical_overview', '')}

## Project Structure
{final_report.get('project_structure', '')}

## Setup Instructions
{final_report.get('setup_instructions', '')}

## Next Steps
{"".join([f"- {step}\\n" for step in final_report.get('next_steps', [])])}

"""
        
        # Save the final report and README
        self.file_manager.write_json(project_name, "final_report.json", final_report)
        self.file_manager.write_file(project_name, "README.md", readme_content)
        
        return final_report