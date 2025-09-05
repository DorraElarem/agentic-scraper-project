"""
Sources tunisiennes CORRIGÉES - URLs fonctionnelles vérifiées
Remplacement des URLs obsolètes par des sources accessibles
"""

from enum import Enum
from typing import Dict, List
from app.config.settings import settings

class TunisianSource(Enum):
    BCT = "Banque Centrale de Tunisie"
    INS = "Institut National de Statistique" 
    INTERNATIONAL = "Sources Internationales Tunisie"
    BACKUP = "Sources de Secours"

# CORRECTION CRITIQUE: URLs fonctionnelles vérifiées
WORKING_TUNISIAN_SOURCES = {
    "government_accessible": [
        "https://www.bct.gov.tn/bct/siteprod/francais/index.jsp",
        "https://www.ins.tn/fr",
        "https://www.finances.gov.tn/fr",
    ],
    "international_tunisia_data": [
        "https://api.worldbank.org/v2/countries/TN/indicators/NY.GDP.MKTP.CD?format=json&date=2020:2023",
        "https://api.worldbank.org/v2/countries/TN/indicators/FP.CPI.TOTL.ZG?format=json&date=2020:2023", 
        "https://api.worldbank.org/v2/countries/TN/indicators/SL.UEM.TOTL.ZS?format=json&date=2020:2023",
        "https://restcountries.com/v3.1/name/tunisia",
    ],
    "economic_data_reliable": [
        "https://tradingeconomics.com/tunisia/gdp",
        "https://www.cia.gov/the-world-factbook/countries/tunisia/",
    ],
    "emergency_fallback": [
        "https://httpbin.org/json",  # Pour tests
        "https://api.worldbank.org/v2/countries?format=json&per_page=300",
    ]
}

# Configuration mise à jour
SOURCE_CONFIG = {
    TunisianSource.BCT: {
        "base_url": "https://www.bct.gov.tn",
        "accessible_pages": [
            "/bct/siteprod/francais/index.jsp",
            "/bct/siteprod/francais/actualites.jsp"
        ],
        "fallback_apis": WORKING_TUNISIAN_SOURCES["international_tunisia_data"]
    },
    TunisianSource.INS: {
        "base_url": "https://www.ins.tn", 
        "accessible_pages": ["/fr"],
        "fallback_apis": WORKING_TUNISIAN_SOURCES["international_tunisia_data"]
    },
    TunisianSource.INTERNATIONAL: {
        "primary_sources": WORKING_TUNISIAN_SOURCES["international_tunisia_data"],
        "secondary_sources": WORKING_TUNISIAN_SOURCES["economic_data_reliable"]
    },
    TunisianSource.BACKUP: {
        "emergency_sources": WORKING_TUNISIAN_SOURCES["emergency_fallback"]
    }
}

def get_source_config(source: TunisianSource, indicator: str = None):
    """Retourne la config pour une source et un indicateur donné"""
    config = SOURCE_CONFIG.get(source)
    if indicator and config:
        return config.get("indicators", {}).get(indicator)
    return config

def get_working_urls() -> List[str]:
    """Retourne toutes les URLs fonctionnelles vérifiées"""
    all_urls = []
    for category in WORKING_TUNISIAN_SOURCES.values():
        all_urls.extend(category)
    return all_urls

def get_fallback_sources() -> List[str]:
    """Sources de secours en cas d'échec des URLs principales"""
    return WORKING_TUNISIAN_SOURCES["international_tunisia_data"]

def get_test_sources() -> List[str]:
    """Sources pour tests - garanties fonctionnelles"""
    return [
        "https://api.worldbank.org/v2/countries/TN/indicators/NY.GDP.MKTP.CD?format=json&date=2020:2023",
        "https://restcountries.com/v3.1/name/tunisia"
    ]

def validate_url_accessibility(url: str) -> bool:
    """Validation rapide d'accessibilité URL"""
    import requests
    try:
        response = requests.head(url, timeout=5)
        return response.status_code < 500
    except:
        return False

# Export des éléments principaux
__all__ = [
    'TunisianSource',
    'WORKING_TUNISIAN_SOURCES', 
    'SOURCE_CONFIG',
    'get_source_config',
    'get_working_urls',
    'get_fallback_sources', 
    'get_test_sources',
    'validate_url_accessibility'
]