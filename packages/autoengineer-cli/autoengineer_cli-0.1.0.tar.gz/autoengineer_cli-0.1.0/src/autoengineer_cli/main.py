"""
AutoEngineer-CLI: Autonomous Software Engineering Multi-Agent System.

Entry point for the CLI application that orchestrates AI agents
to analyze, implement, test, and review code changes.
"""

import os
import sys
import time
import click
from typing import Optional

from crewai import Crew, Task, Process

from .config import Config
from .agents import create_all_agents


def create_tasks(
    agents: dict,
    repo_path: str,
    problem_description: str,
) -> list[Task]:
    """Create the task pipeline for the agents."""
    
    # Task 1: Manager parses the request
    parse_task = Task(
        description=f"""
        Analyze the following software development request and create a structured breakdown:
        
        Repository Path: {repo_path}
        
        Problem Description:
        {problem_description}
        
        Provide:
        1. A clear summary of what needs to be done
        2. Key requirements and constraints
        3. Success criteria for the implementation
        4. Any potential risks or challenges
        """,
        expected_output=(
            "A structured analysis with summary, requirements, success criteria, "
            "and identified risks in JSON format."
        ),
        agent=agents["manager"],
    )
    
    # Task 2: Architect creates execution plan
    architect_task = Task(
        description=f"""
        Based on the manager's analysis, scan the codebase at '{repo_path}' and create 
        a detailed execution plan.
        
        FIRST: Use the list_directory tool to explore the current repository structure.
        
        Your plan should include:
        1. Current codebase structure analysis (if exists)
        2. Files that need to be created or modified
        3. Dependencies to be added
        4. Step-by-step implementation instructions
        5. Testing strategy
        
        Output the plan as a JSON object.
        """,
        expected_output=(
            "A detailed JSON execution plan with file changes, dependencies, "
            "implementation steps, and testing strategy."
        ),
        agent=agents["architect"],
        context=[parse_task],
    )
    
    # Task 3: Coder implements the solution
    coder_task = Task(
        description=f"""
        Implement the solution based on the architect's execution plan.
        
        CRITICAL INSTRUCTIONS:
        1. Use the write_file tool to CREATE ACTUAL FILES in the repository
        2. Write clean, well-documented code
        3. Follow best practices for the language
        4. Include necessary error handling
        5. Add inline comments for complex logic
        
        After creating each file, use list_directory to verify the files were created.
        
        At the end, provide a COMPLETE LIST of all files you created with their paths.
        """,
        expected_output=(
            "Complete code implementation with all files ACTUALLY CREATED using write_file tool. "
            "Include a final list of all files created with their full paths."
        ),
        agent=agents["coder"],
        context=[architect_task],
    )
    
    # Task 4: QA tests the implementation
    qa_task = Task(
        description=f"""
        Test the implemented code.
        
        FIRST: Use list_directory on '{repo_path}' to see ALL files that were just created.
        Then use read_file to examine the actual code files.
        
        Steps:
        1. List the repository to find all newly created files
        2. Read the main code files to understand the implementation
        3. Verify the code meets the requirements
        4. Report any bugs, errors, or issues found
        
        If Podman is available, use podman_sandbox to execute the code safely.
        """,
        expected_output=(
            "Test results including: list of files found, code analysis, "
            "any bugs found, and recommendations for fixes if needed."
        ),
        agent=agents["qa"],
        context=[coder_task],
    )
    
    # Task 5: Reviewer performs final review
    review_task = Task(
        description=f"""
        Perform a comprehensive code review of the NEWLY CREATED implementation.
        
        CRITICAL: You MUST review the files created for THIS task, not previous tasks!
        
        STEP 1: Use list_directory on '{repo_path}' to find ALL current files
        STEP 2: Use read_file to read EACH code file (especially .py files)
        STEP 3: Review the code based on the following criteria:
            1. Code quality and readability
            2. Best practices adherence
            3. Security considerations
            4. Performance implications
            5. Documentation completeness
        
        Your review MUST reference the actual files you read using read_file.
        Do NOT review based on previous context - READ the actual current files!
        
        Generate a detailed Markdown report with your findings.
        """,
        expected_output=(
            "A comprehensive Markdown report including: list of files reviewed, "
            "overall assessment, code quality score, security review, performance notes, "
            "and specific improvement recommendations for the CURRENT implementation."
        ),
        agent=agents["reviewer"],
        context=[coder_task, qa_task],
    )
    
    return [parse_task, architect_task, coder_task, qa_task, review_task]


def run_with_retry(
    crew: Crew,
    agents: dict,
    repo_path: str,
    problem_description: str,
    max_retries: int = None,
) -> str:
    """
    Run the crew with retry logic for connection failures.
    
    Only retries on actual API/connection errors, not on successful completions.
    """
    max_retries = max_retries or Config.MAX_QA_RETRIES
    last_error = None
    
    for attempt in range(max_retries):
        try:
            click.echo(f"\n{'='*60}")
            click.echo(f"Attempt {attempt + 1}/{max_retries}")
            click.echo(f"{'='*60}\n")
            
            result = crew.kickoff()
            
            # If we get here without exception, the execution succeeded
            result_str = str(result)
            return result_str
                
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Only retry on connection/API errors
            is_connection_error = any(x in error_str for x in [
                "connection", "timeout", "chunked read", "peer closed",
                "rate limit", "429", "503", "502", "500"
            ])
            
            if is_connection_error and attempt < max_retries - 1:
                click.echo(f"\n❌ Connection error: {e}")
                click.echo(f"Retrying in {Config.RETRY_DELAY} seconds...")
                time.sleep(Config.RETRY_DELAY)
            else:
                # Don't retry on non-connection errors or if we've exhausted retries
                raise
    
    # If we somehow exit the loop without returning, raise the last error
    if last_error:
        raise last_error
    return ""


@click.command()
@click.option(
    "--repo", "-r",
    required=True,
    type=click.Path(exists=True),
    help="Path to the repository to work on.",
)
@click.option(
    "--task", "-t",
    required=True,
    help="Description of the task or problem to solve.",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Path to save the final report (default: stdout).",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output.",
)
@click.option(
    "--max-retries",
    type=int,
    default=3,
    help="Maximum QA retry attempts (default: 3).",
)
@click.version_option(version="0.1.0", prog_name="autoengineer")
def main(
    repo: str,
    task: str,
    output: Optional[str],
    verbose: bool,
    max_retries: int,
):
    """
    AutoEngineer-CLI: Autonomous Software Engineering Multi-Agent System.
    
    Uses AI agents to analyze, implement, test, and review code changes.
    
    Example:
        autoengineer --repo ./my-project --task "Add a REST API endpoint for user authentication"
    """
    # Banner
    click.echo("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           AutoEngineer-CLI (OpenRouter Edition)           ║
    ║         Autonomous Software Engineering System            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        click.echo(f"❌ Configuration Error: {e}", err=True)
        sys.exit(1)
    
    # Set verbose mode
    if verbose:
        os.environ["AUTOENGINEER_VERBOSE"] = "true"
    
    # Get absolute repo path
    repo_path = os.path.abspath(repo)
    click.echo(f"📁 Repository: {repo_path}")
    click.echo(f"📋 Task: {task}")
    click.echo(f"🔄 Max Retries: {max_retries}")
    click.echo()
    
    # Create agents with repository path for file tools
    click.echo("🤖 Initializing agents...")
    agents = create_all_agents(repo_path)
    
    # Create tasks
    click.echo("📝 Creating task pipeline...")
    tasks = create_tasks(agents, repo_path, task)
    
    # Create crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
        memory=False,  # Disable memory to prevent context bloat
    )
    
    # Run with retry logic
    click.echo("\n🚀 Starting execution...\n")
    
    try:
        result = run_with_retry(
            crew=crew,
            agents=agents,
            repo_path=repo_path,
            problem_description=task,
            max_retries=max_retries,
        )
        
        # Output result
        click.echo("\n" + "="*60)
        click.echo("📊 FINAL REPORT")
        click.echo("="*60 + "\n")
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result)
            click.echo(f"✅ Report saved to: {output}")
        else:
            click.echo(result)
        
        click.echo("\n✅ AutoEngineer-CLI completed successfully!")
        
    except Exception as e:
        click.echo(f"\n❌ Execution failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
