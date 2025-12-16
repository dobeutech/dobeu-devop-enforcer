"""
Dobeu Undertaker - DevOps Standards Enforcement & Agent Orchestrator

A Claude Agent SDK-powered DevOps automation platform for Dobeu Tech Solutions LLC.
Enforces coding standards, compliance policies, and orchestrates specialized agents
across multi-repo environments with Azure platform integration.

Copyright (c) 2025 Dobeu Tech Solutions LLC
"""

from dobeu_undertaker.orchestrator import DobeuOrchestrator
from dobeu_undertaker.config.schema import UndertakerConfig

__version__ = "0.1.0"
__author__ = "Dobeu Tech Solutions LLC"
__email__ = "jeremyw@dobeu.net"

__all__ = [
    "DobeuOrchestrator",
    "UndertakerConfig",
    "__version__",
]
