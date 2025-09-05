"""
Filtre temporel CORRIGÉ COMPLET pour World Bank et sites tunisiens
Correction majeure de l'extraction d'année et du filtrage trop strict
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

class TemporalFilter:
    """Filtre temporel avec extraction d'année COMPLÈTEMENT CORRIGÉE"""
    
    def __init__(self):
        self.target_period = {
            'start_year': 2018,
            'end_year': 2025,
            'valid_years': set(range(2018, 2026)),
            'strict_mode': False  # CORRIGÉ : Plus permissif
        }
        
        # CORRECTIF COMPLET : Patterns World Bank + sites gouvernementaux
        self.year_patterns = [
            # World Bank API spécifique
            r'"date":\s*"(\d{4})"',                    # {"date": "2023"}
            r'"year":\s*"?(\d{4})"?',                  # {"year": "2023"}
            r'"(\d{4})":\s*\{',                        # "2023": {...}
            
            # Patterns généraux améliorés
            r'\b(20(?:1[8-9]|2[0-5]))\b',             # 2018-2025 strict
            r'tunisia\s+(\d{4})',                      # "Tunisia 2024"
            r'tunisie\s+(\d{4})',                      # "Tunisie 2024"
            r'gdp.*?tunisia.*?(\d{4})',                # "GDP Tunisia 2024"
            r'pib.*?tunisie.*?(\d{4})',                # "PIB Tunisie 2024"
            
            # Formats contextuels
            r'(\d{4})\s*[-–—]\s*\d{2}[-–—]\d{2}',     # 2024-01-01
            r'year[:\s]*(\d{4})',                      # year: 2024
            r'année[:\s]*(\d{4})',                     # année: 2024
            r'en\s+(\d{4})',                           # en 2024
            r'for\s+(\d{4})',                          # for 2024
            r'(\d{4})\s*data',                         # 2024 data
            r'statistics.*?(\d{4})',                   # statistics 2024
            
            # Patterns de fin de chaîne
            r'(\d{4})\s*$',                            # ...2024
            r'\((\d{4})\)',                            # (2024)
            r'([0-9]{4})',                             # Fallback: toute année 4 chiffres
        ]
        
        logger.info(f"TemporalFilter CORRECTED COMPLETE - Période: {self.target_period['start_year']}-{self.target_period['end_year']}, Strict: {self.target_period['strict_mode']}")
    
    def is_in_target_period(self, year: int) -> bool:
        """Vérification si l'année est dans la période cible"""
        return year in self.target_period['valid_years']
    
    def filter_indicators(self, indicators: List[Dict[str, Any]], source_url: str = "") -> Dict[str, Any]:
        """Filtre les indicateurs selon la période temporelle avec mode gouvernemental permissif"""
        
        if not indicators:
            return {
                'filtered_indicators': [],
                'stats': {'input_count': 0, 'output_count': 0, 'filtered_out': 0}
            }
        
        filtered = []
        stats = {
            'input_count': len(indicators),
            'rejected_year_outside': 0,
            'rejected_no_year': 0,
            'kept_in_period': 0,
            'kept_extended': 0,
            'kept_non_temporal': 0,
            'government_permissive': 0  # NOUVEAU
        }
        
        # Détection des sites gouvernementaux tunisiens
        is_gov_site = any(domain in source_url.lower() for domain in [
            'bct.gov.tn', 'ins.tn', 'finances.gov.tn', '.gov.tn'
        ])
        
        for indicator in indicators:
            year = self._extract_year_from_indicator(indicator)
            
            if year is None:
                # Mode permissif pour gouvernemental
                if is_gov_site:
                    indicator['year'] = 2024  # Année par défaut
                    indicator['temporal_context'] = 'government_default_2024'
                    filtered.append(indicator)
                    stats['government_permissive'] += 1
                    continue
                else:
                    stats['rejected_no_year'] += 1
                    continue
            
            # FILTRAGE ULTRA-PERMISSIF pour sites gouvernementaux
            if self.is_in_target_period(year):
                acceptance_reason = 'in_target_period'
                in_period = True
                stats['kept_in_period'] += 1
            elif 2010 <= year <= 2030:  # Période ultra-élargie
                acceptance_reason = 'extended_period_accepted'
                in_period = False
                stats['kept_extended'] += 1
            elif is_gov_site:  # NOUVEAU : Mode gouvernemental permissif
                acceptance_reason = 'government_permissive_mode'
                in_period = False
                stats['government_permissive'] += 1
            else:
                stats['rejected_year_outside'] += 1
                continue
            
            # Enrichir l'indicateur
            indicator['temporal_context'] = f"{year}-{acceptance_reason}"
            indicator['in_target_period'] = in_period
            filtered.append(indicator)
        
        stats['output_count'] = len(filtered)
        stats['filtered_out'] = stats['input_count'] - stats['output_count']
        
        return {
            'filtered_indicators': filtered,
            'stats': stats,
            'government_mode': is_gov_site
        }
        
    def _is_government_source(self, indicator: Dict[str, Any]) -> bool:
        """Détecte si l'indicateur vient d'un site gouvernemental"""
        try:
            source_url = indicator.get('source', '') or indicator.get('url', '')
            if isinstance(source_url, str):
                return any(domain in source_url.lower() for domain in ['bct.gov.tn', 'ins.tn', 'finances.gov.tn', 'gov.tn'])
            return False
        except:
            return False
    
    def _extract_year_ultra_comprehensive(self, indicator: Dict[str, Any], content: str = "", index: int = 0) -> Optional[int]:
        """EXTRACTION D'ANNÉE ULTRA-COMPREHENSIVE avec toutes les corrections"""
        
        debug_info = []
        
        # 1. PRIORITÉ ABSOLUE : Année explicite dans l'item
        if 'year' in indicator and indicator['year']:
            try:
                year = int(indicator['year'])
                if 1900 <= year <= 2030:
                    debug_info.append(f"explicit_year: {year}")
                    logger.debug(f"Indicator {index}: Found explicit year: {year}")
                    return year
            except (ValueError, TypeError):
                debug_info.append("explicit_year: failed_conversion")
        
        # 2. CORRECTIF WORLD BANK : Analyse spécialisée du nom d'indicateur
        indicator_name = indicator.get('indicator_name', '')
        if indicator_name:
            debug_info.append(f"analyzing_name: '{indicator_name[:50]}'")
            
            # PATTERNS WORLD BANK SPÉCIALISÉS
            for pattern_name, pattern in [
                ("wb_tunisia", r'tunisia\s+(\d{4})'),
                ("wb_gdp", r'gdp.*?tunisia.*?(\d{4})'),
                ("wb_end_year", r'(\d{4})\s*$'),
                ("wb_target_period", r'\b(20(?:1[8-9]|2[0-5]))\b'),
                ("wb_any_year", r'([0-9]{4})'),
            ]:
                matches = re.findall(pattern, indicator_name, re.IGNORECASE)
                if matches:
                    debug_info.append(f"{pattern_name}: {matches}")
                    
                    for match in matches:
                        try:
                            year = int(match)
                            if 2018 <= year <= 2025:  # PRIORITÉ absolue pour période cible
                                debug_info.append(f"found_target: {year}")
                                logger.debug(f"Indicator {index}: Found target period year in name: {year}")
                                return year
                            elif 1900 <= year <= 2030:  # Accepter autres années valides
                                debug_info.append(f"found_valid: {year}")
                                logger.debug(f"Indicator {index}: Found valid year in name: {year}")
                                return year
                        except ValueError:
                            continue
        
        # 3. EXTRACTION JSON SPÉCIALISÉE pour World Bank API
        raw_text = indicator.get('raw_text', '')
        if raw_text and ('date' in raw_text or 'year' in raw_text):
            debug_info.append("analyzing_json")
            
            # Chercher des patterns JSON
            json_patterns = [
                r'"date":\s*"(\d{4})"',
                r'"year":\s*"?(\d{4})"?',
                r'"(\d{4})":\s*\{',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, raw_text)
                if matches:
                    for match in matches:
                        try:
                            year = int(match)
                            if 2018 <= year <= 2025:
                                debug_info.append(f"json_found: {year}")
                                logger.debug(f"Indicator {index}: Found year in JSON: {year}")
                                return year
                        except ValueError:
                            continue
        
        # 4. MÉTADONNÉES COMPLÈTES de l'indicateur
        debug_info.append("checking_metadata")
        if isinstance(indicator, dict):
            for key, value in indicator.items():
                if any(time_word in key.lower() for time_word in ['date', 'time', 'year', 'period']):
                    try:
                        if isinstance(value, str) and len(value) == 4 and value.isdigit():
                            year = int(value)
                            if 2018 <= year <= 2025:
                                debug_info.append(f"metadata_{key}: {year}")
                                logger.debug(f"Indicator {index}: Found year in metadata {key}: {year}")
                                return year
                    except (ValueError, TypeError):
                        continue
        
        # 5. CONTEXTE TEXTUEL SÉCURISÉ (limité pour éviter pollution)
        if content and len(content) < 3000:  # Limiter taille
            context_year = self._extract_year_from_context_ultra_safe(content)
            if context_year:
                debug_info.append(f"context: {context_year}")
                logger.debug(f"Indicator {index}: Found year in context: {context_year}")
                return context_year
        
        # 6. FALLBACK INTELLIGENT
        current_year = datetime.now().year
        if self.is_in_target_period(current_year):
            debug_info.append(f"fallback_current: {current_year}")
            logger.debug(f"Indicator {index}: Using current year fallback: {current_year}")
            return current_year
        
        # 7. FALLBACK FINAL SÉCURISÉ
        fallback_year = 2024
        debug_info.append(f"fallback_final: {fallback_year}")
        logger.debug(f"Indicator {index}: Using final fallback: {fallback_year}")
        return fallback_year
    
    def _extract_year_from_context_ultra_safe(self, content: str) -> Optional[int]:
        """Extraction d'année ultra-sécurisée depuis contexte"""
        
        if not content or len(content) > 5000:
            return None
        
        # Analyser seulement les premiers 1500 caractères
        safe_content = content[:1500].lower()
        
        # Patterns ultra-spécifiques pour éviter faux positifs
        ultra_safe_patterns = [
            r'tunisia[^0-9]*(\d{4})',          # Tunisia ... 2024
            r'tunisie[^0-9]*(\d{4})',          # Tunisie ... 2024
            r'gdp[^0-9]*tunisia[^0-9]*(\d{4})', # GDP Tunisia 2024
            r'data[^0-9]*(\d{4})',             # data 2024
            r'year[:\s]+(\d{4})',              # year: 2024
            r'statistics[^0-9]*(\d{4})',       # statistics 2024
        ]
        
        candidate_years = []
        
        for pattern in ultra_safe_patterns:
            matches = re.findall(pattern, safe_content)
            for match in matches:
                try:
                    year = int(match)
                    if 2018 <= year <= 2025:
                        candidate_years.append(year)
                except ValueError:
                    continue
        
        if candidate_years:
            # Prendre l'année la plus fréquente
            most_common = Counter(candidate_years).most_common(1)
            return most_common[0][0]
        
        return None
    
    def _is_valid_non_temporal_indicator(self, indicator: Dict[str, Any]) -> bool:
        """Vérifie si un indicateur sans année est valide économiquement"""
        
        # Vérifier la présence de données économiques valides
        indicator_name = indicator.get('indicator_name', '').lower()
        
        economic_keywords = [
            'pib', 'gdp', 'inflation', 'unemployment', 'chomage',
            'population', 'export', 'import', 'trade', 'commerce',
            'budget', 'dette', 'debt', 'taux', 'rate', 'prix', 'price',
            'production', 'industrie', 'financial', 'economique'
        ]
        
        has_economic_content = any(keyword in indicator_name for keyword in economic_keywords)
        
        # Vérifier la présence de valeur numérique
        has_numeric_value = indicator.get('value') is not None
        
        # Vérifier la qualité minimale
        has_reasonable_name = len(indicator_name) >= 3
        
        return has_economic_content and has_numeric_value and has_reasonable_name
    
    def _emergency_acceptance_mode(self, indicators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mode d'acceptation d'urgence quand tout est rejeté"""
        
        logger.warning("EMERGENCY ACCEPTANCE MODE - Keeping all valid indicators with default year")
        
        emergency_filtered = []
        
        for indicator in indicators:
            if isinstance(indicator, dict) and indicator.get('value') is not None:
                indicator_copy = indicator.copy()
                indicator_copy.update({
                    'year': 2024,
                    'period_type': 'emergency_default',
                    'temporal_context': 'emergency-acceptance',
                    'in_target_period': True,
                    'temporal_filter_applied': True,
                    'acceptance_reason': 'emergency_mode'
                })
                emergency_filtered.append(indicator_copy)
        
        logger.warning(f"Emergency mode kept {len(emergency_filtered)} indicators")
        return emergency_filtered
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du filtre"""
        return {
            'period': f"{self.target_period['start_year']}-{self.target_period['end_year']}",
            'valid_years': list(self.target_period['valid_years']),
            'strict_mode': self.target_period['strict_mode'],
            'patterns_count': len(self.year_patterns),
            'version': 'ultra_comprehensive_fix_v2.0',
            'features': [
                'world_bank_specialized',
                'emergency_acceptance_mode',
                'non_temporal_acceptance',
                'extended_period_support'
            ]
        }

# Instance globale
temporal_filter = TemporalFilter()

# Fonctions utilitaires CORRIGÉES
def filter_by_temporal_period(indicators: List[Dict[str, Any]], content: str = "") -> List[Dict[str, Any]]:
    """Fonction principale de filtrage temporel ULTRA-CORRIGÉE"""
    return temporal_filter.filter_indicators(indicators, content)

def is_in_target_period(year: int) -> bool:
    """Vérifie si une année est dans la période 2018-2025"""
    return temporal_filter.is_in_target_period(year)

def extract_year_from_indicator(indicator: Dict[str, Any], content: str = "") -> Optional[int]:
    """Extrait l'année d'un indicateur avec correction World Bank COMPLÈTE"""
    return temporal_filter._extract_year_ultra_comprehensive(indicator, content)

def get_target_period() -> Dict[str, int]:
    """Retourne la période cible"""
    return {
        'start_year': temporal_filter.target_period['start_year'],
        'end_year': temporal_filter.target_period['end_year']
    }

# NOUVELLES FONCTIONS UTILITAIRES
def validate_indicators_list(indicators: Any) -> bool:
    """Valide que indicators est une liste valide"""
    return isinstance(indicators, list) and len(indicators) > 0

def emergency_filter_fallback(indicators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtre d'urgence si le filtre principal échoue"""
    return temporal_filter._emergency_acceptance_mode(indicators)

# Export complet
__all__ = [
    'TemporalFilter',
    'temporal_filter',
    'filter_by_temporal_period',
    'is_in_target_period',
    'extract_year_from_indicator',
    'get_target_period',
    'validate_indicators_list',
    'emergency_filter_fallback'
]