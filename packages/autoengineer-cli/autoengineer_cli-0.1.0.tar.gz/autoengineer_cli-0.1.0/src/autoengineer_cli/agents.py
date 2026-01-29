"""
CrewAI Agent Definitions for AutoEngineer-CLI.
Defines specialized agents for autonomous software engineering tasks.
"""

import os
import litellm
from crewai import Agent, LLM
from .tools.podman_sandbox import PodmanSandboxTool
from .tools.file_writer import create_file_tools
from .config import Config


# Configure LiteLLM for OpenRouter
litellm.api_base = Config.OPENROUTER_BASE_URL
os.environ["OPENROUTER_API_KEY"] = Config.OPENROUTER_API_KEY


def create_llm(model: str) -> LLM:
    """Create a CrewAI LLM instance configured for OpenRouter."""
    return LLM(
        model=model,
        api_key=Config.OPENROUTER_API_KEY,
        base_url=Config.OPENROUTER_BASE_URL,
    )


# =============================================================================
# MANAGER AGENT
# =============================================================================
def create_manager_agent() -> Agent:
    """
    Creates the Manager Agent.
    
    Responsibilities:
    - Parses GitHub Issues and user requests
    - Manages overall workflow state
    - Coordinates between other agents
    - Ensures task completion
    """
    return Agent(
        role="Project Manager",
        goal=(
            "Parse and understand software development requests, break them down "
            "into actionable tasks, and coordinate the development workflow to "
            "ensure successful project completion."
        ),
        backstory=(
            "You are a seasoned project manager with 15 years of experience "
            "leading software development teams. You excel at understanding "
            "complex requirements, breaking them into manageable tasks, and "
            "ensuring smooth collaboration between architects, developers, and "
            "QA engineers. You have a keen eye for identifying potential blockers "
            "and proactively addressing them."
        ),
        llm=create_llm(Config.MANAGER_MODEL),
        verbose=Config.VERBOSE,
        allow_delegation=True,
        max_iter=Config.AGENT_MAX_ITER,
        max_rpm=Config.AGENT_MAX_RPM,
    )


# =============================================================================
# ARCHITECT AGENT
# =============================================================================
def create_architect_agent(repo_path: str = ".") -> Agent:
    """
    Creates the Architect Agent.
    
    Responsibilities:
    - Scans and understands the codebase structure
    - Analyzes dependencies and architecture
    - Creates detailed JSON execution plans
    - Identifies potential technical challenges
    """
    file_tools = create_file_tools(repo_path)
    
    return Agent(
        role="Software Architect",
        goal=(
            "Analyze codebases, understand their architecture and dependencies, "
            "and create comprehensive JSON execution plans that guide developers "
            "in implementing features or fixing bugs efficiently."
        ),
        backstory=(
            "You are a principal software architect with deep expertise in "
            "system design and code analysis. You've architected systems at "
            "scale and have an intuitive understanding of code structures, "
            "design patterns, and best practices. You can quickly scan a "
            "codebase and create actionable implementation plans that consider "
            "existing patterns, dependencies, and potential pitfalls."
        ),
        llm=create_llm(Config.ARCHITECT_MODEL),
        tools=file_tools,
        verbose=Config.VERBOSE,
        allow_delegation=False,
        max_iter=Config.AGENT_MAX_ITER,
        max_rpm=Config.AGENT_MAX_RPM,
    )


# =============================================================================
# CODER AGENT
# =============================================================================
def create_coder_agent(repo_path: str = ".") -> Agent:
    """
    Creates the Coder Agent.
    
    Responsibilities:
    - Implements code based on the architect's plan
    - Specializes in Python and C++ development
    - Writes clean, efficient, and well-documented code
    - Iterates based on QA feedback
    """
    file_tools = create_file_tools(repo_path)
    
    return Agent(
        role="Senior Software Developer",
        goal=(
            "Implement high-quality code based on architectural plans. "
            "Use the write_file tool to create actual files in the repository. "
            "Write clean, efficient, and well-documented code "
            "that follows best practices and passes all quality checks."
        ),
        backstory=(
            "You are a senior software developer with 10+ years of experience "
            "specializing in Python, JavaScript, and C++. You've contributed to major open-source "
            "projects and have a reputation for writing clean, maintainable code. "
            "You understand the importance of testing, documentation, and following "
            "established coding standards. When given a task, you implement it "
            "thoroughly by CREATING ACTUAL FILES using the write_file tool."
        ),
        llm=create_llm(Config.CODER_MODEL),
        tools=file_tools,
        verbose=Config.VERBOSE,
        allow_delegation=False,
        max_iter=Config.AGENT_MAX_ITER,
        max_rpm=Config.AGENT_MAX_RPM,
    )


# =============================================================================
# QA AGENT
# =============================================================================
def create_qa_agent(repo_path: str = ".") -> Agent:
    """
    Creates the QA Agent.
    
    Responsibilities:
    - Tests code in Podman sandbox containers
    - Compiles and runs code to verify functionality
    - Reports bugs and issues with detailed error logs
    - Validates that implementations meet requirements
    """
    sandbox_tool = PodmanSandboxTool()
    file_tools = create_file_tools(repo_path)
    
    return Agent(
        role="QA Engineer",
        goal=(
            "Thoroughly test code implementations by running them in isolated "
            "Podman containers. Compile, execute, and validate code to ensure "
            "it works correctly. Report any bugs or issues with detailed error "
            "logs and reproduction steps."
        ),
        backstory=(
            "You are a meticulous QA engineer with expertise in automated testing "
            "and containerized environments. You've caught countless bugs before "
            "they reached production and have a systematic approach to testing. "
            "You use Podman containers to safely execute and validate code, "
            "ensuring it works in clean, isolated environments."
        ),
        llm=create_llm(Config.QA_MODEL),
        tools=[sandbox_tool] + file_tools,
        verbose=Config.VERBOSE,
        allow_delegation=False,
        max_iter=Config.AGENT_MAX_ITER,
        max_rpm=Config.AGENT_MAX_RPM,
    )


# =============================================================================
# REVIEWER AGENT
# =============================================================================
def create_reviewer_agent(repo_path: str = ".") -> Agent:
    """
    Creates the Reviewer Agent.
    
    Responsibilities:
    - Performs final code review
    - Checks for code quality, security, and best practices
    - Generates comprehensive Markdown reports
    - Provides actionable improvement suggestions
    """
    file_tools = create_file_tools(repo_path)
    
    return Agent(
        role="Code Reviewer",
        goal=(
            "Perform thorough code reviews focusing on quality, security, and "
            "best practices. Generate comprehensive Markdown reports that "
            "summarize the implementation, highlight strengths, identify areas "
            "for improvement, and provide actionable recommendations."
        ),
        backstory=(
            "You are a senior code reviewer with expertise in code quality, "
            "security best practices, and software engineering principles. "
            "You've reviewed thousands of pull requests and have a keen eye "
            "for potential issues. Your reviews are constructive, detailed, "
            "and focus on helping developers improve their code while "
            "ensuring the codebase maintains high standards."
        ),
        llm=create_llm(Config.REVIEWER_MODEL),
        tools=file_tools,
        verbose=Config.VERBOSE,
        allow_delegation=False,
        max_iter=Config.AGENT_MAX_ITER,
        max_rpm=Config.AGENT_MAX_RPM,
    )


# =============================================================================
# AGENT FACTORY
# =============================================================================
def create_all_agents(repo_path: str = ".") -> dict[str, Agent]:
    """Create all agents for the AutoEngineer-CLI system."""
    return {
        "manager": create_manager_agent(),
        "architect": create_architect_agent(repo_path),
        "coder": create_coder_agent(repo_path),
        "qa": create_qa_agent(repo_path),
        "reviewer": create_reviewer_agent(repo_path),
    }
