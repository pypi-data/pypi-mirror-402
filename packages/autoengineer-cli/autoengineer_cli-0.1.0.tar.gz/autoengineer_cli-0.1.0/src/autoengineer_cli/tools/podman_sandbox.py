"""
Podman Sandbox Tool for AutoEngineer-CLI.
Provides secure code execution in isolated containers.
"""

import os
import tempfile
import subprocess
from dataclasses import dataclass
from typing import Optional
from crewai.tools import BaseTool
from pydantic import Field

from ..config import Config


@dataclass
class ExecutionResult:
    """Result of a sandboxed code execution."""
    stdout: str
    stderr: str
    exit_code: int
    success: bool
    
    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        output = f"[{status}] Exit Code: {self.exit_code}\n"
        if self.stdout:
            output += f"\n=== STDOUT ===\n{self.stdout}"
        if self.stderr:
            output += f"\n=== STDERR ===\n{self.stderr}"
        return output


class PodmanSandbox:
    """
    Manages Podman containers for secure code execution.
    
    Supports Python and C++ code execution in isolated environments.
    """
    
    def __init__(
        self,
        python_image: str = None,
        cpp_image: str = None,
        timeout: int = None,
        memory_limit: str = None,
    ):
        self.python_image = python_image or Config.PYTHON_CONTAINER_IMAGE
        self.cpp_image = cpp_image or Config.CPP_CONTAINER_IMAGE
        self.timeout = timeout or Config.CONTAINER_TIMEOUT
        self.memory_limit = memory_limit or Config.CONTAINER_MEMORY_LIMIT
        
    def _run_podman_command(
        self,
        image: str,
        command: str,
        workdir: str = "/workspace",
        mount_path: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a command inside a Podman container."""
        
        podman_cmd = [
            "podman", "run",
            "--rm",  # Remove container after execution
            "--network=none",  # No network access for security
            f"--memory={self.memory_limit}",
            f"--timeout={self.timeout}",
            "-w", workdir,
        ]
        
        # Mount local directory if provided
        if mount_path and os.path.exists(mount_path):
            podman_cmd.extend(["-v", f"{mount_path}:{workdir}:Z"])
        
        podman_cmd.extend([image, "sh", "-c", command])
        
        try:
            result = subprocess.run(
                podman_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 10,  # Extra buffer for container startup
            )
            
            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                success=result.returncode == 0,
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr=f"Execution timed out after {self.timeout} seconds",
                exit_code=-1,
                success=False,
            )
        except FileNotFoundError:
            return ExecutionResult(
                stdout="",
                stderr="Podman is not installed or not in PATH. Please install Podman first.",
                exit_code=-1,
                success=False,
            )
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=-1,
                success=False,
            )
    
    def run_python(
        self,
        code: str,
        requirements: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Execute Python code in a sandboxed container.
        
        Args:
            code: Python code to execute
            requirements: Optional list of pip packages to install
            
        Returns:
            ExecutionResult with stdout, stderr, and exit code
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write the Python code to a file
            code_path = os.path.join(tmpdir, "main.py")
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Build the command
            commands = []
            
            # Install requirements if provided
            if requirements:
                req_str = " ".join(requirements)
                commands.append(f"pip install --quiet {req_str}")
            
            commands.append("python main.py")
            full_command = " && ".join(commands)
            
            return self._run_podman_command(
                image=self.python_image,
                command=full_command,
                mount_path=tmpdir,
            )
    
    def run_cpp(
        self,
        code: str,
        compiler_flags: str = "-std=c++17 -O2",
    ) -> ExecutionResult:
        """
        Compile and execute C++ code in a sandboxed container.
        
        Args:
            code: C++ source code
            compiler_flags: Flags to pass to g++
            
        Returns:
            ExecutionResult with stdout, stderr, and exit code
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write the C++ code to a file
            code_path = os.path.join(tmpdir, "main.cpp")
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Compile and run
            command = f"g++ {compiler_flags} -o main main.cpp && ./main"
            
            return self._run_podman_command(
                image=self.cpp_image,
                command=command,
                mount_path=tmpdir,
            )
    
    def run_command(
        self,
        command: str,
        language: str = "python",
        mount_path: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute an arbitrary command in a container.
        
        Args:
            command: Shell command to execute
            language: "python" or "cpp" to select container image
            mount_path: Optional path to mount into container
            
        Returns:
            ExecutionResult with stdout, stderr, and exit code
        """
        image = self.python_image if language == "python" else self.cpp_image
        
        return self._run_podman_command(
            image=image,
            command=command,
            mount_path=mount_path,
        )


class PodmanSandboxTool(BaseTool):
    """CrewAI Tool wrapper for Podman sandbox execution."""
    
    name: str = "podman_sandbox"
    description: str = (
        "Execute code safely in an isolated Podman container. "
        "Supports Python and C++ code execution. "
        "Input should be a JSON object with 'code', 'language' (python/cpp), "
        "and optionally 'requirements' (list of pip packages for Python)."
    )
    
    sandbox: PodmanSandbox = Field(default_factory=PodmanSandbox)
    
    def _run(self, code: str, language: str = "python", requirements: list = None) -> str:
        """Execute code in the sandbox."""
        if language == "python":
            result = self.sandbox.run_python(code, requirements)
        elif language == "cpp":
            result = self.sandbox.run_cpp(code)
        else:
            return f"Unsupported language: {language}. Use 'python' or 'cpp'."
        
        return str(result)


# Convenience function for direct usage
def run_in_sandbox(
    code: str,
    language: str = "python",
    requirements: Optional[list[str]] = None,
) -> ExecutionResult:
    """
    Convenience function to run code in a Podman sandbox.
    
    Args:
        code: Code to execute
        language: "python" or "cpp"
        requirements: Optional pip packages (Python only)
        
    Returns:
        ExecutionResult with execution details
    """
    sandbox = PodmanSandbox()
    
    if language == "python":
        return sandbox.run_python(code, requirements)
    elif language == "cpp":
        return sandbox.run_cpp(code)
    else:
        raise ValueError(f"Unsupported language: {language}")
