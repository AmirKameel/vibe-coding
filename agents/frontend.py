"""
Vibe Coding System - Frontend Agent
Responsible for generating frontend code based on project requirements
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

class FrontendAgent:
    """
    Frontend Agent is responsible for:
    1. Creating UI/UX components
    2. Implementing frontend logic
    3. Ensuring responsive design
    4. Integration with backend APIs
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
    
    async def implement_frontend(
        self,
        project_id: str,
        project_name: str,
        tasks: List[Dict[str, Any]],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Implement frontend code based on tasks and architecture"""
        
        logger.info(f"Implementing frontend for project {project_id}")
        
        # Ensure frontend directory exists
        frontend_dir = os.path.join(self.settings.projects_root_dir, project_name, "frontend")
        if not os.path.exists(frontend_dir):
            os.makedirs(frontend_dir)
        
        results = {
            "completed_tasks": [],
            "created_files": []
        }
        
        # Map priority to order of execution
        priority_map = {"high": 0, "medium": 1, "low": 2}
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: priority_map.get(t.get("priority", "medium"), 1))
        
        # Process tasks sequentially
        for task in sorted_tasks:
            task_result = await self._process_task(project_name, task, architecture)
            results["completed_tasks"].append({
                "task_id": task.get("task_id"),
                "description": task.get("description"),
                "result": task_result
            })
            results["created_files"].extend(task_result.get("created_files", []))
        
        # Create package.json and configuration files if not already created
        await self._create_config_files(project_name, architecture)
        
        # Save the results to a file
        self.file_manager.write_json(project_name, "frontend/frontend_results.json", results)
        
        return results
    
    async def _process_task(
        self,
        project_name: str,
        task: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single frontend task"""
        
        task_id = task.get("task_id", "unknown")
        description = task.get("description", "")
        
        logger.info(f"Processing frontend task {task_id}: {description}")
        
        # Structure file generation based on task description
        if "component" in description.lower():
            return await self._generate_component(project_name, task, architecture)
        elif "page" in description.lower():
            return await self._generate_page(project_name, task, architecture)
        elif "style" in description.lower():
            return await self._generate_styles(project_name, task, architecture)
        elif "service" in description.lower() or "api" in description.lower():
            return await self._generate_service(project_name, task, architecture)
        else:
            # Generic frontend code generation
            return await self._generate_generic_files(project_name, task, architecture)
    
    async def _generate_component(
        self,
        project_name: str,
        task: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a frontend component based on task description"""
        
        description = task.get("description", "")
        
        # Determine component name from task description
        component_name = self._extract_component_name(description)
        file_structure = architecture.get("file_structure", {})
        
        # Get framework from architecture or use default
        frontend_framework = architecture.get("framework", "react")
        
        # Define file extension based on framework
        extension = ".jsx" if frontend_framework == "react" else ".vue" if frontend_framework == "vue" else ".ts"
        if frontend_framework == "angular":
            file_paths = [
                f"src/app/components/{component_name}/{component_name}.component{extension}",
                f"src/app/components/{component_name}/{component_name}.component.html",
                f"src/app/components/{component_name}/{component_name}.component.css"
            ]
        else:
            file_paths = [f"src/components/{component_name}{extension}"]
        
        created_files = []
        
        for file_path in file_paths:
            prompt = f"""
            Act as an expert frontend developer using {frontend_framework}.
            
            Create a {frontend_framework} component based on the following details:
            
            Component Name: {component_name}
            Task Description: {description}
            
            File Path: {file_path}
            
            The component should:
            1. Follow {frontend_framework} best practices
            2. Be well-structured and maintainable
            3. Include appropriate PropTypes/TypeScript types
            4. Have clean, minimal styling
            5. Include comments explaining complex logic
            
            Implement the component fully without placeholders.
            Only return the complete code for the file without any explanations.
            """
            
            response = await self.model.generate_content_async(prompt)
            code = response.text.strip()
            
            # Clean up code (remove markdown code blocks if present)
            if code.startswith("```") and code.endswith("```"):
                code = "\n".join(code.split("\n")[1:-1])
            
            # Further clean up if language is specified
            for lang in ["jsx", "vue", "typescript", "javascript", "html", "css"]:
                if code.startswith(f"```{lang}") and code.endswith("```"):
                    code = "\n".join(code.split("\n")[1:-1])
            
            # Write component file
            self.file_manager.write_file(project_name, f"frontend/{file_path}", code)
            created_files.append(file_path)
        
        return {
            "component_name": component_name,
            "created_files": created_files
        }
    
    async def _generate_page(
        self,
        project_name: str,
        task: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a frontend page based on task description"""
        
        description = task.get("description", "")
        
        # Determine page name from task description
        page_name = self._extract_page_name(description)
        
        # Get framework from architecture or use default
        frontend_framework = architecture.get("framework", "react")
        
        # Define file extension based on framework
        extension = ".jsx" if frontend_framework == "react" else ".vue" if frontend_framework == "vue" else ".ts"
        if frontend_framework == "angular":
            file_paths = [
                f"src/app/pages/{page_name}/{page_name}.component{extension}",
                f"src/app/pages/{page_name}/{page_name}.component.html",
                f"src/app/pages/{page_name}/{page_name}.component.css"
            ]
        else:
            file_paths = [f"src/pages/{page_name}{extension}"]
        
        created_files = []
        
        for file_path in file_paths:
            prompt = f"""
            Act as an expert frontend developer using {frontend_framework}.
            
            Create a {frontend_framework} page component based on the following details:
            
            Page Name: {page_name}
            Task Description: {description}
            
            File Path: {file_path}
            
            The page should:
            1. Follow {frontend_framework} best practices
            2. Include layout elements (header, footer, main content)
            3. Be responsive
            4. Handle loading/error states if data fetching is involved
            5. Include routing configuration if needed
            
            Implement the page fully without placeholders.
            Only return the complete code for the file without any explanations.
            """
            
            response = await self.model.generate_content_async(prompt)
            code = response.text.strip()
            
            # Clean up code (remove markdown code blocks if present)
            if code.startswith("```") and code.endswith("```"):
                code = "\n".join(code.split("\n")[1:-1])
            
            # Further clean up if language is specified
            for lang in ["jsx", "vue", "typescript", "javascript", "html", "css"]:
                if code.startswith(f"```{lang}") and code.endswith("```"):
                    code = "\n".join(code.split("\n")[1:-1])
            
            # Write page file
            self.file_manager.write_file(project_name, f"frontend/{file_path}", code)
            created_files.append(file_path)
        
        return {
            "page_name": page_name,
            "created_files": created_files
        }
    
    async def _generate_styles(
        self,
        project_name: str,
        task: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate stylesheets based on task description"""
        
        description = task.get("description", "")
        
        # Get framework from architecture or use default
        frontend_framework = architecture.get("framework", "react")
        
        # Determine styling approach from description or use framework-specific default
        styling_approach = "CSS" if "css" in description.lower() else "SCSS" if "scss" in description.lower() else "Tailwind" if "tailwind" in description.lower() else "CSS"
        
        # Define file path based on styling approach
        extension = ".scss" if styling_approach == "SCSS" else ".css"
        file_path = f"src/styles/main{extension}"
        
        prompt = f"""
        Act as an expert frontend stylist using {styling_approach}.
        
        Create styles based on the following details:
        
        Task Description: {description}
        Framework: {frontend_framework}
        Styling Approach: {styling_approach}
        
        File Path: {file_path}
        
        The styles should:
        1. Be well-organized and maintainable
        2. Follow {styling_approach} best practices
        3. Include responsive design (mobile, tablet, desktop)
        4. Use variables for colors, spacing, etc.
        5. Include base styles for common elements
        
        Implement the styles fully without placeholders.
        Only return the complete code for the file without any explanations.
        """
        
        response = await self.model.generate_content_async(prompt)
        code = response.text.strip()
        
        # Clean up code (remove markdown code blocks if present)
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.split("\n")[1:-1])
        
        # Further clean up if language is specified
        for lang in ["css", "scss"]:
            if code.startswith(f"```{lang}") and code.endswith("```"):
                code = "\n".join(code.split("\n")[1:-1])
        
        # Write stylesheet file
        self.file_manager.write_file(project_name, f"frontend/{file_path}", code)
        
        return {
            "styling_approach": styling_approach,
            "created_files": [file_path]
        }
    
    async def _generate_service(
        self,
        project_name: str,
        task: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a frontend service for API communication"""
        
        description = task.get("description", "")
        
        # Determine service name from task description
        service_name = self._extract_service_name(description)
        
        # Get framework from architecture or use default
        frontend_framework = architecture.get("framework", "react")
        
        # Define file extension based on framework
        extension = ".js" if frontend_framework == "react" else ".ts" if frontend_framework == "angular" else ".js"
        file_path = f"src/services/{service_name}.service{extension}"
        
        prompt = f"""
        Act as an expert frontend developer.
        
        Create a service file for API communication based on the following details:
        
        Service Name: {service_name}
        Task Description: {description}
        Framework: {frontend_framework}
        
        File Path: {file_path}
        
        The service should:
        1. Handle API requests and responses
        2. Include error handling
        3. Use modern HTTP client (fetch, axios, etc.)
        4. Follow {frontend_framework} best practices
        5. Export functions for components to use
        
        Implement the service fully without placeholders.
        Only return the complete code for the file without any explanations.
        """
        
        response = await self.model.generate_content_async(prompt)
        code = response.text.strip()
        
        # Clean up code (remove markdown code blocks if present)
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.split("\n")[1:-1])
        
        # Further clean up if language is specified
        for lang in ["javascript", "typescript"]:
            if code.startswith(f"```{lang}") and code.endswith("```"):
                code = "\n".join(code.split("\n")[1:-1])
        
        # Write service file
        self.file_manager.write_file(project_name, f"frontend/{file_path}", code)
        
        return {
            "service_name": service_name,
            "created_files": [file_path]
        }
    
    async def _generate_generic_files(
        self,
        project_name: str,
        task: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate generic frontend files based on task description"""
        
        description = task.get("description", "")
        
        # Try to determine the most likely file type from description
        file_type = "utility" if "util" in description.lower() else "component" if "component" in description.lower() else "config" if "config" in description.lower() else "misc"
        
        # Get framework from architecture or use default
        frontend_framework = architecture.get("framework", "react")
        
        # Define file path based on file type
        extension = ".js" if frontend_framework == "react" else ".ts" if frontend_framework == "angular" else ".js"
        
        file_path = f"src/utils/helpers{extension}" if file_type == "utility" else f"src/config/app-config{extension}" if file_type == "config" else f"src/misc/index{extension}"
        
        # Custom file path if mentioned in description
        for line in description.split("\n"):
            if "file:" in line.lower() or "path:" in line.lower():
                potential_path = line.split(":", 1)[1].strip()
                if potential_path and not potential_path.startswith("/"):
                    file_path = potential_path
        
        prompt = f"""
        Act as an expert frontend developer using {frontend_framework}.
        
        Create a frontend file based on the following details:
        
        Task Description: {description}
        File Type: {file_type}
        Framework: {frontend_framework}
        
        File Path: {file_path}
        
        The file should:
        1. Be well-structured and maintainable
        2. Follow {frontend_framework} best practices
        3. Include appropriate comments and documentation
        4. Implement the functionality described in the task
        
        Implement the file fully without placeholders.
        Only return the complete code for the file without any explanations.
        """
        
        response = await self.model.generate_content_async(prompt)
        code = response.text.strip()
        
        # Clean up code (remove markdown code blocks if present)
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.split("\n")[1:-1])
        
        # Further clean up if language is specified
        for lang in ["javascript", "typescript", "jsx", "tsx"]:
            if code.startswith(f"```{lang}") and code.endswith("```"):
                code = "\n".join(code.split("\n")[1:-1])
        
        # Write file
        self.file_manager.write_file(project_name, f"frontend/{file_path}", code)
        
        return {
            "file_type": file_type,
            "created_files": [file_path]
        }
    
    async def _create_config_files(
        self,
        project_name: str,
        architecture: Dict[str, Any]
    ) -> None:
        """Create package.json and other configuration files"""
        
        # Get framework from architecture or use default
        frontend_framework = architecture.get("framework", "react")
        
        # Create package.json
        package_json_path = "package.json"
        
        prompt = f"""
        Act as an expert frontend developer.
        
        Create a package.json file for a {frontend_framework} project with:
        1. Appropriate dependencies for {frontend_framework}
        2. Common development dependencies (webpack, babel, etc.)
        3. NPM scripts for development, building, testing
        4. Project metadata (name, version, description)
        
        Only return the complete JSON for package.json without any explanations.
        """
        
        response = await self.model.generate_content_async(prompt)
        package_json = response.text.strip()
        
        # Clean up code (remove markdown code blocks if present)
        if package_json.startswith("```") and package_json.endswith("```"):
            package_json = "\n".join(package_json.split("\n")[1:-1])
        
        if package_json.startswith("```json") and package_json.endswith("```"):
            package_json = "\n".join(package_json.split("\n")[1:-1])
        
        # Update project name in package.json
        try:
            package_data = json.loads(package_json)
            package_data["name"] = project_name.lower().replace(" ", "-")
            package_json = json.dumps(package_data, indent=2)
        except:
            # If parsing fails, proceed with the original
            pass
        
        # Write package.json file
        self.file_manager.write_file(project_name, f"frontend/{package_json_path}", package_json)
        
        # Create framework-specific config files
        if frontend_framework == "react":
            # Create .babelrc
            babel_config = """{
  "presets": [
    "@babel/preset-env",
    "@babel/preset-react"
  ],
  "plugins": [
    "@babel/plugin-transform-runtime"
  ]
}"""
            self.file_manager.write_file(project_name, "frontend/.babelrc", babel_config)
            
        elif frontend_framework == "vue":
            # Create vue.config.js
            vue_config = """module.exports = {
  publicPath: '/',
  lintOnSave: false,
  productionSourceMap: false,
  css: {
    sourceMap: true
  }
}"""
            self.file_manager.write_file(project_name, "frontend/vue.config.js", vue_config)
            
        elif frontend_framework == "angular":
            # Create angular.json (simplified)
            angular_config = """{
  "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
  "version": 1,
  "newProjectRoot": "projects",
  "projects": {
    "app": {
      "projectType": "application",
      "schematics": {},
      "root": "",
      "sourceRoot": "src",
      "prefix": "app",
      "architect": {
        "build": {
          "builder": "@angular-devkit/build-angular:browser",
          "options": {
            "outputPath": "dist",
            "index": "src/index.html",
            "main": "src/main.ts",
            "polyfills": "src/polyfills.ts",
            "tsConfig": "tsconfig.app.json"
          }
        },
        "serve": {
          "builder": "@angular-devkit/build-angular:dev-server",
          "options": {
            "browserTarget": "app:build"
          }
        }
      }
    }
  },
  "defaultProject": "app"
}"""
            self.file_manager.write_file(project_name, "frontend/angular.json", angular_config)
        
        # Create index.html
        index_html_prompt = f"""
        Create a basic index.html file for a {frontend_framework} application.
        
        Only return the complete HTML without explanations.
        """
        
        response = await self.model.generate_content_async(index_html_prompt)
        index_html = response.text.strip()
        
        # Clean up code
        if index_html.startswith("```html") and index_html.endswith("```"):
            index_html = "\n".join(index_html.split("\n")[1:-1])
        elif index_html.startswith("```") and index_html.endswith("```"):
            index_html = "\n".join(index_html.split("\n")[1:-1])
        
        self.file_manager.write_file(project_name, "frontend/public/index.html", index_html)
    
    def _extract_component_name(self, description: str) -> str:
        """Extract component name from task description"""
        
        # Try to find component name in the description
        words = description.split()
        component_name = "DefaultComponent"
        
        for i, word in enumerate(words):
            if word.lower() in ["component", "widget", "element"]:
                if i > 0:
                    component_name = words[i-1]
                    # Capitalize first letter
                    component_name = component_name[0].upper() + component_name[1:]
                    # Remove any non-alphanumeric characters
                    component_name = ''.join(c for c in component_name if c.isalnum())
        
        return component_name
    
    def _extract_page_name(self, description: str) -> str:
        """Extract page name from task description"""
        
        # Try to find page name in the description
        words = description.split()
        page_name = "DefaultPage"
        
        for i, word in enumerate(words):
            if word.lower() in ["page", "screen", "view"]:
                if i > 0:
                    page_name = words[i-1]
                    # Capitalize first letter
                    page_name = page_name[0].upper() + page_name[1:]
                    # Remove any non-alphanumeric characters
                    page_name = ''.join(c for c in page_name if c.isalnum())
        
        return page_name
    
    def _extract_service_name(self, description: str) -> str:
        """Extract service name from task description"""
        
        # Try to find service name in the description
        words = description.split()
        service_name = "api"
        
        for i, word in enumerate(words):
            if word.lower() in ["service", "api", "client"]:
                if i > 0:
                    service_name = words[i-1].lower()
                    # Remove any non-alphanumeric characters
                    service_name = ''.join(c for c in service_name if c.isalnum() or c == '-')
        
        return service_name