"""
🤖 SCRAPERS - Exportations simplifiées et cohérentes
"""

from .traditional import TunisianWebScraper
from .intelligent import IntelligentScraper

# Factory function pour choix automatique
def get_optimal_scraper(url: str, enable_llm: bool = False):
    """Retourne le scraper optimal pour l'URL donnée"""
    if any(api_indicator in url for api_indicator in ['api.', 'json', 'data.']):
        return TunisianWebScraper()
    else:
        return IntelligentScraper()

__all__ = ['TunisianWebScraper', 'IntelligentScraper', 'get_optimal_scraper']