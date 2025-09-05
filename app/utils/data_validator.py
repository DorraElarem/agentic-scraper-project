"""
Validateur STRICT pour les données économiques - VERSION CORRIGÉE 2018-2025
Validation intelligente mais stricte avec filtrage temporel 2018-2025
"""

import re
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from collections import Counter
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class EconomicIndicator(BaseModel):
    """Modèle strict pour les indicateurs économiques"""
    year: int = Field(..., description="Année de l'indicateur")
    value: Union[float, int] = Field(..., description="Valeur numérique")
    unit: str = Field("", description="Unité de mesure")
    indicator_name: str = Field(..., description="Nom de l'indicateur")
    source: str = Field("", description="Source des données")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    
    @field_validator('year')
    @classmethod
    def validate_year_strict(cls, v):
        """Validation stricte de l'année - PÉRIODE 2018-2025"""
        if not isinstance(v, int):
            raise ValueError(f"L'année doit être un entier, reçu: {type(v)}")
        if not (2018 <= v <= 2025):
            raise ValueError(f"L'année {v} n'est pas dans la période 2018-2025")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value_strict(cls, v):
        """Validation stricte de la valeur"""
        if not isinstance(v, (int, float)):
            try:
                v = float(v)
            except (ValueError, TypeError):
                raise ValueError(f"Valeur non numérique: {v}")
        
        # Rejeter les valeurs suspectes (années déguisées)
        if 1900 <= v <= 2030 and len(str(int(v))) == 4:
            raise ValueError(f"Valeur suspecte (année déguisée): {v}")
        
        # Plausibilité économique
        if abs(v) > 1e12:  # 1 trillion
            raise ValueError(f"Valeur économique implausible: {v}")
        
        return float(v)

class StrictDataValidator:
    """Validateur strict pour données économiques tunisiennes avec filtrage 2018-2025"""
    
    def __init__(self):
        # PÉRIODE CIBLE STRICTE
        self.target_period = {
            'start_year': 2018,
            'end_year': 2025,
            'valid_years': list(range(2018, 2026))  # 2018-2025 inclus
        }
        
        # Règles strictes par type d'indicateur
        self.validation_rules = {
            'taux': {'min': -50, 'max': 100, 'unit_patterns': ['%', 'pourcent']},
            'inflation': {'min': -20, 'max': 50, 'unit_patterns': ['%']},
            'chomage': {'min': 0, 'max': 50, 'unit_patterns': ['%']},
            'pib': {'min': 0, 'max': 200000, 'unit_patterns': ['md', 'milliards', 'millions']},
            'population': {'min': 1000000, 'max': 20000000, 'unit_patterns': ['habitants', 'millions']},
            'commerce': {'min': 0, 'max': 100000, 'unit_patterns': ['md', 'millions', 'usd', 'eur']}
        }
        
        # Patterns à rejeter catégoriquement
        self.reject_patterns = [
            r'^(19|20)\d{2}$',  # Années seules
            r'^(tableau|table|total|somme|sum)$',  # En-têtes
            r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # Mois
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',  # Dates
            r'^(source|note|reference|ref)[:.]',  # Métadonnées
            r'^(en|in|de|du|des|le|la|les|et|and|or|ou)\s',  # Mots de liaison
            r'classe|category|type|kind|sort',  # Catégories
            r'html|css|javascript|script|div|span|class',  # Code HTML/CSS
            r'^[<>].*[<>]$',  # Balises HTML
        ]
        
        # Mots-clés économiques ENRICHIS
        self.valid_economic_terms = [
            # Termes tunisiens
            'pib', 'gdp', 'inflation', 'taux', 'chomage', 'emploi',
            'population', 'demographie', 'export', 'import', 'commerce',
            'industrie', 'production', 'investissement', 'dette', 'deficit',
            'budget', 'recettes', 'depenses', 'croissance', 'development',
            
            # Termes World Bank et internationaux
            'gross domestic product', 'unemployment', 'trade', 'economy',
            'economic', 'financial', 'monetary', 'fiscal', 'statistics',
            'indicator', 'index', 'rate', 'percentage', 'billion', 'million',
            'annual', 'quarterly', 'growth', 'development', 'social',
            'demographic', 'tunisia', 'tunisian', 'tn', 'country', 'national',
            'current', 'constant', 'real', 'nominal'
        ]
        
        logger.info(f"StrictDataValidator initialized - Période cible: {self.target_period['start_year']}-{self.target_period['end_year']}")
    
    def validate_indicators(self, data: List[Dict[str, Any]], 
                          content: str = "") -> Dict[str, Any]:
        """Validation avec filtrage STRICT 2018-2025"""
        
        if not data:
            return self._empty_validation_result()
        
        # VALIDATION STRICTE avec filtrage temporel
        valid_data = []
        rejected_stats = {
            'outside_period': 0,
            'no_year': 0,
            'validation_error': 0,
            'rejected_patterns': 0
        }
        
        for i, item in enumerate(data):
            try:
                # PRÉ-VALIDATION : Rejeter les patterns évidents
                if self._should_reject_item(item):
                    rejected_stats['rejected_patterns'] += 1
                    continue
                
                # EXTRACTION ET VALIDATION DE L'ANNÉE
                year = self._extract_comprehensive_year(item, content)
                
                if year is None:
                    rejected_stats['no_year'] += 1
                    logger.debug(f"Rejected (no year): {item.get('indicator_name', f'item_{i}')}")
                    continue
                
                # FILTRAGE STRICT : Rejeter si hors période 2018-2025
                if not self._is_year_in_target_period(year):
                    rejected_stats['outside_period'] += 1
                    logger.debug(f"Rejected (year {year} outside 2018-2025): {item.get('indicator_name', f'item_{i}')}")
                    continue
                
                # Enrichissement et validation Pydantic
                enriched_item = self._enrich_and_normalize(item, i, content, year)
                validated_item = EconomicIndicator(**enriched_item)
                valid_data.append(validated_item.model_dump())
                
                logger.debug(f"ACCEPTED (year {year}): {enriched_item.get('indicator_name')}")
                
            except Exception as e:
                rejected_stats['validation_error'] += 1
                logger.debug(f"Validation error for item {i}: {e}")
                continue
        
        # RÉSULTAT avec statistiques détaillées
        total_rejected = sum(rejected_stats.values())
        result = {
            "valid": len(valid_data) > 0,
            "valid_data": valid_data,
            "errors": [],
            "warnings": self._generate_warnings(rejected_stats, len(data)),
            "summary": {
                "total_input": len(data),
                "valid_output": len(valid_data),
                "rejected_total": total_rejected,
                "rejected_outside_period": rejected_stats['outside_period'],
                "rejected_no_year": rejected_stats['no_year'],
                "rejected_patterns": rejected_stats['rejected_patterns'],
                "rejected_validation_errors": rejected_stats['validation_error'],
                "success_rate": (len(valid_data) / len(data) * 100) if data else 0,
                "validation_mode": "strict_temporal_2018_2025",
                "target_period": f"{self.target_period['start_year']}-{self.target_period['end_year']}"
            }
        }
        
        logger.info(f"STRICT validation 2018-2025: {len(data)} -> {len(valid_data)} (rejected: {total_rejected})")
        logger.info(f"Rejection breakdown: {rejected_stats}")
        
        return result
    
    def _extract_comprehensive_year(self, item: Dict[str, Any], content: str) -> Optional[int]:
        """Extraction COMPREHENSIVE d'année avec tous les patterns"""
        
        # 1. Année explicite dans l'item (priorité absolue)
        if 'year' in item and item['year']:
            try:
                year = int(item['year'])
                if 1900 <= year <= 2030:  # Validation de base
                    return year
            except (ValueError, TypeError):
                pass
        
        # 2. Extraction depuis le nom de l'indicateur
        indicator_name = item.get('indicator_name', '')
        if indicator_name:
            year = self._extract_year_from_name(indicator_name)
            if year:
                return year
        
        # 3. Extraction depuis le texte brut de l'item
        raw_text = item.get('raw_text', '') or item.get('context_text', '')
        if raw_text:
            year = self._extract_year_from_text(raw_text)
            if year:
                return year
        
        # 4. Extraction depuis le contenu global (limitée et prudente)
        if content:
            year = self._extract_year_from_context(content)
            if year:
                return year
        
        # 5. Dernière tentative : année courante si dans la période
        current_year = datetime.now().year
        if self._is_year_in_target_period(current_year):
            logger.debug(f"Using current year {current_year} as last resort")
            return current_year
        
        return None
    
    def _extract_year_from_name(self, name: str) -> Optional[int]:
        """Extraction d'année depuis le nom avec patterns étendus"""
        
        if not name:
            return None
        
        # Patterns spécialisés pour noms d'indicateurs
        year_patterns = [
            r'\b(20(?:1[8-9]|2[0-5]))\b',  # 2018-2025 strict
            r'tunisia\s+(\d{4})',  # "Tunisia 2024"
            r'gdp.*?(\d{4})',  # "GDP 2023"
            r'(\d{4})\s*$',  # Année en fin
            r'(\d{4})\s*[)\]\}]',  # Année avant parenthèse/bracket
            r'current.*?(\d{4})',  # "current 2024"
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, name.lower())
            if matches:
                try:
                    # Prendre toutes les années trouvées et choisir celle dans la période cible
                    for match in matches:
                        year = int(match)
                        if self._is_year_in_target_period(year):
                            logger.debug(f"Valid year from name '{name}': {year}")
                            return year
                    
                    # Si aucune année dans la période cible, prendre la plus récente
                    years = [int(m) for m in matches if 1900 <= int(m) <= 2030]
                    if years:
                        return max(years)
                        
                except ValueError:
                    continue
        
        return None
    
    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Extraction d'année depuis le texte brut"""
        
        if not text or len(text) > 1000:  # Limiter les textes trop longs
            return None
        
        # Patterns contextuels
        contextual_patterns = [
            r'year[:\s]+(\d{4})',
            r'année[:\s]+(\d{4})',
            r'en\s+(\d{4})',
            r'for\s+(\d{4})',
            r'(\d{4})\s+data',
            r'statistics.*?(\d{4})'
        ]
        
        for pattern in contextual_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                for match in matches:
                    try:
                        year = int(match)
                        if self._is_year_in_target_period(year):
                            return year
                    except ValueError:
                        continue
        
        # Pattern général pour années 2018-2025
        general_years = re.findall(r'\b(20(?:1[8-9]|2[0-5]))\b', text)
        if general_years:
            # Prendre l'année la plus fréquente dans la période cible
            year_counts = Counter(int(y) for y in general_years if self._is_year_in_target_period(int(y)))
            if year_counts:
                most_common_year = year_counts.most_common(1)[0][0]
                return most_common_year
        
        return None
    
    def _extract_year_from_context(self, content: str) -> Optional[int]:
        """Extraction d'année depuis le contexte global (très limitée)"""
        
        if not content or len(content) > 5000:  # Très limité pour éviter la pollution
            return None
        
        # Chercher des patterns très spécifiques dans les premiers caractères
        header_content = content[:2000]
        
        # Patterns pour en-têtes et titres
        header_patterns = [
            r'tunisia.*?(\d{4})',
            r'gdp.*?(\d{4})',
            r'economic.*?(\d{4})',
            r'statistics.*?(\d{4})',
            r'report.*?(\d{4})',
            r'data.*?(\d{4})'
        ]
        
        for pattern in header_patterns:
            matches = re.findall(pattern, header_content.lower())
            if matches:
                for match in matches:
                    try:
                        year = int(match)
                        if self._is_year_in_target_period(year):
                            return year
                    except ValueError:
                        continue
        
        return None
    
    def _is_year_in_target_period(self, year: int) -> bool:
        """Vérification si l'année est dans la période cible 2018-2025"""
        return year in self.target_period['valid_years']
    
    def _should_reject_item(self, item: Dict[str, Any]) -> bool:
        """Pré-validation pour rejeter les éléments évidents"""
        
        # Vérifier le nom de l'indicateur
        indicator_name = str(item.get('indicator_name', '')).lower().strip()
        
        if not indicator_name or len(indicator_name) < 3:
            return True
        
        # Appliquer les patterns de rejet
        for pattern in self.reject_patterns:
            if re.match(pattern, indicator_name, re.IGNORECASE):
                logger.debug(f"REJECTED by pattern: {indicator_name}")
                return True
        
        # Validation permissive pour données internationales
        has_economic_term = any(term in indicator_name for term in self.valid_economic_terms)
        
        # Si aucun terme économique direct, vérifier contexte numérique
        if not has_economic_term:
            # Vérifier si contient des mots-clés contextuels
            contextual_terms = ['data', 'value', 'measure', 'metric', 'figure', 'amount']
            has_contextual = any(term in indicator_name for term in contextual_terms)
            
            # Rejeter seulement si VRAIMENT non-économique
            if (len(indicator_name) > 150 or  # Très long
                indicator_name.count(' ') > 15 or  # Trop de mots
                not has_contextual):  # Et pas de contexte
                return True
        
        # Vérifier la valeur
        value = item.get('value')
        if value is not None:
            try:
                numeric_value = float(value)
                # Rejeter les années déguisées en valeurs
                if 1900 <= numeric_value <= 2030 and len(str(int(numeric_value))) == 4:
                    logger.debug(f"REJECTED year disguised as value: {numeric_value}")
                    return True
            except (ValueError, TypeError):
                return True
        
        return False
    
    def _enrich_and_normalize(self, item: Dict[str, Any], index: int, content: str, year: int) -> Dict[str, Any]:
        """Enrichissement et normalisation stricte avec année validée"""
        
        enriched = {}
        
        # Année - utiliser l'année validée
        enriched['year'] = year
        
        # Valeur - nettoyage strict
        value = item.get('value', 0)
        if isinstance(value, str):
            value = self._clean_numeric_value(value)
        enriched['value'] = value
        
        # Nom de l'indicateur - nettoyage
        indicator_name = str(item.get('indicator_name', f'Indicator_{index}')).strip()
        indicator_name = self._clean_indicator_name(indicator_name)
        enriched['indicator_name'] = indicator_name
        
        # Unité - standardisation
        unit = str(item.get('unit', '')).strip()
        enriched['unit'] = self._standardize_unit(unit, indicator_name, value)
        
        # Source
        enriched['source'] = str(item.get('source', 'Unknown')).strip()
        
        # Score de confiance basé sur la qualité des données
        enriched['confidence_score'] = self._calculate_confidence(enriched, item)
        
        return enriched
    
    def _clean_numeric_value(self, value_str: str) -> float:
        """Nettoyage strict des valeurs numériques"""
        try:
            # Nettoyer les séparateurs
            cleaned = re.sub(r'[^\d\.,\-]', '', value_str.strip())
            
            # Format européen (virgule décimale)
            if ',' in cleaned and '.' not in cleaned:
                cleaned = cleaned.replace(',', '.')
            elif ',' in cleaned and '.' in cleaned:
                # Garder le dernier comme décimal
                if cleaned.rfind(',') > cleaned.rfind('.'):
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def _clean_indicator_name(self, name: str) -> str:
        """Nettoyage du nom de l'indicateur"""
        if not name:
            return "Unknown Indicator"
        
        # Supprimer les balises HTML
        name = re.sub(r'<[^>]+>', '', name)
        
        # Supprimer les caractères de contrôle
        name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
        
        # Normaliser les espaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Limiter la longueur
        if len(name) > 100:
            name = name[:97] + "..."
        
        return name
    
    def _standardize_unit(self, unit: str, indicator_name: str, value: Union[float, int]) -> str:
        """Standardisation des unités"""
        if not unit:
            # Inférer l'unité selon le contexte
            name_lower = indicator_name.lower()
            
            if any(term in name_lower for term in ['taux', 'inflation', 'chomage', '%']):
                return '%'
            elif any(term in name_lower for term in ['pib', 'dette', 'budget']):
                return 'MD' if value > 1000 else 'MDT'
            elif 'population' in name_lower:
                return 'habitants'
            else:
                return ''
        
        # Standardiser les unités connues
        unit_mapping = {
            'pourcent': '%',
            'pourcentage': '%',
            'millions de dinars': 'MD',
            'milliards': 'MD',
            'dollar': 'USD',
            'euro': 'EUR'
        }
        
        unit_lower = unit.lower()
        for pattern, standard in unit_mapping.items():
            if pattern in unit_lower:
                return standard
        
        return unit[:10]  # Limiter la longueur
    
    def _calculate_confidence(self, enriched_data: Dict[str, Any], original_data: Dict[str, Any]) -> float:
        """Calcul du score de confiance"""
        confidence = 0.5  # Base
        
        # Bonus pour année dans la période cible
        if self._is_year_in_target_period(enriched_data['year']):
            confidence += 0.3  # Bonus important pour la période cible
        
        # Bonus pour indicateur économique reconnu
        name_lower = enriched_data['indicator_name'].lower()
        if any(term in name_lower for term in self.valid_economic_terms):
            confidence += 0.2
        
        # Bonus pour unité standardisée
        if enriched_data['unit']:
            confidence += 0.1
        
        # Bonus pour valeur plausible
        value = enriched_data['value']
        if isinstance(value, (int, float)) and abs(value) < 1e10:
            confidence += 0.1
        
        # Malus pour données suspectes
        if 'raw_text' in original_data and len(original_data['raw_text']) < 10:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_warnings(self, rejected_stats: Dict[str, int], total_input: int) -> List[str]:
        """Génération des warnings informatifs"""
        warnings = []
        
        if rejected_stats['outside_period'] > 0:
            warnings.append(f"{rejected_stats['outside_period']} éléments rejetés (hors période 2018-2025)")
        
        if rejected_stats['no_year'] > 0:
            warnings.append(f"{rejected_stats['no_year']} éléments rejetés (année non trouvée)")
        
        if rejected_stats['rejected_patterns'] > 0:
            warnings.append(f"{rejected_stats['rejected_patterns']} éléments rejetés (patterns non-économiques)")
        
        if rejected_stats['validation_error'] > 0:
            warnings.append(f"{rejected_stats['validation_error']} erreurs de validation")
        
        total_rejected = sum(rejected_stats.values())
        rejection_rate = (total_rejected / total_input * 100) if total_input > 0 else 0
        
        if rejection_rate > 80:
            warnings.append(f"Taux de rejet élevé ({rejection_rate:.1f}%) - vérifier la qualité des données source")
        
        return warnings
    
    def _empty_validation_result(self) -> Dict[str, Any]:
        """Résultat de validation vide"""
        return {
            "valid": False,
            "valid_data": [],
            "errors": ["Aucune donnée à valider"],
            "warnings": [],
            "summary": {
                "total_input": 0,
                "valid_output": 0,
                "rejected_total": 0,
                "rejected_outside_period": 0,
                "rejected_no_year": 0,
                "rejected_patterns": 0,
                "rejected_validation_errors": 0,
                "success_rate": 0,
                "validation_mode": "strict_temporal_2018_2025",
                "target_period": f"{self.target_period['start_year']}-{self.target_period['end_year']}"
            }
        }

# Instance globale
strict_validator = StrictDataValidator()

# Fonctions utilitaires
def validate_indicators_strict(data: List[Dict[str, Any]], content: str = "") -> Dict[str, Any]:
    """Fonction principale de validation stricte 2018-2025"""
    return strict_validator.validate_indicators(data, content)

def is_economic_indicator_valid(indicator_name: str) -> bool:
    """Vérifie si un nom d'indicateur est économiquement valide"""
    return not strict_validator._should_reject_item({'indicator_name': indicator_name})

def is_year_in_target_period(year: int) -> bool:
    """Vérifie si une année est dans la période cible 2018-2025"""
    return strict_validator._is_year_in_target_period(year)

# Export
__all__ = [
    'EconomicIndicator',
    'StrictDataValidator', 
    'strict_validator',
    'validate_indicators_strict',
    'is_economic_indicator_valid',
    'is_year_in_target_period'
]