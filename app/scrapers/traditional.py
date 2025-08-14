import re
from typing import Optional, Dict, Any, List
import requests
from bs4 import BeautifulSoup
import logging
import time
import json
from datetime import datetime
from urllib.parse import urlparse
from app.models.schemas import ScrapedContent
from app.config.settings import settings

logger = logging.getLogger(__name__)

class TunisianWebScraper:
    def __init__(self, delay: float = None):
        self.delay = delay or settings.DEFAULT_DELAY
        # 🔥 CORRECTION PRINCIPALE: Augmenter la limite de contenu
        self.max_content_length = getattr(settings, 'MIN_CONTENT_LENGTH', 50000)  # Augmenté de 5000 à 50000
        # Attributs supplémentaires pour compatibilité
        self.timeout = getattr(settings, 'REQUEST_TIMEOUT', 30)
        self.max_retries = getattr(settings, 'MAX_SCRAPE_RETRIES', 3)
        self.user_agent = getattr(settings, 'SCRAPE_USER_AGENT', 'Mozilla/5.0 (compatible; AgenticScraper/1.0)')
        
        self._prepare_smart_patterns()
        
    def _prepare_smart_patterns(self) -> None:
        """Prépare les patterns intelligents optimisés"""
        
        # Patterns d'exclusion pour éviter les faux positifs
        self.exclusion_patterns = [
            r'\b(2024|2025|2023|2022|2021|2020|2019|2018)\b',  # Années seules
            r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b',  # Mois
            r'\b(1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)\b',  # Jours
            r'\bpage\s+\d+\b',  # Numéros de page
            r'\bfichier\b',  # Références aux fichiers
            r'\bcontact\b',  # Informations de contact
            r'\bmise\s+à\s+jour\b',  # Mentions de mise à jour
        ]
        
        # 🔥 AMÉLIORATION: Patterns pour données de chômage INS
        self.economic_indicator_patterns = [
            # Taux avec contexte économique explicite
            r'(taux\s+(?:d\'intérêt\s+)?directeur(?:\s+bct)?)\s*:?\s*([0-9]+[,.]?[0-9]*)\s*%',
            r'(taux\s+(?:de\s+)?rémunération\s+(?:de\s+l\')?épargne(?:\s+\(tre\))?)\s*:?\s*([0-9]+[,.]?[0-9]*)\s*%',
            r'(taux\s+(?:moyen\s+)?(?:du\s+)?marché\s+monétaire(?:\s+\([tm]+\))?)\s*:?\s*([0-9]+[,.]?[0-9]*)\s*%',
            r'((?:taux\s+d\')?inflation(?:\s+sous-jacente)?)\s*:?\s*([0-9]+[,.]?[0-9]*)\s*%',
            
            # Montants financiers avec contexte
            r'(compte\s+courant\s+du\s+trésor)\s*:?\s*([0-9\s]+[,.]?[0-9]*)\s*(mdt?|millions?)',
            r'(billets\s+et\s+monnaies\s+en\s+circulation)\s*:?\s*([0-9\s]+[,.]?[0-9]*)\s*(mdt?|millions?)',
            r'(volume\s+global\s+de\s+refinancement)\s*:?\s*([0-9\s]+[,.]?[0-9]*)\s*(mdt?|millions?)',
            r'(avoirs\s+nets\s+en\s+devises)\s*:?\s*([0-9\s]+[,.]?[0-9]*)\s*(mdt?|millions?)',
            
            # 🔥 NOUVEAUX: Patterns spécifiques pour données de chômage
            r'(Evolution\s+de\s+la\s+population\s+active\s+en\s+chômage)\s*([0-9]+[,.]?[0-9]*)',
            r'(Masculin)\s*([0-9]+[,.]?[0-9]*)',
            r'(Féminin)\s*([0-9]+[,.]?[0-9]*)',
            
            # Indices et ratios
            r'(indice\s+(?:des\s+)?prix\s+(?:à\s+)?(?:la\s+)?consommation(?:\s+\(ipc\))?)\s*(?:\([^)]+\))?\s*:?\s*([0-9]+[,.]?[0-9]*)',
            r'(taux\s+de\s+(?:couverture|croissance))\s*:?\s*([0-9]+[,.]?[0-9]*)\s*%',
            
            # Patterns flexibles avec validation contextuelle
            r'([a-zA-ZÀâäéèêëïîôöùûüÿç\s]{10,50})\s*:?\s*([0-9\s]+[,.]?[0-9]*)\s*(%|mdt?|millions?|milliards?)',
        ]
        
        # Mapping intelligent des catégories
        self.smart_category_mapping = {
            'taux directeur': 'finance_et_monnaie',
            'taux d\'intérêt': 'finance_et_monnaie', 
            'rémunération épargne': 'finance_et_monnaie',
            'marché monétaire': 'finance_et_monnaie',
            'compte trésor': 'finance_et_monnaie',
            'billets monnaies': 'finance_et_monnaie',
            'refinancement': 'finance_et_monnaie',
            'avoirs devises': 'finance_et_monnaie',
            'inflation': 'prix_et_inflation',
            'indice prix': 'prix_et_inflation',
            'ipc': 'prix_et_inflation',
            'couverture': 'commerce_exterieur',
            'export': 'commerce_exterieur',
            'import': 'commerce_exterieur',
            'croissance': 'production_et_activite',
            'pib': 'production_et_activite',
            # 🔥 NOUVEAUX: Catégories pour données sociales
            'evolution': 'menages',
            'population active': 'menages',
            'chômage': 'menages',
            'masculin': 'menages',
            'féminin': 'menages'
        }

    def scrape(self, url: str) -> Optional[ScrapedContent]:
        """Point d'entrée principal optimisé"""
        try:
            logger.info(f"🌐 Universal scraping: {url}")
            
            # Récupération avec timeout optimisé
            response = requests.get(url, timeout=self.timeout, headers={
                'User-Agent': self.user_agent
            })
            response.raise_for_status()
            
            logger.info(f"📄 Content size: {len(response.text)} characters")
            
            # 🔥 CORRECTION: Ne pas limiter le contenu si c'est petit
            if len(response.text) <= self.max_content_length:
                content = response.text
                logger.info(f"Using full content: {len(content)} characters")
            else:
                content = response.text[:self.max_content_length]
                logger.info(f"Content truncated to: {len(content)} characters")
            
            # Extraction universelle optimisée
            result = self._universal_scrape(content, url)
            
            if result:
                extracted_count = len(result.structured_data.get('extracted_values', {}))
                logger.info(f"✅ Universal extraction: {extracted_count} values from {urlparse(url).netloc}")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Scraping failed for {url}: {str(e)}")
            return None

    def _universal_scrape(self, html: str, url: str) -> Optional[ScrapedContent]:
        """Scraping universel intelligent optimisé"""
        try:
            # Parse HTML de manière sécurisée
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            logger.info(f"🔍 Text content extracted: {len(text_content)} characters")
            
            # Extraction avec patterns intelligents
            extracted_values = self._extract_with_smart_patterns(text_content, url)
            
            # Post-traitement et validation
            validated_values = self._validate_and_enhance_values(extracted_values, text_content, url)
            
            # Génération des métadonnées
            metadata = self._generate_smart_metadata(url, validated_values, text_content)
            
            structured_data = {
                'extracted_values': validated_values,
                'extraction_summary': {
                    'total_values': len(validated_values),
                    'categories_found': len(set(v.get('category') for v in validated_values.values())),
                    'target_indicators_found': len([v for v in validated_values.values() if v.get('is_target_indicator')]),
                    'extraction_method': 'smart_universal',
                    'processing_time': time.time()
                },
                'settings_compliance': self._assess_settings_compliance(validated_values),
                'source_analysis': self._analyze_source(url, text_content)
            }
            
            return ScrapedContent(
                raw_content=html,
                structured_data=structured_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Universal scraping error: {e}")
            return None

    # 🔥 AJOUT: Méthodes d'information pour le worker
    def get_scraper_info(self) -> Dict[str, Any]:
        """Retourne les informations du scraper pour debugging"""
        return {
            "delay": self.delay,
            "max_content_length": self.max_content_length,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "user_agent": self.user_agent,
            "class_name": self.__class__.__name__,
            "patterns_count": len(self.economic_indicator_patterns),
            "categories_count": len(self.smart_category_mapping)
        }

    def _extract_with_smart_patterns(self, text: str, url: str) -> Dict[str, Any]:
        """Extraction avec patterns intelligents"""
        extracted = {}
        
        # 🔥 NOUVEAU: Vérifier d'abord si c'est du JSON
        try:
            if text.strip().startswith('[') or text.strip().startswith('{'):
                logger.info("🔍 JSON content detected, parsing economic data...")
                
                json_data = json.loads(text)
                
                # Cas spécial: API Banque Mondiale
                if 'api.worldbank.org' in url and isinstance(json_data, list) and len(json_data) >= 2:
                    data_array = json_data[1]
                    if isinstance(data_array, list):
                        for i, record in enumerate(data_array):
                            if isinstance(record, dict) and 'value' in record and isinstance(record['value'], (int, float)):
                                value = record['value']
                                date = record.get('date', 'unknown')
                                indicator = record.get('indicator', {}).get('value', 'Economic Indicator')
                                country = record.get('country', {}).get('value', 'Unknown')
                                
                                key = f"json_wb_{i}"
                                extracted[key] = {
                                    'value': value,
                                    'raw_text': str(value),
                                    'indicator_name': f"{indicator} - {country} ({date})",
                                    'category': 'comptes_nationaux',
                                    'unit': 'USD',
                                    'unit_description': 'Dollars américains',
                                    'context_text': f"{indicator} {country} {date}: {value}",
                                    'extraction_method': 'json_worldbank',
                                    'source_domain': 'api.worldbank.org',
                                    'extraction_timestamp': datetime.utcnow().isoformat(),
                                    'confidence_score': 0.95,
                                    'is_target_indicator': True,
                                    'temporal_valid': True,
                                    'is_real_indicator': True,
                                    'validated': True
                                }
                                logger.info(f"📊 JSON extrait: {indicator} {date} = {value}")
                                
                logger.info(f"✅ JSON extraction: {len(extracted)} valeurs trouvées")
                
        except json.JSONDecodeError:
            logger.debug("Contenu n'est pas du JSON valide")
        except Exception as e:
            logger.debug(f"Erreur parsing JSON: {e}")
        
        # Continuer avec l'extraction normale pour le texte
        text_sample = text
        logger.info(f"🔍 Analyzing {len(text_sample)} characters for patterns")
        
        for i, pattern in enumerate(self.economic_indicator_patterns):
            try:
                matches = re.finditer(pattern, text_sample, re.IGNORECASE | re.MULTILINE)
                match_count = 0
                
                for match in matches:
                    if match_count >= 10:  # Plus de matches autorisés
                        break
                        
                    groups = match.groups()
                    if len(groups) >= 2:
                        indicator_raw = groups[0].strip()
                        value_str = groups[1].strip()
                        unit = groups[2].strip() if len(groups) > 2 else 'Nombre'
                        
                        # Validation immédiate
                        if self._is_excluded_value(match.group(0)):
                            continue
                            
                        # Parse numérique
                        parsed_value = self._parse_numeric_enhanced(value_str)
                        if parsed_value is None or parsed_value <= 0:
                            continue
                            
                        # Génération d'une clé unique
                        key = f"smart_{i}_{match_count}"
                        
                        # Construction de l'objet valeur
                        extracted[key] = {
                            'value': parsed_value,
                            'raw_text': value_str,
                            'indicator_name': self._clean_indicator_name(indicator_raw),
                            'category': self._categorize_intelligently(indicator_raw),
                            'unit': self._normalize_unit(unit),
                            'unit_description': self._get_unit_description(unit),
                            
                            # Métadonnées contextuelles
                            'context_text': match.group(0),
                            'pattern_index': i,
                            'extraction_method': 'smart_pattern',
                            'source_domain': urlparse(url).netloc,
                            'extraction_timestamp': datetime.utcnow().isoformat(),
                            
                            # Scores de qualité
                            'confidence_score': self._calculate_pattern_confidence(pattern, match),
                            'is_target_indicator': self._is_target_indicator(indicator_raw),
                            'temporal_valid': self._is_temporally_valid(match.group(0)),
                            'is_real_indicator': True
                        }
                        
                        match_count += 1
                        logger.debug(f"📊 Extracted: {indicator_raw} = {parsed_value}")
                        
            except Exception as e:
                logger.debug(f"Pattern {i} error: {e}")
                continue
                
        logger.info(f"Smart patterns extracted {len(extracted)} candidate values")
        return extracted

    def _validate_and_enhance_values(self, values: Dict[str, Any], text: str, url: str) -> Dict[str, Any]:
        """Validation et enrichissement des valeurs"""
        validated = {}
        
        for key, value_data in values.items():
            try:
                # Pour les données JSON (Banque Mondiale), validation très permissive
                if value_data.get('extraction_method') == 'json_worldbank':
                    validated[key] = value_data
                    validated[key]['quality_score'] = 0.95
                    continue
                
                # Tests de validation plus permissifs pour les autres
                if not self._is_valid_economic_value(value_data):
                    continue
                    
                # Enrichissement contextuel
                enhanced_data = self._enrich_value_context(value_data, text)
                
                # Score de qualité final
                quality_score = self._calculate_quality_score(enhanced_data)
                
                if quality_score >= 0.4:  # 🔥 SEUIL TRÈS PERMISSIF pour récupérer plus de données
                    enhanced_data['quality_score'] = quality_score
                    enhanced_data['validated'] = True
                    validated[key] = enhanced_data
                    
            except Exception as e:
                logger.debug(f"Validation error for {key}: {e}")
                continue
                
        logger.info(f"Validated {len(validated)}/{len(values)} extracted values")
        return validated

    def _is_excluded_value(self, text: str) -> bool:
        """Vérifie si le texte correspond à un pattern d'exclusion"""
        for pattern in self.exclusion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _parse_numeric_enhanced(self, value_str: str) -> Optional[float]:
        """Parse numérique amélioré avec gestion des espaces"""
        try:
            # Nettoyage avancé
            cleaned = re.sub(r'[^\d,.-]', '', value_str.replace(' ', ''))
            cleaned = cleaned.replace(',', '.')
            
            if not cleaned or cleaned in ['.', '-']:
                return None
                
            parsed = float(cleaned)
            
            # Validation des plages réalistes - PLUS PERMISSIVE
            if 0.01 <= parsed <= 10000000:  # Plage très large
                return parsed
                
        except (ValueError, OverflowError):
            pass
            
        return None

    def _clean_indicator_name(self, raw_name: str) -> str:
        """Nettoie et standardise le nom d'indicateur"""
        # Nettoyage de base
        cleaned = re.sub(r'[^\w\s\'\(\)-]', ' ', raw_name)
        cleaned = ' '.join(cleaned.split())  # Normalise les espaces
        
        # Mapping vers noms standards pour données de chômage
        name_mappings = {
            'evolution de la population active en chômage': 'Evolution de la population active en chômage',
            'masculin': 'Chômage - Population masculine',
            'féminin': 'Chômage - Population féminine',
            'taux directeur': 'Taux d\'intérêt directeur BCT',
            'inflation': 'Taux d\'inflation'
        }
        
        cleaned_lower = cleaned.lower()
        for key, standard_name in name_mappings.items():
            if key in cleaned_lower:
                return standard_name
                
        return cleaned.title()

    def _categorize_intelligently(self, indicator_text: str) -> str:
        """Catégorisation intelligente basée sur le contenu"""
        text_lower = indicator_text.lower()
        
        # Recherche dans le mapping intelligent
        for key_phrase, category in self.smart_category_mapping.items():
            if key_phrase in text_lower:
                return category
                
        # Catégorisation par mots-clés
        if any(word in text_lower for word in ['chômage', 'population', 'masculin', 'féminin', 'evolution']):
            return 'menages'
        elif any(word in text_lower for word in ['taux', 'directeur', 'monétaire', 'épargne']):
            return 'finance_et_monnaie'
        elif any(word in text_lower for word in ['inflation', 'prix', 'ipc']):
            return 'prix_et_inflation'
        else:
            return 'economie_generale'

    def _normalize_unit(self, unit_str: str) -> str:
        """Normalise les unités"""
        unit_lower = unit_str.lower().strip()
        
        unit_mappings = {
            '%': '%',
            'mdt': 'MDT',
            'millions': 'MDT',
            'nombre': 'Milliers',
            'milliers': 'Milliers'
        }
        
        return unit_mappings.get(unit_lower, unit_str)

    def _get_unit_description(self, unit: str) -> str:
        """Description des unités"""
        descriptions = {
            '%': 'Pourcentage',
            'MDT': 'Millions de Dinars Tunisiens',
            'Milliers': 'Milliers de personnes',
            'Nombre': 'Nombre (unité)',
            'USD': 'Dollars américains'
        }
        return descriptions.get(unit, 'Unité non spécifiée')

    def _calculate_pattern_confidence(self, pattern: str, match) -> float:
        """Calcule la confiance du pattern"""
        base_confidence = 0.7
        
        # Bonus pour patterns spécifiques
        if any(word in pattern.lower() for word in ['evolution', 'masculin', 'féminin']):
            base_confidence += 0.2
        if ':' in match.group(0):
            base_confidence += 0.1
            
        return min(base_confidence, 1.0)

    def _is_target_indicator(self, indicator_name: str) -> bool:
        """Vérifie si c'est un indicateur cible"""
        name_lower = indicator_name.lower()
        
        # Indicateurs spécifiques pour chômage
        chomage_indicators = ['chômage', 'population active', 'masculin', 'féminin', 'evolution']
        if any(indicator in name_lower for indicator in chomage_indicators):
            return True
            
        for category, indicators in settings.TARGET_INDICATORS.items():
            if any(indicator.lower() in name_lower or name_lower in indicator.lower() 
                   for indicator in indicators):
                return True
        return False

    def _is_temporally_valid(self, context: str) -> bool:
        """Vérifie la validité temporelle"""
        # Cherche des années dans le contexte
        years = re.findall(r'\b(20\d{2})\b', context)
        if years:
            return any(int(year) in settings.TARGET_YEARS for year in years)
        return True

    def _is_valid_economic_value(self, value_data: Dict[str, Any]) -> bool:
        """Validation globale de la valeur économique - PLUS PERMISSIVE"""
        try:
            value = value_data.get('value', 0)
            indicator = value_data.get('indicator_name', '').lower()
            
            # Tests de validité basiques
            if value <= 0:
                return False
                
            # Validation spéciale pour données de chômage
            if any(word in indicator for word in ['chômage', 'population', 'masculin', 'féminin']):
                return 10 <= value <= 2000  # Chômage entre 10k et 2M personnes
                
            # Validation générale très permissive
            return 0.01 <= value <= 1000000000
            
        except Exception:
            return False

    def _enrich_value_context(self, value_data: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Enrichit le contexte de la valeur"""
        enhanced = value_data.copy()
        
        # Recherche de contexte temporel
        context = enhanced.get('context_text', '')
        
        # Extraction de trimestres pour données INS
        trimestre_patterns = [
            r'(première|deuxième|troisième|quatrième)[-\s]*trimestre\s+(\d{4})',
            r'T(\d)\s+(\d{4})',
            r'(\d{4})'
        ]
        
        for pattern in trimestre_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                enhanced['temporal_context'] = {
                    'reference_period': match.group(0),
                    'year_detected': match.groups()[-1] if match.groups()[-1].isdigit() else None
                }
                break
                
        # Identification de la source INS
        if 'ins' in text.lower() or 'institut national' in text.lower():
            enhanced['institutional_source'] = 'Institut National de la Statistique'
            
        return enhanced

    def _calculate_quality_score(self, value_data: Dict[str, Any]) -> float:
        """Calcule le score de qualité global"""
        score = 0.0
        
        # Score de base pour l'extraction
        score += value_data.get('confidence_score', 0) * 0.4
        
        # Bonus pour indicateur cible
        if value_data.get('is_target_indicator'):
            score += 0.3  # Plus de poids
            
        # Bonus pour validité temporelle
        if value_data.get('temporal_valid'):
            score += 0.1
            
        # Bonus pour contexte riche
        context = value_data.get('context_text', '')
        if len(context) > 10:  # Plus permissif
            score += 0.2
            
        return min(score, 1.0)

    def _generate_smart_metadata(self, url: str, values: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Génère des métadonnées intelligentes"""
        domain = urlparse(url).netloc
        
        return {
            'source_url': url,
            'source_domain': domain,
            'is_trusted_source': domain in [source.lower() for source in settings.TRUSTED_SOURCES],
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'content_length': len(text),
            'extraction_quality': {
                'total_extracted': len(values),
                'high_quality_count': len([v for v in values.values() if v.get('quality_score', 0) > 0.8]),
                'target_indicators_found': len([v for v in values.values() if v.get('is_target_indicator')]),
                'categories_covered': len(set(v.get('category') for v in values.values()))
            },
            'processing_info': {
                'scraper_version': 'smart_universal_v2.0',
                'extraction_method': 'intelligent_patterns',
                'validation_enabled': True
            }
        }

    def _analyze_source(self, url: str, text: str) -> Dict[str, Any]:
        """Analyse de la source"""
        domain = urlparse(url).netloc
        
        analysis = {
            'domain': domain,
            'is_government': domain.endswith('.tn') and any(gov in domain for gov in ['gov', 'ins', 'bct']),
            'content_type': 'statistical_data' if any(term in text.lower() for term in ['statistique', 'données', 'indicateur']) else 'general',
            'language': 'french' if any(term in text.lower() for term in ['le', 'la', 'des', 'du']) else 'unknown',
            'data_freshness': 'recent' if str(datetime.now().year) in text else 'historical'
        }
        
        return analysis

    def _assess_settings_compliance(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Évaluation de la conformité aux settings"""
        if not values:
            return {'compliant': False, 'details': 'No values extracted'}
            
        compliance = {
            'target_indicators_found': len([v for v in values.values() if v.get('is_target_indicator')]),
            'recognized_units_used': len([v for v in values.values() if v.get('unit') in settings.RECOGNIZED_UNITS]),
            'temporal_validity': len([v for v in values.values() if v.get('temporal_valid')]),
            'total_values': len(values)
        }
        
        compliance['compliance_score'] = (
            (compliance['target_indicators_found'] > 0) * 0.4 +
            (compliance['recognized_units_used'] > 0) * 0.3 +
            (compliance['temporal_validity'] > 0) * 0.3
        )
        
        compliance['compliant'] = compliance['compliance_score'] >= 0.3  # Plus permissif
        
        return compliance