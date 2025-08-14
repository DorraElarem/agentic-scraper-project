import re
import json
import asyncio
import aiohttp
import time
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime
from app.models.schemas import ScrapedContent, AnalysisResult, AnalysisType
from app.config.settings import settings, AnalysisCategory
from .traditional import TunisianWebScraper

logger = logging.getLogger(__name__)

class IntelligentScraper(TunisianWebScraper):
    def __init__(self, delay: float = None):
        super().__init__(delay or settings.DEFAULT_DELAY)
        self._prepare_intelligence_layer()
        
        # Configuration Ollama
        self.ollama_url = "http://ollama:11434"
        self.ollama_model = "tinyllama"  # Modèle détecté
        self.llm_timeout = 120  # 🔧 CORRIGÉ: Augmenté de 30s à 120s

    def _prepare_intelligence_layer(self) -> None:
        """Prépare la couche d'intelligence avec reconnaissance contextuelle avancée"""
        
        # Patterns d'enrichissement contextuel
        self.context_enrichment_patterns = {
            'temporal_markers': [
                r'au\s+(\d{1,2})/(\d{1,2})/(\d{4})',  # au 11/08/2025
                r'du\s+mois\s+de\s+(\w+)\s+(\d{4})',  # du mois de juillet 2025
                r'(\w+)\s+(\d{4})',  # juillet 2025
                r'T(\d)\s+(\d{4})',  # T3 2025
            ],
            
            'institutional_sources': [
                r'source\s*:\s*(.+?)(?:\n|$)',
                r'institut\s+national\s+de\s+la\s+statistique',
                r'banque\s+centrale\s+de\s+tunisie',
                r'mise\s+à\s+jour\s*:\s*(.+?)(?:\n|$)'
            ],
            
            'indicator_qualifiers': [
                r'(taux\s+d\'intérêt\s+directeur)',
                r'(taux\s+de\s+rémunération\s+de\s+l\'épargne)',
                r'(compte\s+courant\s+du\s+trésor)',
                r'(billets\s+et\s+monnaies\s+en\s+circulation)',
                r'(volume\s+global\s+de\s+refinancement)',
                r'(avoirs\s+nets\s+en\s+devises)',
                r'(indice\s+des\s+prix\s+à\s+la\s+consommation)',
                r'(inflation\s+sous-jacente)'
            ],
            
            'value_context_patterns': [
                r'([a-zA-Zàâäéèêëïîôöùûüÿç\s]+)\s*:\s*([0-9]+[,.]?[0-9]*)\s*(%|MDT?|TND|millions?)',
                r'([a-zA-Zàâäéèêëïîôöùûüÿç\s]+)\s+(?:atteint|est de|s\'élève à)\s*([0-9]+[,.]?[0-9]*)\s*(%|MDT?|TND)',
                r'([0-9]+[,.]?[0-9]*)\s*(%|MDT?|TND)\s+(?:pour|de|du)\s+([a-zA-Zàâäéèêëïîôöùûüÿç\s]+)'
            ]
        }
        
        # Mappings intelligents pour noms d'indicateurs
        self.smart_indicator_mapping = {
            'taux directeur': 'Taux d\'intérêt directeur BCT',
            'taux du marché monétaire': 'Taux du marché monétaire (TM)',
            'taux moyen du marché monétaire': 'Taux moyen du marché monétaire (TMM)', 
            'tre': 'Taux de rémunération de l\'épargne (TRE)',
            'taux de rémunération de l\'épargne': 'Taux de rémunération de l\'épargne (TRE)',
            'compte courant du trésor': 'Compte courant du Trésor',
            'billets et monnaies en circulation': 'Billets et monnaies en circulation',
            'volume global de refinancement': 'Volume global de refinancement',
            'avoirs nets en devises': 'Avoirs nets en devises',
            'inflation': 'Taux d\'inflation',
            'inflation sous-jacente': 'Taux d\'inflation sous-jacente',
            'ipc': 'Indice des Prix à la Consommation (IPC)',
            'tunibor': 'Taux interbancaire tunisien (TUNIBOR)',
            'gdp': 'Produit Intérieur Brut (PIB)',
            'pib': 'Produit Intérieur Brut (PIB)'
        }

    async def _test_ollama_connection(self) -> Dict[str, Any]:
        """Test de connexion Ollama"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.ollama_url}/api/version") as response:
                    if response.status == 200:
                        version_data = await response.json()
                        return {
                            "status": "connected",
                            "version": version_data.get("version", "unknown"),
                            "model_available": self.ollama_model
                        }
                    else:
                        return {"status": "version_failed", "http_status": response.status}
        except Exception as e:
            return {
                "status": "connection_failed",
                "error": str(e)
            }

    async def _analyze_with_ollama(self, content: str, extracted_values: Dict[str, Any]) -> Dict[str, Any]:
        """🔧 CORRIGÉ: Analyse avec Ollama - timeout amélioré"""
        
        # Test de connexion
        connection_test = await self._test_ollama_connection()
        if connection_test["status"] != "connected":
            return {
                "error": f"Ollama non disponible: {connection_test.get('error', 'Service non connecté')}",
                "llm_status": "not_available",
                "connection_details": connection_test
            }

        # Créer le prompt d'analyse
        prompt = self._create_analysis_prompt(content, extracted_values)
        
        try:
            # 🔧 TIMEOUT AUGMENTÉ à 120s
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.llm_timeout)) as session:
                payload = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.8,
                        "max_tokens": 300,  # 🔧 RÉDUIT de 400 à 300 pour accélérer
                        "stop": ["\n\n", "---", "Conclusion:"]  # 🔧 AJOUT de stops pour accélérer
                    }
                }
                
                logger.info(f"🤖 Démarrage analyse Ollama (timeout: {self.llm_timeout}s)")
                start_time = time.time()
                
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        processing_time = time.time() - start_time
                        
                        logger.info(f"✅ Ollama terminé en {processing_time:.2f}s")
                        
                        return {
                            "analysis": result.get("response", ""),
                            "model_used": self.ollama_model,
                            "llm_status": "success",
                            "confidence_score": 0.85,
                            "processing_time": processing_time,
                            "tokens_generated": result.get("eval_count", 0)
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"Erreur Ollama HTTP {response.status}: {error_text}",
                            "llm_status": "http_error"
                        }
                        
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout Ollama après {self.llm_timeout}s")
            return {
                "error": f"Timeout Ollama après {self.llm_timeout}s - Modèle trop lent",
                "llm_status": "timeout",
                "suggestion": "Essayer avec un modèle plus léger comme tinyllama"
            }
        except Exception as e:
            logger.error(f"Erreur Ollama: {str(e)}")
            return {
                "error": f"Erreur Ollama: {str(e)}",
                "llm_status": "error"
            }

    def _create_analysis_prompt(self, content: str, extracted_values: Dict[str, Any]) -> str:
        """Créer le prompt d'analyse pour Ollama"""
        
        # Résumé des valeurs extraites
        values_summary = []
        for key, value_data in extracted_values.items():
            if isinstance(value_data, dict):
                name = value_data.get('indicator_name', key)
                value = value_data.get('value', 0)
                unit = value_data.get('unit', '')
                values_summary.append(f"- {name}: {value} {unit}")
        
        values_text = "\n".join(values_summary) if values_summary else "Aucune valeur extraite"
        
        # Extrait du contenu pour contexte
        content_preview = content[:300] + "..." if len(content) > 300 else content
        
        prompt = f"""Analysez ces données économiques tunisiennes:

VALEURS EXTRAITES:
{values_text}

CONTEXTE DU CONTENU:
{content_preview}

Fournissez une analyse concise incluant:
1. Type de données économiques (PIB, inflation, taux directeur, etc.)
2. Qualité et fiabilité (source officielle, données récentes)
3. Tendances observées (hausse, baisse, stabilité)
4. Contexte économique tunisien

Réponse structurée (max 200 mots):"""
        
        return prompt

    def scrape_with_analysis(self, url: str, enable_llm_analysis: bool = False) -> Optional[ScrapedContent]:
        """🔧 CORRIGÉ: Point d'entrée principal avec paramètre enable_llm_analysis"""
        try:
            logger.info(f"🧠 Starting enhanced intelligent scraping for: {url}")
            logger.info(f"🤖 LLM Analysis: {'Enabled' if enable_llm_analysis else 'Disabled'}")
            
            # Scraping de base avec le parent amélioré
            base_data = super().scrape(url)
            if not base_data:
                logger.warning(f"No base data from smart scraper for {url}")
                return None
            
            # 🔧 CORRIGÉ: Passer enable_llm_analysis à l'analyse
            enhanced_analysis = self._perform_enhanced_analysis(
                base_data.raw_content, 
                base_data.structured_data, 
                url,
                enable_llm_analysis  # 🔧 NOUVEAU paramètre
            )
            
            # Fusion des données avec l'analyse intelligente
            enriched_data = {
                **base_data.structured_data,
                'intelligent_analysis': enhanced_analysis.dict() if enhanced_analysis else {},
                'enhancement_method': 'intelligent_contextual',
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'settings_compliance': self._assess_enhanced_compliance(base_data.structured_data)
            }
            
            return ScrapedContent(
                raw_content=base_data.raw_content,
                structured_data=enriched_data,
                metadata={
                    **base_data.metadata,
                    'analysis_method': 'intelligent_contextual',
                    'ai_enhanced': True,
                    'context_enriched': True,
                    'semantic_validation': True
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced intelligent scraping failed for {url}: {str(e)}", exc_info=True)
            return None

    def _perform_enhanced_analysis(self, html: str, base_data: Dict[str, Any], url: str, enable_llm: bool = False) -> Optional[AnalysisResult]:
        """🔧 CORRIGÉ: Analyse intelligente avec paramètre enable_llm"""
        try:
            text_content = html
            extracted_values = base_data.get('extracted_values', {})
            
            # 1. Enrichissement contextuel des valeurs existantes
            enriched_values = self._enrich_with_context_intelligence(extracted_values, text_content)
            
            # 2. Validation sémantique et nettoyage intelligent
            validated_values = self._semantic_validation_and_cleanup(enriched_values, text_content)
            
            # 3. Extraction d'indicateurs manqués avec IA contextuelle
            missed_indicators = self._extract_missed_indicators_with_ai(text_content, validated_values)
            validated_values.update(missed_indicators)
            
            # 4. Analyse des relations et cohérence
            coherence_analysis = self._analyze_data_coherence(validated_values)
            
            # 5. 🔧 CORRIGÉ: Passer enable_llm aux insights
            smart_insights = self._generate_smart_insights_sync(validated_values, text_content, url, coherence_analysis, enable_llm)
            
            # 6. Construire la liste d'indicateurs pour AnalysisResult
            indicators_list = self._build_indicators_list(validated_values)
            
            return AnalysisResult(
                indicators=indicators_list,
                confidence=self._calculate_enhanced_confidence(validated_values, coherence_analysis),
                analysis_type=AnalysisType.ADVANCED,
                insights=smart_insights
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced analysis: {e}")
            return None

    def _build_indicators_list(self, extracted_values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Construire la liste d'indicateurs pour AnalysisResult"""
        indicators_list = []
        
        for key, value_data in extracted_values.items():
            if isinstance(value_data, dict):
                indicator = {
                    "id": key,
                    "name": value_data.get("enhanced_indicator_name", value_data.get("indicator_name", "")),
                    "value": value_data.get("value", 0),
                    "unit": value_data.get("unit", ""),
                    "category": value_data.get("category", ""),
                    "confidence": value_data.get("confidence_score", 0),
                    "validated": value_data.get("validated", False),
                    "extraction_method": value_data.get("extraction_method", ""),
                    "temporal_info": value_data.get("temporal_metadata", {}),
                    "source": value_data.get("institutional_source", "")
                }
                indicators_list.append(indicator)
        
        return indicators_list

    def _generate_smart_insights_sync(self, values: Dict[str, Any], text: str, url: str, coherence: Dict[str, Any], enable_llm: bool = False) -> Dict[str, Any]:
        """🔧 CORRIGÉ: Génère des insights avec LLM seulement si enable_llm=True"""
        insights = {
            'data_summary': self._generate_data_summary(values),
            'quality_assessment': self._assess_data_quality(values, coherence),
            'indicator_analysis': self._analyze_indicators(values),
            'temporal_analysis': self._analyze_temporal_patterns(values),
            'recommendations': self._generate_recommendations(values, coherence),
            'llm_analysis': self._run_llm_analysis_sync(text, values) if enable_llm else self._create_llm_disabled_response()
        }
        
        return insights

    def _create_llm_disabled_response(self) -> Dict[str, Any]:
        """🔧 NOUVEAU: Réponse quand LLM est désactivé"""
        return {
            "insights": {
                "message": "Analyse LLM désactivée par l'utilisateur"
            },
            "llm_status": "disabled_by_user",
            "processing_time": 0,
            "model_used": None
        }

    def _run_llm_analysis_sync(self, content: str, extracted_values: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute l'analyse LLM de manière synchrone"""
        try:
            # Utiliser asyncio pour exécuter la fonction async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self._analyze_with_ollama(content, extracted_values))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error running LLM analysis: {e}")
            return {
                "error": f"Erreur lors de l'analyse LLM: {str(e)}",
                "llm_status": "sync_error"
            }

    def _enrich_with_context_intelligence(self, values: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Enrichissement contextuel intelligent des valeurs"""
        enriched = {}
        
        for key, value_data in values.items():
            try:
                enhanced_data = value_data.copy()
                context = value_data.get('context_text', '')
                
                # Amélioration intelligente du nom d'indicateur
                enhanced_data['enhanced_indicator_name'] = self._enhance_indicator_name_intelligently(
                    context, value_data.get('indicator_name', ''), value_data.get('value', 0)
                )
                
                # Extraction de métadonnées temporelles précises
                enhanced_data['temporal_metadata'] = self._extract_precise_temporal_data(context)
                
                # Identification de la source institutionnelle
                enhanced_data['institutional_source'] = self._identify_institutional_source(context)
                
                # Validation de la cohérence économique
                enhanced_data['economic_coherence'] = self._validate_economic_coherence(
                    value_data.get('value', 0), 
                    enhanced_data['enhanced_indicator_name'],
                    context
                )
                
                # Score de qualité sémantique
                enhanced_data['semantic_quality'] = self._calculate_semantic_quality(enhanced_data)
                
                enriched[key] = enhanced_data
                
            except Exception as e:
                logger.debug(f"Error enriching value {key}: {e}")
                enriched[key] = value_data
                
        return enriched

    def _semantic_validation_and_cleanup(self, values: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Validation sémantique et nettoyage intelligent"""
        validated = {}
        
        for key, value_data in values.items():
            try:
                value = value_data.get('value', 0)
                indicator_name = value_data.get('enhanced_indicator_name', value_data.get('indicator_name', ''))
                context = value_data.get('context_text', '')
                
                # Tests de validation sémantique
                validations = {
                    'is_economic_indicator': self._is_genuine_economic_indicator(indicator_name, context, value),
                    'is_temporally_coherent': self._is_temporally_coherent(value_data.get('temporal_metadata', {})),
                    'is_value_plausible': self._is_value_economically_plausible(value, indicator_name),
                    'has_institutional_backing': bool(value_data.get('institutional_source')),
                    'semantic_score': value_data.get('semantic_quality', 0)
                }
                
                # Score de validation global
                validation_score = sum([
                    validations['is_economic_indicator'] * 0.3,
                    validations['is_temporally_coherent'] * 0.2,
                    validations['is_value_plausible'] * 0.2,
                    validations['has_institutional_backing'] * 0.1,
                    validations['semantic_score'] * 0.2
                ])
                
                # Garder seulement les valeurs avec score suffisant
                if validation_score >= 0.4:  # Seuil abaissé pour être moins strict
                    value_data['validation_details'] = validations
                    value_data['overall_validation_score'] = validation_score
                    value_data['validated'] = True
                    validated[key] = value_data
                    
                    logger.debug(f"✅ Validated indicator: {indicator_name} (score: {validation_score:.2f})")
                else:
                    logger.debug(f"❌ Rejected indicator: {indicator_name} (score: {validation_score:.2f})")
                    
            except Exception as e:
                logger.debug(f"Error validating {key}: {e}")
                
        return validated

    def _extract_missed_indicators_with_ai(self, text: str, existing_values: Dict[str, Any]) -> Dict[str, Any]:
        """Extraction d'indicateurs manqués avec IA contextuelle"""
        missed_indicators = {}
        
        try:
            # Analyser les patterns de valeurs contextuels
            for pattern in self.context_enrichment_patterns['value_context_patterns']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    try:
                        groups = match.groups()
                        if len(groups) >= 3:
                            # Extraction flexible selon le pattern
                            if groups[1] and groups[2]:  # Pattern: nom : valeur unité
                                indicator_raw = groups[0].strip()
                                value_str = groups[1]
                                unit = groups[2]
                            elif groups[0] and groups[2]:  # Pattern: valeur unité pour nom
                                value_str = groups[0] 
                                unit = groups[1]
                                indicator_raw = groups[2].strip()
                            else:
                                continue
                            
                            # Parser la valeur
                            parsed_value = self._parse_numeric_enhanced(value_str)
                            if parsed_value is None:
                                continue
                            
                            # Nettoyer et mapper le nom d'indicateur
                            indicator_name = self._map_to_smart_indicator_name(indicator_raw)
                            
                            # Vérifier si ce n'est pas déjà extrait
                            if self._is_already_extracted(indicator_name, parsed_value, existing_values):
                                continue
                            
                            # Catégoriser intelligemment
                            category = self._categorize_intelligently(indicator_name, indicator_raw)
                            
                            # Valider la cohérence
                            if self._is_coherent_new_indicator(indicator_name, parsed_value, unit, category):
                                key = f"ai_extracted_{len(missed_indicators)}"
                                
                                missed_indicators[key] = {
                                    'value': parsed_value,
                                    'raw_text': value_str,
                                    'indicator_name': indicator_name,
                                    'enhanced_indicator_name': indicator_name,
                                    'category': category,
                                    'unit': unit,
                                    'unit_description': self._get_unit_description(unit),
                                    
                                    'context_text': match.group(0),
                                    'extraction_method': 'ai_contextual_pattern',
                                    'is_real_indicator': True,
                                    'confidence_score': 0.85,
                                    'semantic_quality': 0.9,
                                    'validated': True,
                                    'extraction_date': datetime.now().isoformat()
                                }
                                
                                logger.info(f"🔍 AI extracted missed indicator: {indicator_name} = {parsed_value} {unit}")
                                
                    except Exception as e:
                        logger.debug(f"Error processing AI pattern match: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in AI missed indicators extraction: {e}")
            
        return missed_indicators

    def _enhance_indicator_name_intelligently(self, context: str, current_name: str, value: float) -> str:
        """Amélioration intelligente du nom d'indicateur"""
        context_lower = context.lower()
        
        # Mapping pour données World Bank
        if 'gdp' in context_lower or 'current us$' in context_lower:
            return 'Produit Intérieur Brut (PIB) - USD courants'
        
        # Recherche de patterns spécifiques dans le contexte
        for pattern in self.context_enrichment_patterns['indicator_qualifiers']:
            match = re.search(pattern, context_lower)
            if match:
                matched_text = match.group(1)
                return self._map_to_smart_indicator_name(matched_text)
        
        # Mapping intelligent basé sur le contexte et la valeur
        if 'directeur' in context_lower and 0 < value < 20:
            return 'Taux d\'intérêt directeur BCT'
        elif 'marché monétaire' in context_lower and 'moyen' in context_lower:
            return 'Taux moyen du marché monétaire (TMM)'
        elif 'marché monétaire' in context_lower:
            return 'Taux du marché monétaire (TM)'
        elif 'épargne' in context_lower and 'rémunération' in context_lower:
            return 'Taux de rémunération de l\'épargne (TRE)'
        
        return current_name

    def _map_to_smart_indicator_name(self, raw_name: str) -> str:
        """Mapping intelligent vers noms d'indicateurs standardisés"""
        raw_lower = raw_name.lower().strip()
        
        # Recherche directe dans le mapping
        if raw_lower in self.smart_indicator_mapping:
            return self.smart_indicator_mapping[raw_lower]
        
        # Recherche par mots-clés
        for key, mapped_name in self.smart_indicator_mapping.items():
            if key in raw_lower or any(word in raw_lower for word in key.split()):
                return mapped_name
        
        # Nettoyage et capitalisation
        cleaned = re.sub(r'[^\w\s\'\(\)-]', '', raw_name).strip()
        return cleaned.title() if cleaned else 'Indicateur économique'

    def _extract_precise_temporal_data(self, context: str) -> Dict[str, Any]:
        """Extraction précise des données temporelles"""
        temporal_data = {
            'reference_date': None,
            'period_type': 'unknown',
            'is_current_period': False,
            'year': None,
            'month': None,
            'day': None
        }
        
        try:
            # Détecter les années dans le contexte (important pour World Bank)
            year_pattern = r'\b(20\d{2})\b'
            year_match = re.search(year_pattern, context)
            if year_match:
                temporal_data['year'] = int(year_match.group(1))
                temporal_data['reference_date'] = year_match.group(1)
                temporal_data['period_type'] = 'yearly'
                temporal_data['is_current_period'] = temporal_data['year'] >= 2020
            
            for pattern in self.context_enrichment_patterns['temporal_markers']:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 3:  # jour/mois/année
                        temporal_data.update({
                            'day': int(groups[0]),
                            'month': int(groups[1]) if groups[1].isdigit() else groups[1],
                            'year': int(groups[2]),
                            'reference_date': match.group(0),
                            'period_type': 'daily'
                        })
                    elif len(groups) == 2:  # mois année
                        temporal_data.update({
                            'month': groups[0] if not groups[0].isdigit() else int(groups[0]),
                            'year': int(groups[1]),
                            'reference_date': match.group(0),
                            'period_type': 'monthly'
                        })
                    
                    temporal_data['is_current_period'] = temporal_data['year'] == datetime.now().year
                    break
                    
        except Exception as e:
            logger.debug(f"Error extracting temporal data: {e}")
            
        return temporal_data

    def _identify_institutional_source(self, context: str) -> Optional[str]:
        """Identification de la source institutionnelle"""
        context_lower = context.lower()
        
        sources = {
            'bct': 'Banque Centrale de Tunisie',
            'banque centrale': 'Banque Centrale de Tunisie',
            'ins': 'Institut National de la Statistique',
            'institut national de la statistique': 'Institut National de la Statistique',
            'source : institut': 'Institut National de la Statistique',
            'world bank': 'Banque Mondiale',
            'worldbank': 'Banque Mondiale',
            'api.worldbank.org': 'Banque Mondiale'
        }
        
        for pattern, source in sources.items():
            if pattern in context_lower:
                return source
                
        return None

    def _is_genuine_economic_indicator(self, indicator_name: str, context: str, value: float) -> bool:
        """Vérifie si c'est un vrai indicateur économique"""
        indicator_lower = indicator_name.lower()
        context_lower = context.lower()
        
        # Indicateurs économiques reconnus
        economic_terms = [
            'taux', 'inflation', 'pib', 'gdp', 'commerce', 'export', 'import',
            'monétaire', 'directeur', 'épargne', 'refinancement', 'compte',
            'circulation', 'devises', 'croissance', 'population'
        ]
        
        # Termes non économiques
        non_economic_terms = [
            'date', 'jour', 'mois', 'année', 'mise à jour', 'source',
            'page', 'fichier', 'lien', 'contact'
        ]
        
        has_economic_terms = any(term in indicator_lower for term in economic_terms)
        has_non_economic_terms = any(term in indicator_lower for term in non_economic_terms)
        
        return has_economic_terms and not has_non_economic_terms

    def _is_temporally_coherent(self, temporal_metadata: Dict[str, Any]) -> bool:
        """Vérifie la cohérence temporelle"""
        try:
            year = temporal_metadata.get('year')
            if year and isinstance(year, int):
                return 2015 <= year <= 2025  # Période réaliste
            return True  # Si pas d'info temporelle, considérer comme valide
        except:
            return True

    def _is_value_economically_plausible(self, value: float, indicator_name: str) -> bool:
        """Vérifie la plausibilité économique de la valeur"""
        indicator_lower = indicator_name.lower()
        
        # Plages réalistes par type d'indicateur
        if 'taux' in indicator_lower and '%' in indicator_name:
            return 0 <= value <= 30  # Taux entre 0 et 30%
        elif 'pib' in indicator_lower or 'gdp' in indicator_lower:
            return 1000000000 <= value <= 1000000000000  # PIB en USD (milliards)
        elif 'compte' in indicator_lower or 'volume' in indicator_lower or 'billets' in indicator_lower:
            return 100 <= value <= 100000  # Montants en MDT
        elif 'inflation' in indicator_lower:
            return 0 <= value <= 50  # Inflation réaliste
        
        return 0.01 <= value <= 1000000000000  # Plage générale très large

    def _calculate_semantic_quality(self, enhanced_data: Dict[str, Any]) -> float:
        """Calcule le score de qualité sémantique"""
        score = 0.0
        
        # Qualité du nom d'indicateur
        if enhanced_data.get('enhanced_indicator_name', '').count(' ') >= 1:
            score += 0.3
        
        # Présence de métadonnées temporelles
        if enhanced_data.get('temporal_metadata', {}).get('reference_date'):
            score += 0.2
        
        # Source institutionnelle identifiée
        if enhanced_data.get('institutional_source'):
            score += 0.2
        
        # Contexte économique riche
        context = enhanced_data.get('context_text', '')
        if len(context) > 50 and any(term in context.lower() for term in ['taux', 'économique', 'statistique', 'gdp', 'tunisia']):
            score += 0.3
        
        return min(score, 1.0)

    def _analyze_data_coherence(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse la cohérence des données extraites"""
        coherence = {
            'temporal_consistency': True,
            'value_ranges_realistic': True,
            'indicator_coverage': {},
            'data_quality_score': 0.0
        }
        
        try:
            # Analyser la cohérence temporelle
            years = [v.get('temporal_metadata', {}).get('year') for v in values.values()]
            years = [y for y in years if y]
            if years:
                coherence['temporal_consistency'] = max(years) - min(years) <= 5
            
            # Analyser la couverture des indicateurs
            categories = [v.get('category') for v in values.values()]
            coherence['indicator_coverage'] = {cat: categories.count(cat) for cat in set(categories) if cat}
            
            # Score de qualité global
            quality_scores = [v.get('semantic_quality', 0) for v in values.values()]
            coherence['data_quality_score'] = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
        except Exception as e:
            logger.debug(f"Error analyzing coherence: {e}")
            
        return coherence

    def _generate_data_summary(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un résumé intelligent des données"""
        summary = {
            'total_indicators': len(values),
            'validated_indicators': len([v for v in values.values() if v.get('validated')]),
            'categories_found': list(set(v.get('category') for v in values.values() if v.get('category'))),
            'time_periods_covered': list(set(str(v.get('temporal_metadata', {}).get('year')) for v in values.values() if v.get('temporal_metadata', {}).get('year'))),
            'sources_identified': list(set(v.get('institutional_source') for v in values.values() if v.get('institutional_source')))
        }
        
        return summary

    def _assess_data_quality(self, values: Dict[str, Any], coherence: Dict[str, Any]) -> Dict[str, Any]:
        """Évalue la qualité des données"""
        quality_scores = [v.get('overall_validation_score', 0) for v in values.values()]
        
        return {
            'average_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'high_quality_indicators': len([s for s in quality_scores if s > 0.8]),
            'temporal_coherence': coherence.get('temporal_consistency', False),
            'data_completeness': min(len(values) / 4, 1.0),  # Ratio par rapport à 4 indicateurs attendus
        }

    def _analyze_indicators(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les indicateurs trouvés"""
        by_category = {}
        for value_data in values.values():
            category = value_data.get('category', 'unknown')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append({
                'name': value_data.get('enhanced_indicator_name', ''),
                'value': value_data.get('value', 0),
                'unit': value_data.get('unit', ''),
                'quality': value_data.get('semantic_quality', 0)
            })
        
        return by_category

    def _analyze_temporal_patterns(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les patterns temporels"""
        temporal_data = []
        for value_data in values.values():
            temp_meta = value_data.get('temporal_metadata', {})
            if temp_meta.get('reference_date'):
                temporal_data.append(temp_meta)
        
        return {
            'periods_found': len(temporal_data),
            'most_recent': max([t.get('year', 0) for t in temporal_data]) if temporal_data else None,
            'period_types': list(set(t.get('period_type') for t in temporal_data if t.get('period_type')))
        }

    def _generate_recommendations(self, values: Dict[str, Any], coherence: Dict[str, Any]) -> List[str]:
        """Génère des recommandations intelligentes"""
        recommendations = []
        
        quality_score = coherence.get('data_quality_score', 0)
        if quality_score < 0.7:
            recommendations.append("Améliorer la qualité des données en validant avec des sources officielles supplémentaires")
        
        if len(values) < 3:
            recommendations.append("Rechercher des indicateurs économiques supplémentaires pour enrichir l'analyse")
        
        categories = set(v.get('category') for v in values.values() if v.get('category'))
        if len(categories) < 2:
            recommendations.append("Diversifier les catégories d'indicateurs économiques (monétaire, fiscal, commerce extérieur)")
        
        if not coherence.get('temporal_consistency'):
            recommendations.append("Vérifier la cohérence temporelle des données extraites")
            
        return recommendations

    def _calculate_enhanced_confidence(self, values: Dict[str, Any], coherence: Dict[str, Any]) -> float:
        """Calcule la confiance globale enrichie"""
        if not values:
            return 0.0
        
        # Confiance basée sur la validation sémantique
        validation_scores = [v.get('overall_validation_score', 0) for v in values.values()]
        avg_validation = sum(validation_scores) / len(validation_scores)
        
        # Bonus pour la cohérence des données
        coherence_bonus = 0.1 if coherence.get('temporal_consistency') else 0
        
        # Bonus pour la qualité sémantique
        quality_scores = [v.get('semantic_quality', 0) for v in values.values()]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Bonus pour le nombre d'indicateurs
        quantity_bonus = min(len(values) / 4 * 0.1, 0.1)
        
        return min(avg_validation * 0.5 + avg_quality * 0.3 + coherence_bonus + quantity_bonus, 1.0)

    def _assess_enhanced_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Évaluation améliorée de la conformité"""
        values = data.get('extracted_values', {})
        
        compliance = {
            'target_indicators_compliance': len([v for v in values.values() if v.get('is_target_indicator')]) > 0,
            'recognized_units_compliance': len([v for v in values.values() if v.get('unit')]) > 0,
            'temporal_compliance': len([v for v in values.values() if v.get('temporal_valid')]) > 0,
            'semantic_quality_compliance': sum([v.get('semantic_quality', 0) for v in values.values()]) / len(values) > 0.5 if values else False,
            'validation_compliance': len([v for v in values.values() if v.get('validated')]) / len(values) > 0.6 if values else False
        }
        
        compliance['overall_compliance_score'] = sum(compliance.values()) / len(compliance)
        
        return compliance

    # Méthodes utilitaires supplémentaires
    
    def _is_already_extracted(self, indicator_name: str, value: float, existing_values: Dict[str, Any]) -> bool:
        """Vérifie si un indicateur similaire a déjà été extrait"""
        for existing_data in existing_values.values():
            existing_name = existing_data.get('enhanced_indicator_name', existing_data.get('indicator_name', ''))
            existing_value = existing_data.get('value', 0)
            
            # Même nom d'indicateur ou valeur très proche
            if (indicator_name.lower() == existing_name.lower() or 
                abs(value - existing_value) < 0.01):
                return True
        return False

    def _categorize_intelligently(self, indicator_name: str, raw_indicator: str) -> str:
        """Catégorisation intelligente basée sur plusieurs critères"""
        combined_text = f"{indicator_name} {raw_indicator}".lower()
        
        # Catégorisation spécifique
        if 'pib' in combined_text or 'gdp' in combined_text:
            return 'comptes_nationaux'
        elif 'directeur' in combined_text or 'monétaire' in combined_text:
            return 'finance_et_monnaie'
        elif 'inflation' in combined_text or 'prix' in combined_text:
            return 'prix_et_inflation'
        elif 'commerce' in combined_text or 'export' in combined_text:
            return 'commerce_exterieur'
        elif 'chomage' in combined_text or 'emploi' in combined_text:
            return 'marche_du_travail'
        
        return 'comptes_nationaux'  # Par défaut

    def _is_coherent_new_indicator(self, indicator_name: str, value: float, unit: str, category: str) -> bool:
        """Vérifie la cohérence d'un nouvel indicateur"""
        try:
            # Validation de base
            if value <= 0 or not indicator_name:
                return False
            
            # Validation par catégorie
            if category == 'finance_et_monnaie':
                if unit == '%':
                    return 0.1 <= value <= 25  # Taux réalistes
                elif unit in ['MDT', 'millions']:
                    return 100 <= value <= 50000  # Montants réalistes
            elif category == 'prix_et_inflation':
                return 0.1 <= value <= 20 and unit == '%'  # Inflation réaliste
            elif category == 'comptes_nationaux':
                if 'pib' in indicator_name.lower() or 'gdp' in indicator_name.lower():
                    return 1000000000 <= value <= 1000000000000  # PIB en USD
            
            return True
            
        except Exception:
            return False

    def _validate_economic_coherence(self, value: float, indicator_name: str, context: str) -> Dict[str, Any]:
        """Validation approfondie de la cohérence économique"""
        coherence = {
            'is_economically_plausible': True,
            'value_range_check': 'passed',
            'context_consistency': True,
            'temporal_alignment': True
        }
        
        try:
            # Validation des plages par type d'indicateur
            indicator_lower = indicator_name.lower()
            
            if 'pib' in indicator_lower or 'gdp' in indicator_lower:
                coherence['is_economically_plausible'] = 1000000000 <= value <= 1000000000000
                coherence['value_range_check'] = 'gdp_range'
            elif 'taux' in indicator_lower and 'directeur' in indicator_lower:
                coherence['is_economically_plausible'] = 1 <= value <= 15
                coherence['value_range_check'] = 'central_bank_rate'
            elif 'inflation' in indicator_lower:
                coherence['is_economically_plausible'] = 0 <= value <= 25
                coherence['value_range_check'] = 'inflation_rate'
            elif 'compte' in indicator_lower and 'trésor' in indicator_lower:
                coherence['is_economically_plausible'] = abs(value) <= 10000
                coherence['value_range_check'] = 'treasury_account'
            
            # Validation contextuelle
            if any(year in context for year in ['2020', '2021', '2022', '2023', '2024', '2025']):
                coherence['temporal_alignment'] = True
            
        except Exception as e:
            logger.debug(f"Error validating economic coherence: {e}")
            coherence['is_economically_plausible'] = False
            
        return coherence

    def _get_unit_description(self, unit: str) -> str:
        """Retourne la description de l'unité"""
        unit_descriptions = {
            '%': 'Pourcentage',
            'USD': 'Dollars américains',
            'TND': 'Dinars tunisiens',
            'MDT': 'Millions de dinars tunisiens',
            'millions': 'Millions d\'unités',
            'milliards': 'Milliards d\'unités'
        }
        return unit_descriptions.get(unit, unit)

    def _parse_numeric_enhanced(self, value_str: str) -> Optional[float]:
        """Parse une valeur numérique avec gestion des formats variés"""
        try:
            # Nettoyer la chaîne
            cleaned = re.sub(r'[^\d,.-]', '', value_str.strip())
            
            # Remplacer virgule par point si nécessaire
            if ',' in cleaned and '.' not in cleaned:
                cleaned = cleaned.replace(',', '.')
            elif ',' in cleaned and '.' in cleaned:
                # Format européen: 1.234,56 -> 1234.56
                parts = cleaned.split(',')
                if len(parts) == 2:
                    cleaned = parts[0].replace('.', '') + '.' + parts[1]
            
            return float(cleaned)
        except (ValueError, AttributeError):
            return None