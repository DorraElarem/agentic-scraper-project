"""
🤖 AGENTS - Package d'agents intelligents
Exportations simplifiées pour une architecture claire
"""

from .scraper_agent import ScraperAgent
from .analyzer_agent import AnalyzerAgent
from .navigation_agent import NavigationAgent
from .smart_coordinator import SmartScrapingCoordinator
from .orchestrator import SmartMultiAgentOrchestrator as MultiAgentOrchestrator

# ❌ SUPPRIMER l'ancien coordinator.py qui duplique smart_coordinator.py

__all__ = [
    'ScraperAgent',
    'AnalyzerAgent', 
    'NavigationAgent',
    'SmartScrapingCoordinator',
    'SmartMultiAgentOrchestrator'
]