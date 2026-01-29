"""
File Writer Tool for AutoEngineer-CLI.
Allows the Coder agent to create and modify files in the repository.
"""

import os
from pathlib import Path
from typing import Optional
from crewai.tools import BaseTool
from pydantic import Field


class FileWriterTool(BaseTool):
    """CrewAI Tool for writing files to the repository."""
    
    name: str = "write_file"
    description: str = (
        "Create or overwrite a file in the repository. "
        "Use this to write source code, configuration files, or documentation. "
        "Input: file_path (relative to repo root), content (the file contents). "
        "Returns confirmation of file creation."
    )
    
    repo_path: str = Field(default=".", description="Base repository path")
    
    def _run(self, file_path: str, content: str) -> str:
        """Write content to a file."""
        try:
            # Construct full path
            full_path = Path(self.repo_path) / file_path
            
            # Security check: ensure we're writing within repo
            full_path = full_path.resolve()
            repo_resolved = Path(self.repo_path).resolve()
            
            if not str(full_path).startswith(str(repo_resolved)):
                return f"❌ Error: Cannot write outside repository: {file_path}"
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"✅ Successfully created: {file_path} ({len(content)} bytes)"
            
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"


class FileReaderTool(BaseTool):
    """CrewAI Tool for reading files from the repository."""
    
    name: str = "read_file"
    description: str = (
        "Read the contents of a file from the repository. "
        "Use this to examine existing code before making modifications. "
        "Input: file_path (relative to repo root). "
        "Returns the file contents or an error message."
    )
    
    repo_path: str = Field(default=".", description="Base repository path")
    
    def _run(self, file_path: str) -> str:
        """Read content from a file."""
        try:
            full_path = Path(self.repo_path) / file_path
            
            if not full_path.exists():
                return f"❌ File not found: {file_path}"
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"📄 Contents of {file_path}:\n\n{content}"
            
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"


class DirectoryListerTool(BaseTool):
    """CrewAI Tool for listing directory contents."""
    
    name: str = "list_directory"
    description: str = (
        "List files and folders in a directory. "
        "Use this to explore the repository structure. "
        "Input: dir_path (relative to repo root, use '.' for root). "
        "Returns a list of files and directories."
    )
    
    repo_path: str = Field(default=".", description="Base repository path")
    
    def _run(self, dir_path: str = ".") -> str:
        """List contents of a directory."""
        try:
            full_path = Path(self.repo_path) / dir_path
            
            if not full_path.exists():
                return f"❌ Directory not found: {dir_path}"
            
            if not full_path.is_dir():
                return f"❌ Not a directory: {dir_path}"
            
            items = []
            for item in sorted(full_path.iterdir()):
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"📄 {item.name} ({size} bytes)")
            
            if not items:
                return f"📂 {dir_path}/ is empty"
            
            return f"📂 Contents of {dir_path}/:\n" + "\n".join(items)
            
        except Exception as e:
            return f"❌ Error listing directory: {str(e)}"


def create_file_tools(repo_path: str) -> list:
    """Create all file manipulation tools for a given repository."""
    return [
        FileWriterTool(repo_path=repo_path),
        FileReaderTool(repo_path=repo_path),
        DirectoryListerTool(repo_path=repo_path),
    ]
