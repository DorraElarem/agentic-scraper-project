"""
ANALYZER AGENT CORRIGÉ - Analyse LLM fonctionnelle
Version finale avec appels LLM robustes et gestion d'erreurs
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import logging
from datetime import datetime
import json
import requests

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Résultat d'analyse simplifié et intelligent"""
    analysis_id: str
    data_source: str
    insights: Dict[str, Any]
    confidence_score: float
    timestamp: str
    processing_time: float
    
    # Nouvelles données intelligentes
    economic_category: str = "general"
    quality_score: float = 0.0
    auto_recommendations: list = None
    intelligence_metadata: Dict[str, Any] = None

class AnalyzerAgent:
    """Agent d'analyse avec LLM fonctionnel"""
    
    def __init__(self, agent_id: str = "smart_analyzer_001"):
        self.agent_id = agent_id
        
        # Configuration LLM sécurisée et fonctionnelle
        self.llm_config = self._initialize_llm_config()
        self.llm_available = self._test_llm_availability()
        
        # Patterns économiques tunisiens intelligents
        self.tunisian_economic_patterns = {
            'monetary_financial': {
                'keywords': ['bct', 'banque centrale', 'taux directeur', 'inflation', 'monétaire', 'crédit'],
                'indicators': ['taux', 'inflation', 'masse monétaire', 'réserves']
            },
            'statistical_demographic': {
                'keywords': ['ins', 'statistique', 'population', 'démographie', 'recensement', 'enquête'],
                'indicators': ['population', 'natalité', 'mortalité', 'migration']
            },
            'industrial_production': {
                'keywords': ['industrie', 'production', 'manufacturier', 'secteur', 'usine'],
                'indicators': ['production', 'capacité', 'exportation', 'emploi industriel']
            },
            'trade_commerce': {
                'keywords': ['commerce', 'export', 'import', 'échange', 'balance'],
                'indicators': ['exportations', 'importations', 'balance commerciale', 'partenaires']
            },
            'employment_social': {
                'keywords': ['emploi', 'chômage', 'travail', 'social', 'salaire'],
                'indicators': ['taux chômage', 'emploi', 'salaires', 'protection sociale']
            }
        }
        
        # Métriques de performance intelligentes
        self.analysis_performance = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'llm_successful_calls': 0,
            'llm_failed_calls': 0,
            'avg_confidence': 0.0,
            'avg_processing_time': 0.0
        }
        
        logger.info(f"AnalyzerAgent initialized: {self.agent_id} (LLM: {'Available' if self.llm_available else 'Unavailable'})")
        
    def _initialize_llm_config(self) -> Dict[str, Any]:
        """Initialise la configuration LLM de façon robuste"""
        try:
            import os
            return {
                'ollama_url': os.getenv('OLLAMA_HOST', 'http://ollama:11434'),
                'model': os.getenv('OLLAMA_MODEL', 'mistral:7b-instruct-v0.2-q4_0'),
                'timeout': int(os.getenv('OLLAMA_TIMEOUT', '180')),
                'connection_timeout': 30,
                'max_tokens': 400
            }
        except Exception as e:
            logger.error(f"LLM config initialization failed: {e}")
            return {}
    
    def _test_llm_availability(self) -> bool:
        """Test de disponibilité LLM avec timeout court"""
        if not self.llm_config:
            return False
            
        try:
            response = requests.get(
                f"{self.llm_config['ollama_url']}/api/tags",
                timeout=self.llm_config['connection_timeout']
            )
            available = response.status_code == 200
            logger.info(f"LLM availability test: {'✅ Available' if available else '❌ Unavailable'}")
            return available
        except Exception as e:
            logger.warning(f"LLM availability test failed: {e}")
            return False
    
    def analyze_scraped_data(self, data: Dict[str, Any]) -> AnalysisResult:
        """Analyse intelligente automatique des données scrapées"""
        start_time = datetime.now()
        analysis_id = f"smart_analysis_{int(start_time.timestamp())}"
        
        try:
            content = data.get("result", "") or data.get("content", "")
            source = data.get("source", "unknown")
            
            # 1️⃣ DÉTECTION AUTOMATIQUE DE CATÉGORIE
            economic_category = self._auto_detect_category(content, source)
            
            # 2️⃣ ANALYSE INTELLIGENTE SELON LA CATÉGORIE
            insights = self._perform_intelligent_analysis(content, economic_category)
            
            # 3️⃣ ENRICHISSEMENT AUTOMATIQUE
            enriched_insights = self._auto_enrich_analysis(insights, content, economic_category)
            
            # 4️⃣ SCORES AUTOMATIQUES
            confidence_score = self._calculate_smart_confidence(enriched_insights, content)
            quality_score = self._calculate_auto_quality(enriched_insights, content)
            
            # 5️⃣ RECOMMANDATIONS AUTOMATIQUES
            auto_recommendations = self._generate_smart_recommendations(enriched_insights, economic_category)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 6️⃣ MISE À JOUR DES MÉTRIQUES
            self._update_performance_metrics(True, confidence_score, processing_time)
            
            result = AnalysisResult(
                analysis_id=analysis_id,
                data_source=source,
                insights=enriched_insights,
                confidence_score=confidence_score,
                timestamp=datetime.now().isoformat(),
                processing_time=processing_time,
                economic_category=economic_category,
                quality_score=quality_score,
                auto_recommendations=auto_recommendations,
                intelligence_metadata={
                    'auto_category_detection': True,
                    'smart_enrichment_applied': True,
                    'analyzer_version': '2.0_fixed_llm',
                    'tunisian_context': True,
                    'llm_used': insights.get('llm_analysis_success', False)
                }
            )
            
            logger.info(f"✅ Smart analysis completed: {analysis_id} (category: {economic_category}, quality: {quality_score:.2f})")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(False, 0.0, processing_time)
            logger.error(f"❌ Smart analysis failed {self.agent_id}: {e}")
            
            return AnalysisResult(
                analysis_id=analysis_id,
                data_source=data.get("source", "unknown"),
                insights={"error": str(e), "error_type": "analysis_failure"},
                confidence_score=0.0,
                timestamp=datetime.now().isoformat(),
                processing_time=processing_time,
                economic_category="error",
                quality_score=0.0,
                auto_recommendations=["Erreur d'analyse - vérifier les données d'entrée"],
                intelligence_metadata={'error': True}
            )
    
    def _auto_detect_category(self, content: str, source: str) -> str:
        """Détection automatique intelligente de catégorie"""
        if not content:
            return "empty_content"
        
        content_lower = content.lower()
        source_lower = source.lower()
        
        # Scores par catégorie basés sur contenu + source
        category_scores = {}
        
        for category, pattern_data in self.tunisian_economic_patterns.items():
            score = 0
            
            # Score basé sur les mots-clés
            for keyword in pattern_data['keywords']:
                if keyword in content_lower:
                    score += 2
                if keyword in source_lower:
                    score += 3  # Source plus importante
            
            # Score basé sur les indicateurs
            for indicator in pattern_data['indicators']:
                if indicator in content_lower:
                    score += 1
            
            if score > 0:
                category_scores[category] = score
        
        # Retourner la catégorie avec le meilleur score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"Auto-detected category: {best_category} (score: {category_scores[best_category]})")
            return best_category
        
        return "general"
    
    def _perform_intelligent_analysis(self, content: str, category: str) -> Dict[str, Any]:
        """Analyse intelligente selon la catégorie détectée"""
        try:
            if self.llm_available and len(content) > 100:
                return self._llm_intelligent_analysis_fixed(content, category)
            else:
                return self._fallback_intelligent_analysis(content, category)
        except Exception as e:
            logger.warning(f"⚠️ Intelligent analysis failed, using fallback: {e}")
            return self._fallback_intelligent_analysis(content, category)
    
    def _llm_intelligent_analysis_fixed(self, content: str, category: str) -> Dict[str, Any]:
        """Analyse LLM CORRIGÉE avec appel direct fonctionnel"""
        try:
            if not self.llm_config:
                return self._fallback_intelligent_analysis(content, category)
            
            # Prompt spécialisé et optimisé
            prompt = self._create_optimized_prompt(content, category)
            
            # Appel LLM direct avec gestion d'erreur robuste
            llm_result = self._call_ollama_fixed(prompt)
            
            if llm_result and llm_result.get('success'):
                self.analysis_performance['llm_successful_calls'] += 1
                logger.info("LLM analysis successful")
                
                # Combiner résultat LLM avec analyse fallback
                fallback_result = self._fallback_intelligent_analysis(content, category)
                
                return {
                    **fallback_result,
                    'llm_analysis': llm_result['response'],
                    'llm_analysis_success': True,
                    'llm_execution_time': llm_result.get('execution_time', 0),
                    'analysis_method': 'llm_enhanced'
                }
            else:
                self.analysis_performance['llm_failed_calls'] += 1
                logger.warning(f"LLM analysis failed: {llm_result.get('error', 'Unknown error')}")
                fallback_result = self._fallback_intelligent_analysis(content, category)
                fallback_result['llm_analysis_success'] = False
                fallback_result['llm_error'] = llm_result.get('error', 'Unknown error')
                return fallback_result
                
        except Exception as e:
            self.analysis_performance['llm_failed_calls'] += 1
            logger.error(f"LLM analysis exception: {e}")
            fallback_result = self._fallback_intelligent_analysis(content, category)
            fallback_result['llm_analysis_success'] = False
            fallback_result['llm_error'] = str(e)
            return fallback_result
    
    def _create_optimized_prompt(self, content: str, category: str) -> str:
        """Crée un prompt optimisé pour l'économie tunisienne"""
        
        # Limiter le contenu pour éviter les timeouts
        truncated_content = content[:1500] if len(content) > 1500 else content
        
        category_prompts = {
            "monetary_financial": f"""Analysez ces données monétaires tunisiennes:
{truncated_content}

Répondez en JSON:
{{"indicateurs": ["taux directeur", "inflation"], "confiance": 0.8, "resume": "analyse monétaire"}}""",

            "statistical_demographic": f"""Analysez ces données démographiques tunisiennes:
{truncated_content}

Répondez en JSON:
{{"indicateurs": ["population", "emploi"], "confiance": 0.8, "resume": "analyse démographique"}}""",

            "trade_commerce": f"""Analysez ces données de commerce tunisien:
{truncated_content}

Répondez en JSON:
{{"indicateurs": ["exportations", "importations"], "confiance": 0.8, "resume": "analyse commerciale"}}""",

            "general": f"""Analysez ces données économiques tunisiennes:
{truncated_content}

Identifiez les indicateurs économiques valides et répondez en JSON:
{{"indicateurs": ["liste"], "confiance": 0.8, "resume": "brève analyse"}}"""
        }
        
        return category_prompts.get(category, category_prompts["general"])
    
    def _call_ollama_fixed(self, prompt: str) -> Dict[str, Any]:
        """Appel Ollama CORRIGÉ avec gestion d'erreurs complète"""
        
        start_time = datetime.now()
        
        try:
            payload = {
                "model": self.llm_config['model'],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": self.llm_config['max_tokens'],
                    "num_ctx": 2048,
                    "stop": ["###", "---"],
                    "repeat_penalty": 1.05
                }
            }
            
            response = requests.post(
                f"{self.llm_config['ollama_url']}/api/generate",
                json=payload,
                timeout=self.llm_config['timeout'],
                headers={'Content-Type': 'application/json'}
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '').strip()
                
                if analysis_text:
                    parsed_response = self._parse_llm_response(analysis_text)
                    
                    return {
                        "success": True,
                        "response": parsed_response,
                        "execution_time": execution_time,
                        "raw_response": analysis_text[:200]  # Premiers 200 chars pour debug
                    }
                else:
                    return {
                        "success": False,
                        "error": "Empty response from LLM",
                        "execution_time": execution_time
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "execution_time": execution_time
                }
                
        except requests.exceptions.Timeout:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "error": f"Timeout after {self.llm_config['timeout']}s",
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parser robuste de la réponse LLM"""
        try:
            # Nettoyer la réponse
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Chercher JSON dans le texte
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            
            return json.loads(response)
            
        except json.JSONDecodeError:
            logger.warning(f"LLM response not valid JSON: {response[:100]}...")
            return {
                "raw_response": response[:300],
                "parsing_error": True,
                "fallback_analysis": "Réponse LLM reçue mais non structurée"
            }
        except Exception as e:
            logger.warning(f"LLM response parsing error: {e}")
            return {
                "parsing_error": True,
                "error": str(e)
            }
    
    def _fallback_intelligent_analysis(self, content: str, category: str) -> Dict[str, Any]:
        """Analyse de fallback intelligente sans LLM"""
        import re
        
        analysis = {
            "analysis_method": "intelligent_fallback",
            "category": category,
            "content_stats": {
                "length": len(content),
                "word_count": len(content.split())
            }
        }
        
        # Extraction intelligente selon la catégorie
        if category in self.tunisian_economic_patterns:
            pattern_data = self.tunisian_economic_patterns[category]
            
            # Recherche des indicateurs spécialisés
            found_indicators = []
            for indicator in pattern_data['indicators']:
                if indicator.lower() in content.lower():
                    found_indicators.append(indicator)
            
            analysis["indicateurs_detectes"] = found_indicators
            
            # Recherche de valeurs numériques
            numbers = re.findall(r'\d+[.,]?\d*', content)
            percentages = re.findall(r'\d+[.,]?\d*\s*%', content)
            
            analysis["donnees_numeriques"] = {
                "nombres_detectes": len(numbers),
                "pourcentages": len(percentages),
                "echantillon_nombres": numbers[:5] if numbers else []
            }
            
            # Analyse contextuelle simple
            analysis["contexte_tunisien"] = {
                "mots_cles_tunisiens": self._extract_tunisian_keywords(content),
                "niveau_detail": "riche" if len(content) > 2000 else "moyen" if len(content) > 500 else "basique"
            }
        
        return analysis
    
    def _extract_tunisian_keywords(self, content: str) -> list:
        """Extraction de mots-clés spécifiques à la Tunisie"""
        tunisian_keywords = [
            'tunisie', 'tunisien', 'bct', 'ins', 'dinar', 'gouvernorat',
            'république tunisienne', 'tunis', 'sfax', 'sousse'
        ]
        
        content_lower = content.lower()
        found_keywords = [kw for kw in tunisian_keywords if kw in content_lower]
        return found_keywords[:10]  # Limiter à 10
    
    def _auto_enrich_analysis(self, base_insights: Dict[str, Any], 
                             content: str, category: str) -> Dict[str, Any]:
        """Enrichissement automatique intelligent"""
        enriched = base_insights.copy()
        
        # Enrichissement contextuel automatique
        enriched.update({
            'auto_enrichment': {
                'content_analysis': {
                    'tunisian_context_detected': self._detect_tunisian_context(content),
                    'data_density': self._calculate_data_density(content),
                    'temporal_references': self._extract_temporal_info(content),
                    'credibility_indicators': self._assess_source_credibility(content)
                },
                'category_insights': {
                    'specialization_level': self._assess_specialization(content, category),
                    'institutional_references': self._find_institutional_refs(content),
                    'methodology_indicators': self._detect_methodology(content)
                },
                'intelligence_metadata': {
                    'enrichment_timestamp': datetime.now().isoformat(),
                    'enrichment_version': '2.0_fixed_llm',
                    'tunisian_optimization': True
                }
            }
        })
        
        return enriched
    
    def _detect_tunisian_context(self, content: str) -> Dict[str, Any]:
        """Détection du contexte tunisien"""
        content_lower = content.lower()
        
        institutional_refs = sum(1 for inst in ['bct', 'ins', 'ministère', 'gouvernement'] if inst in content_lower)
        geographic_refs = sum(1 for geo in ['tunisie', 'tunis', 'sfax', 'sousse', 'gouvernorat'] if geo in content_lower)
        economic_refs = sum(1 for eco in ['dinar', 'économie tunisienne', 'pib tunisien'] if eco in content_lower)
        
        return {
            'institutional_density': institutional_refs,
            'geographic_density': geographic_refs,
            'economic_context_density': economic_refs,
            'overall_tunisian_score': (institutional_refs + geographic_refs + economic_refs) / 3
        }
    
    def _calculate_data_density(self, content: str) -> float:
        """Calcule la densité de données"""
        if not content:
            return 0.0
        
        import re
        
        total_words = len(content.split())
        numbers = len(re.findall(r'\d+', content))
        tables_indicators = content.lower().count('tableau') + content.lower().count('table')
        
        density = (numbers + tables_indicators * 5) / max(total_words, 1)
        return min(density, 1.0)
    
    def _extract_temporal_info(self, content: str) -> Dict[str, Any]:
        """Extraction d'informations temporelles"""
        import re
        
        years = re.findall(r'\b(20[0-2][0-9])\b', content)
        months = re.findall(r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b', content.lower())
        
        return {
            'years_mentioned': list(set(years))[:5],
            'months_mentioned': list(set(months))[:3],
            'temporal_coverage': len(set(years)),
            'recent_data': any(int(year) >= 2020 for year in years) if years else False
        }
    
    def _assess_source_credibility(self, content: str) -> str:
        """Évaluation de la crédibilité de la source"""
        content_lower = content.lower()
        
        credibility_indicators = 0
        
        # Indicateurs institutionnels
        if any(term in content_lower for term in ['officiel', 'ministère', 'banque centrale', 'ins']):
            credibility_indicators += 2
        
        # Méthodologie
        if any(term in content_lower for term in ['méthodologie', 'enquête', 'recensement', 'étude']):
            credibility_indicators += 1
        
        # Références
        if any(term in content_lower for term in ['source', 'référence', 'données']):
            credibility_indicators += 1
        
        if credibility_indicators >= 3:
            return "high"
        elif credibility_indicators >= 2:
            return "medium"
        else:
            return "low"
    
    def _assess_specialization(self, content: str, category: str) -> str:
        """Évalue le niveau de spécialisation"""
        if category == "general":
            return "basic"
        
        content_lower = content.lower()
        
        if category in self.tunisian_economic_patterns:
            specialized_terms = self.tunisian_economic_patterns[category]['indicators']
            found_terms = sum(1 for term in specialized_terms if term.lower() in content_lower)
            
            if found_terms >= 3:
                return "expert"
            elif found_terms >= 2:
                return "intermediate"
            else:
                return "basic"
        
        return "basic"
    
    def _find_institutional_refs(self, content: str) -> list:
        """Trouve les références institutionnelles"""
        institutions = [
            'BCT', 'Banque Centrale de Tunisie', 'INS', 'Institut National de Statistique',
            'Ministère des Finances', 'Ministère de l\'Économie', 'Gouvernement tunisien'
        ]
        
        found_institutions = []
        content_lower = content.lower()
        
        for institution in institutions:
            if institution.lower() in content_lower:
                found_institutions.append(institution)
        
        return found_institutions[:5]  # Limiter à 5
    
    def _detect_methodology(self, content: str) -> bool:
        """Détecte les indicateurs de méthodologie"""
        methodology_terms = [
            'méthodologie', 'enquête', 'échantillon', 'sondage', 'recensement',
            'collecte', 'traitement', 'analyse statistique'
        ]
        
        content_lower = content.lower()
        return any(term in content_lower for term in methodology_terms)
    
    def _calculate_smart_confidence(self, insights: Dict[str, Any], content: str) -> float:
        """Calcul intelligent de confiance"""
        if "error" in insights:
            return 0.0
        
        confidence_factors = []
        
        # Facteur de richesse des insights
        if len(insights) > 3:
            confidence_factors.append(0.3)
        
        # Facteur de contenu tunisien
        if 'auto_enrichment' in insights:
            tunisian_score = insights['auto_enrichment']['content_analysis'].get('tunisian_context_detected', {}).get('overall_tunisian_score', 0)
            confidence_factors.append(tunisian_score * 0.2)
        
        # Facteur de données numériques
        if any(char.isdigit() for char in content):
            confidence_factors.append(0.2)
        
        # Facteur LLM
        if insights.get('llm_analysis_success'):
            confidence_factors.append(0.3)
        else:
            confidence_factors.append(0.1)
        
        return min(sum(confidence_factors), 1.0)
    
    def _calculate_auto_quality(self, insights: Dict[str, Any], content: str) -> float:
        """Calcul automatique de qualité"""
        try:
            quality_factors = []
            
            # Facteur de richesse du contenu
            content_length = len(content) if content else 0
            if content_length > 2000:
                quality_factors.append(1.0)
            elif content_length > 500:
                quality_factors.append(0.7)
            else:
                quality_factors.append(0.3)
            
            # Facteur d'enrichissement
            if 'auto_enrichment' in insights:
                enrichment_data = insights['auto_enrichment']
                data_density = enrichment_data.get('content_analysis', {}).get('data_density', 0)
                quality_factors.append(data_density)
                
                # Crédibilité
                credibility = enrichment_data.get('content_analysis', {}).get('credibility_indicators', 'low')
                if credibility == 'high':
                    quality_factors.append(1.0)
                elif credibility == 'medium':
                    quality_factors.append(0.6)
                else:
                    quality_factors.append(0.2)
            
            # Facteur de spécialisation
            if 'indicateurs_detectes' in insights and insights['indicateurs_detectes']:
                quality_factors.append(0.8)
            
            # Facteur LLM
            if insights.get('llm_analysis_success'):
                quality_factors.append(0.9)
            
            return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
            
        except Exception as e:
            logger.warning(f"Quality calculation failed: {e}")
            return 0.5
    
    def _generate_smart_recommendations(self, insights: Dict[str, Any], category: str) -> List[str]:
        """Génération automatique de recommandations intelligentes"""
        recommendations = []
        
        try:
            # Recommandations basées sur la catégorie
            category_recommendations = {
                'monetary_financial': [
                    "Analyser l'impact des décisions BCT sur l'économie réelle",
                    "Suivre l'évolution des taux d'intérêt et de l'inflation",
                    "Évaluer les effets sur le secteur bancaire"
                ],
                'statistical_demographic': [
                    "Croiser avec données INS pour validation",
                    "Analyser les tendances démographiques à long terme",
                    "Évaluer l'impact sur les politiques sociales"
                ],
                'industrial_production': [
                    "Analyser la compétitivité sectorielle",
                    "Évaluer les opportunités d'exportation",
                    "Suivre les investissements industriels"
                ],
                'trade_commerce': [
                    "Analyser la balance commerciale",
                    "Identifier les partenaires stratégiques",
                    "Évaluer la compétitivité des exportations"
                ],
                'employment_social': [
                    "Analyser les politiques d'emploi",
                    "Évaluer l'adéquation formation-emploi",
                    "Suivre l'évolution du marché du travail"
                ]
            }
            
            if category in category_recommendations:
                recommendations.extend(category_recommendations[category][:2])
            
            # Recommandations basées sur la qualité
            if 'auto_enrichment' in insights:
                enrichment = insights['auto_enrichment']
                
                credibility = enrichment.get('content_analysis', {}).get('credibility_indicators', 'low')
                if credibility == 'low':
                    recommendations.append("Rechercher des sources officielles complémentaires")
                elif credibility == 'high':
                    recommendations.append("Données fiables - utiliser pour analyse approfondie")
                
                # Recommandations temporelles
                temporal_info = enrichment.get('content_analysis', {}).get('temporal_references', {})
                if not temporal_info.get('recent_data', False):
                    recommendations.append("Rechercher des données plus récentes")
                
                # Recommandations de spécialisation
                specialization = enrichment.get('category_insights', {}).get('specialization_level', 'basic')
                if specialization == 'basic':
                    recommendations.append("Approfondir avec des sources spécialisées")
            
            # Recommandations LLM
            if insights.get('llm_analysis_success'):
                recommendations.append("Analyse LLM réussie - données enrichies disponibles")
            elif insights.get('llm_error'):
                recommendations.append("Analyse LLM échouée - validation manuelle recommandée")
            
            # Recommandations générales
            if len(recommendations) < 2:
                recommendations.extend([
                    "Valider avec des sources officielles tunisiennes",
                    "Analyser dans le contexte économique tunisien"
                ])
            
            return recommendations[:4]  # Limiter à 4 recommandations
            
        except Exception as e:
            logger.warning(f"Recommendations generation failed: {e}")
            return ["Analyse effectuée - recommandations indisponibles"]
    
    def _update_performance_metrics(self, success: bool, confidence: float, processing_time: float):
        """Mise à jour des métriques de performance"""
        try:
            self.analysis_performance['total_analyses'] += 1
            
            if success:
                self.analysis_performance['successful_analyses'] += 1
                
                # Mise à jour moyenne mobile de confiance
                total = self.analysis_performance['total_analyses']
                current_avg = self.analysis_performance['avg_confidence']
                self.analysis_performance['avg_confidence'] = (
                    (current_avg * (total - 1)) + confidence
                ) / total
            
            # Mise à jour temps moyen
            total = self.analysis_performance['total_analyses']
            current_avg_time = self.analysis_performance['avg_processing_time']
            self.analysis_performance['avg_processing_time'] = (
                (current_avg_time * (total - 1)) + processing_time
            ) / total
            
        except Exception as e:
            logger.warning(f"Performance metrics update failed: {e}")
    
    # MÉTHODES DE STATUT ET PERFORMANCE
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Statut de l'agent analyzer intelligent"""
        success_rate = 0
        llm_success_rate = 0
        
        if self.analysis_performance['total_analyses'] > 0:
            success_rate = self.analysis_performance['successful_analyses'] / self.analysis_performance['total_analyses']
        
        total_llm_calls = self.analysis_performance['llm_successful_calls'] + self.analysis_performance['llm_failed_calls']
        if total_llm_calls > 0:
            llm_success_rate = self.analysis_performance['llm_successful_calls'] / total_llm_calls
        
        return {
            "agent_id": self.agent_id,
            "agent_type": "SmartAnalyzerAgent",
            "version": "2.0_fixed_llm",
            "llm_available": self.llm_available,
            "llm_config": self.llm_config,
            "performance_metrics": {
                **self.analysis_performance,
                "success_rate": success_rate,
                "llm_success_rate": llm_success_rate
            },
            "tunisian_patterns": list(self.tunisian_economic_patterns.keys()),
            "capabilities": [
                "automatic_category_detection",
                "intelligent_tunisian_analysis",
                "smart_enrichment",
                "auto_quality_scoring",
                "intelligent_recommendations",
                "fixed_llm_analysis",
                "robust_fallback_analysis",
                "performance_tracking"
            ],
            "intelligence_features": {
                "auto_category_detection": True,
                "tunisian_context_optimization": True,
                "smart_fallback": True,
                "performance_learning": True,
                "llm_integration": self.llm_available
            }
        }
    
    def test_llm_functionality(self) -> Dict[str, Any]:
        """Test de fonctionnalité LLM"""
        if not self.llm_available:
            return {
                "status": "unavailable",
                "message": "LLM service not available",
                "llm_config": self.llm_config
            }
        
        test_prompt = "Analyser: PIB Tunisie 2024. Répondre en JSON: {\"indicateurs\": [\"pib\"], \"confiance\": 0.8}"
        
        result = self._call_ollama_fixed(test_prompt)
        
        return {
            "status": "success" if result.get('success') else "failed",
            "execution_time": result.get('execution_time', 0),
            "error": result.get('error') if not result.get('success') else None,
            "response_preview": str(result.get('response', {}))[:200],
            "llm_config": self.llm_config,
            "test_timestamp": datetime.now().isoformat()
        }
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Analytiques de performance détaillées"""
        if self.analysis_performance['total_analyses'] == 0:
            return {'message': 'No analyses performed yet'}
        
        try:
            stats = self.analysis_performance
            success_rate = stats['successful_analyses'] / stats['total_analyses']
            
            total_llm_calls = stats['llm_successful_calls'] + stats['llm_failed_calls']
            llm_success_rate = stats['llm_successful_calls'] / max(total_llm_calls, 1)
            
            return {
                'summary': {
                    'total_analyses': stats['total_analyses'],
                    'success_rate': success_rate,
                    'average_confidence': stats['avg_confidence'],
                    'average_processing_time': stats['avg_processing_time'],
                    'llm_success_rate': llm_success_rate,
                    'llm_total_calls': total_llm_calls
                },
                'performance_level': (
                    'excellent' if success_rate > 0.9 and stats['avg_confidence'] > 0.8 
                    else 'good' if success_rate > 0.7 and stats['avg_confidence'] > 0.6 
                    else 'needs_improvement'
                ),
                'llm_performance': (
                    'excellent' if llm_success_rate > 0.8
                    else 'good' if llm_success_rate > 0.6
                    else 'poor' if llm_success_rate > 0.3
                    else 'failing'
                ),
                'intelligence_status': 'fully_automatic_with_fixed_llm',
                'tunisian_optimization': True,
                'recommendations': self._generate_performance_recommendations(success_rate, stats['avg_confidence'], llm_success_rate)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate performance analytics: {e}")
            return {'error': str(e)}
    
    def _generate_performance_recommendations(self, success_rate: float, avg_confidence: float, llm_success_rate: float) -> List[str]:
        """Recommandations basées sur la performance"""
        recommendations = []
        
        if success_rate > 0.9 and avg_confidence > 0.8:
            recommendations.append("Performance excellente - système optimisé")
        elif success_rate > 0.7:
            recommendations.append("Bonne performance - quelques améliorations possibles")
        else:
            recommendations.append("Performance à améliorer - réviser les sources")
        
        if avg_confidence < 0.5:
            recommendations.append("Confiance faible - enrichir les données d'entrée")
        
        if self.analysis_performance['avg_processing_time'] > 10:
            recommendations.append("Temps de traitement élevé - optimiser les requêtes LLM")
        
        # Recommandations LLM spécifiques
        if llm_success_rate < 0.3:
            recommendations.append("LLM défaillant - vérifier la connectivité Ollama")
        elif llm_success_rate < 0.6:
            recommendations.append("LLM instable - optimiser les timeouts")
        elif llm_success_rate > 0.8:
            recommendations.append("LLM performant - analyses enrichies disponibles")
        
        return recommendations
    
    def reset_performance_metrics(self):
        """Reset des métriques de performance"""
        self.analysis_performance = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'llm_successful_calls': 0,
            'llm_failed_calls': 0,
            'avg_confidence': 0.0,
            'avg_processing_time': 0.0
        }
        logger.info(f"Performance metrics reset for {self.agent_id}")
    
    def export_intelligence_data(self) -> Dict[str, Any]:
        """Export des données d'intelligence"""
        return {
            'agent_id': self.agent_id,
            'agent_type': 'SmartAnalyzerAgent',
            'version': '2.0_fixed_llm',
            'tunisian_economic_patterns': self.tunisian_economic_patterns,
            'performance_metrics': self.analysis_performance,
            'llm_available': self.llm_available,
            'llm_config': self.llm_config,
            'export_timestamp': datetime.now().isoformat()
        }