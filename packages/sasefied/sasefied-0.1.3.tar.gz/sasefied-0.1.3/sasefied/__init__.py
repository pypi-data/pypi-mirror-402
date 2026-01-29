"""
Sasefied Agent Library

A comprehensive, production-ready library for building intelligent AI agents 
with industry-specific capabilities.

Author: Library Maintainer
Email: maintainer@sasefied.com
GitHub: https://github.com/sasefied/sasefied-agent
"""

__version__ = "0.1.3"
__author__ = "Library Maintainer"
__email__ = "satyamsingh7734@gmail.com"
__description__ = "A comprehensive library for building intelligent AI agents with industry-specific capabilities"

# Core imports
from .agents.base import BaseAgent
from .agents.deep_search import DeepSearchAgent

# Industry modules
from . import industry
from . import hub
from . import tools
from . import agentic_systems

__all__ = [
    "BaseAgent",
    "DeepSearchAgent",
    "industry",
    "hub", 
    "tools",
    "agentic_systems",
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]