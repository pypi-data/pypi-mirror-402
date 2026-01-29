"""
AutoEngineer-CLI: Autonomous Software Engineering Multi-Agent System.

A CLI tool that uses 5 specialized AI agents to analyze, implement,
test, and review code from natural language descriptions.
"""

__version__ = "0.1.0"
__author__ = "AutoEngineer Team"

from .config import Config
from .agents import create_all_agents

__all__ = ["Config", "create_all_agents", "__version__"]
