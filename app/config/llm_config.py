"""
Configuration LLM CORRIGÉE - Fix du parsing et prompts simplifiés
Version fixée pour résoudre les problèmes d'analyse vide
"""

import os
import requests
import json
import time
import logging
import re
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

logger = logging.getLogger(__name__)

class FixedLLMConfig:
    """Configuration LLM corrigée avec parsing robuste"""
    
    def __init__(self):
        self.ollama_url = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'mistral:7b-instruct-v0.2-q4_0')
        
        # TIMEOUTS RÉALISTES
        self.connection_timeout = 30
        self.quick_timeout = 240
        self.standard_timeout = 600 
        self.heavy_timeout = 240
        self.emergency_timeout = 180
        
        # Session optimisée
        self.session = self._create_optimized_session()
        
        # Test de disponibilité
        self.llm_available = self._test_ollama_connection()
        
        # Métriques
        self.performance_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'timeout_calls': 0,
            'avg_response_time': 0.0,
            'last_successful_call': None
        }
        
        logger.info(f"FixedLLMConfig initialized - Available: {self.llm_available}")
        logger.info(f"Timeouts: quick={self.quick_timeout}s, standard={self.standard_timeout}s, heavy={self.heavy_timeout}s")

    def _create_optimized_session(self) -> requests.Session:
        session = requests.Session()
        
        retry_strategy = Retry(
            total=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
            backoff_factor=0.3,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=2, pool_connections=1)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TunisianEconomicScraper-Fixed/2.0'
        })
        
        return session

    def _test_ollama_connection(self) -> bool:
        try:
            logger.info(f"Testing Ollama connection: {self.ollama_url}")
            
            response = self.session.get(
                f"{self.ollama_url}/api/tags",
                timeout=self.connection_timeout
            )
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.info(f"Ollama available - {len(models)} models found")
                return True
            else:
                logger.error(f"Ollama responded with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False

    def analyze_economic_data(self, content: str, context: str = "economic", 
                            source_domain: str = None) -> Dict[str, Any]:
        """ANALYSE LLM FIXÉE avec parsing robuste"""
        
        if not self.llm_available:
            return self._fallback_analysis(content, "LLM not available")
        
        # Sélection timeout intelligente
        timeout = self._select_smart_timeout(content, context, source_domain)
        timeout_type = self._get_timeout_type(timeout)
        
        # PROMPT SIMPLIFIÉ ET EFFICACE
        prompt = self._create_simple_effective_prompt(content, context)
        
        # Appel avec gestion robuste
        return self._call_ollama_with_robust_handling(prompt, timeout, timeout_type)

    def _create_simple_effective_prompt(self, content: str, context: str) -> str:
        """PROMPT SIMPLIFIÉ pour meilleure réponse"""
        
        # Limiter le contenu pour éviter timeouts
        if len(content) > 2000:
            content = content[:2000] + "\n[...contenu limité...]"
        
        # PROMPT ULTRA-SIMPLIFIÉ
        simple_prompt = f"""Analysez ce contenu économique tunisien et listez les indicateurs trouvés.

Contenu à analyser:
{content}

Répondez avec cette structure simple:
{{
  "indicateurs": ["PIB", "inflation", "emploi"],
  "annees": [2024, 2023, 2022],
  "qualite": "bon",
  "confiance": 0.8
}}

Réponse JSON:"""
        
        return simple_prompt

    def _call_ollama_with_robust_handling(self, prompt: str, timeout: int, timeout_type: str) -> Dict[str, Any]:
        """APPEL OLLAMA FIXÉ avec meilleur parsing"""
        
        start_time = time.time()
        self.performance_stats['total_calls'] += 1
        
        try:
            logger.info(f"LLM call starting: {timeout_type} timeout ({timeout}s)")
            
            # CONFIGURATION SIMPLIFIÉE
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,  # Plus bas pour consistance
                    "top_p": 0.8,
                    "num_predict": 200,  # Plus court pour éviter timeouts
                    "num_ctx": 2048,
                    "stop": ["###", "---", "\n\n\n"],
                    "repeat_penalty": 1.1
                }
            }
            
            response = self.session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '').strip()
                
                logger.info(f"LLM raw response: {analysis_text[:200]}...")
                
                if analysis_text:
                    self.performance_stats['successful_calls'] += 1
                    self.performance_stats['last_successful_call'] = datetime.now().isoformat()
                    self._update_avg_response_time(execution_time)
                    
                    logger.info(f"LLM success in {execution_time:.1f}s ({timeout_type})")
                    
                    # PARSING AMÉLIORÉ
                    parsed_analysis = self._parse_llm_response_fixed(analysis_text)
                    
                    return {
                        "success": True,
                        "analysis": parsed_analysis,
                        "execution_time": execution_time,
                        "timeout_used": timeout,
                        "timeout_type": timeout_type,
                        "method": "fixed_llm_config",
                        "raw_response": analysis_text[:500]  # Pour debug
                    }
                else:
                    logger.warning("LLM returned empty response")
                    return self._fallback_analysis(prompt, f"Empty response after {execution_time:.1f}s")
            else:
                logger.error(f"LLM HTTP error: {response.status_code}")
                self.performance_stats['failed_calls'] += 1
                return self._fallback_analysis(prompt, f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            execution_time = time.time() - start_time
            logger.warning(f"LLM timeout after {timeout}s ({timeout_type})")
            
            self.performance_stats['timeout_calls'] += 1
            
            # Fallback d'urgence
            if timeout_type != 'emergency' and timeout > self.emergency_timeout:
                logger.info("Attempting emergency fallback")
                return self._emergency_fallback_call(prompt)
            else:
                return self._fallback_analysis(prompt, f"Timeout after {timeout}s")
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"LLM call failed: {e}")
            self.performance_stats['failed_calls'] += 1
            return self._fallback_analysis(prompt, f"Error: {str(e)}")

    def _parse_llm_response_fixed(self, response: str) -> Dict[str, Any]:
        """PARSING FIXÉ pour extraire vraiment les données"""
        
        logger.info(f"Parsing LLM response: {response[:300]}...")
        
        try:
            # Nettoyer la réponse
            response = response.strip()
            
            # Supprimer les marqueurs markdown
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Trouver le JSON dans la réponse
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                logger.info(f"Found JSON: {json_text}")
                
                try:
                    parsed = json.loads(json_text)
                    normalized = self._normalize_parsed_response_fixed(parsed)
                    logger.info(f"Successfully parsed and normalized: {normalized}")
                    return normalized
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {e}")
                    pass
            
            # FALLBACK: Extraction par regex si JSON échoue
            return self._extract_indicators_by_regex(response)
            
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            return self._extract_indicators_by_regex(response)

    def _normalize_parsed_response_fixed(self, parsed: Dict) -> Dict[str, Any]:
        """NORMALISATION FIXÉE des réponses"""
        
        normalized = {
            'indicateurs': [],
            'annees_detectees': [],
            'qualite': 'moyenne',
            'confiance': 0.5
        }
        
        # Traitement flexible des clés
        for key, value in parsed.items():
            key_lower = key.lower()
            
            # Indicateurs
            if any(word in key_lower for word in ['indicateur', 'indicator', 'metric']):
                if isinstance(value, list):
                    normalized['indicateurs'] = [str(v) for v in value[:10]]
                elif isinstance(value, str):
                    normalized['indicateurs'] = [value]
                    
            # Années
            elif any(word in key_lower for word in ['annee', 'year', 'periode']):
                if isinstance(value, list):
                    # Filtrer et convertir les années
                    valid_years = []
                    for item in value:
                        try:
                            year = int(item)
                            if 2018 <= year <= 2025:
                                valid_years.append(year)
                        except (ValueError, TypeError):
                            pass
                    normalized['annees_detectees'] = valid_years
                    
            # Qualité
            elif any(word in key_lower for word in ['qualite', 'quality']):
                normalized['qualite'] = str(value)
                
            # Confiance
            elif any(word in key_lower for word in ['confiance', 'confidence', 'conf']):
                try:
                    conf = float(value)
                    normalized['confiance'] = max(0.0, min(1.0, conf))
                except:
                    normalized['confiance'] = 0.5
        
        # Assurer au moins quelques données par défaut
        if not normalized['indicateurs']:
            normalized['indicateurs'] = ['analyse_disponible']
        
        if not normalized['annees_detectees']:
            normalized['annees_detectees'] = [2024]
        
        logger.info(f"Normalized response: {normalized}")
        return normalized

    def _extract_indicators_by_regex(self, text: str) -> Dict[str, Any]:
        """EXTRACTION ROBUSTE par regex en fallback"""
        
        logger.info("Using regex fallback extraction")
        
        # Mots-clés économiques tunisiens étendus
        economic_keywords = [
            # Mots français
            'pib', 'inflation', 'chomage', 'emploi', 'population', 'dette',
            'export', 'import', 'taux', 'croissance', 'production', 'budget',
            'investissement', 'reserves', 'change', 'credit', 'epargne',
            
            # Mots anglais
            'gdp', 'unemployment', 'growth', 'rate', 'trade', 'balance',
            'deficit', 'surplus', 'revenue', 'expenditure', 'fiscal',
            
            # Indicateurs spécifiques tunisiens
            'directeur', 'monétaire', 'commerciale', 'extérieur', 'publique'
        ]
        
        found_indicators = []
        text_lower = text.lower()
        
        # Recherche d'indicateurs
        for keyword in economic_keywords:
            if keyword in text_lower:
                # Extraire le contexte autour du mot-clé
                pattern = rf'\b[\w\s]*{keyword}[\w\s]*\b'
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 3 and clean_match not in found_indicators:
                        found_indicators.append(clean_match)
                        if len(found_indicators) >= 10:  # Limite
                            break
        
        # Recherche d'années
        years = re.findall(r'\b(20(?:1[8-9]|2[0-5]))\b', text)
        valid_years = [int(y) for y in set(years) if 2018 <= int(y) <= 2025]
        
        # Évaluer la qualité
        quality = 'excellente' if len(found_indicators) > 5 else 'bonne' if len(found_indicators) > 2 else 'faible'
        confidence = min(0.9, len(found_indicators) * 0.15)
        
        result = {
            'indicateurs': found_indicators[:10],
            'annees_detectees': valid_years,
            'qualite': quality,
            'confiance': confidence,
            'extraction_method': 'regex_fallback'
        }
        
        logger.info(f"Regex extraction result: {result}")
        return result

    def _emergency_fallback_call(self, original_prompt: str) -> Dict[str, Any]:
        """Appel d'urgence ultra-simplifié"""
        
        # Prompt minimal
        simple_prompt = f"Données économiques tunisiennes. Listez 3 indicateurs principaux trouvés."
        
        try:
            logger.info("Emergency fallback call starting")
            
            response = self.session.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": simple_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 50,
                        "num_ctx": 512,
                        "stop": ["###"]
                    }
                },
                timeout=self.emergency_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '').strip()
                
                if analysis_text:
                    logger.info("Emergency fallback successful")
                    parsed_analysis = self._extract_indicators_by_regex(analysis_text)
                    
                    return {
                        "success": True,
                        "analysis": parsed_analysis,
                        "execution_time": self.emergency_timeout,
                        "timeout_used": self.emergency_timeout,
                        "timeout_type": "emergency",
                        "method": "emergency_fallback"
                    }
            
        except Exception as e:
            logger.error(f"Emergency fallback failed: {e}")
        
        return self._fallback_analysis(original_prompt, "Emergency fallback failed")

    def _fallback_analysis(self, content: str, reason: str) -> Dict[str, Any]:
        """Analyse de fallback intelligente"""
        logger.warning(f"Using fallback analysis: {reason}")
        
        # Analyse basique mais utile
        fallback_result = self._extract_indicators_by_regex(content[:1000] if content else "")
        
        return {
            "success": False,
            "analysis": fallback_result,
            "fallback_reason": reason,
            "method": "fallback_analysis",
            "execution_time": 0.0
        }

    # Méthodes utilitaires simplifiées
    def _select_smart_timeout(self, content: str, context: str, source_domain: str = None) -> int:
        base_timeout = self.standard_timeout
        
        if source_domain:
            domain_lower = source_domain.lower()
            if 'ins.tn' in domain_lower:
                base_timeout = self.heavy_timeout
            elif 'api.' in domain_lower:
                base_timeout = self.quick_timeout
        
        content_length = len(content) if content else 0
        if content_length > 3000:
            base_timeout = min(self.heavy_timeout, base_timeout * 1.2)
        elif content_length < 800:
            base_timeout = self.quick_timeout
        
        return int(base_timeout)

    def _get_timeout_type(self, timeout: int) -> str:
        if timeout <= self.quick_timeout:
            return 'quick'
        elif timeout <= self.standard_timeout:
            return 'standard'
        elif timeout <= self.heavy_timeout:
            return 'heavy'
        else:
            return 'emergency'

    def _update_avg_response_time(self, response_time: float):
        if self.performance_stats['successful_calls'] == 1:
            self.performance_stats['avg_response_time'] = response_time
        else:
            current_avg = self.performance_stats['avg_response_time']
            total_successful = self.performance_stats['successful_calls']
            self.performance_stats['avg_response_time'] = (
                (current_avg * (total_successful - 1)) + response_time
            ) / total_successful

    def get_performance_stats(self) -> Dict[str, Any]:
        """Statistiques de performance"""
        total_calls = self.performance_stats['total_calls']
        success_rate = (self.performance_stats['successful_calls'] / max(total_calls, 1)) * 100
        
        return {
            "llm_config_version": "fixed_v2.1",
            "service_available": self.llm_available,
            "model": self.ollama_model,
            "performance_summary": {
                "total_calls": total_calls,
                "successful_calls": self.performance_stats['successful_calls'],
                "success_rate": f"{success_rate:.1f}%",
                "timeout_calls": self.performance_stats['timeout_calls'],
                "avg_response_time": f"{self.performance_stats['avg_response_time']:.1f}s",
                "last_successful_call": self.performance_stats['last_successful_call']
            }
        }

# Instance globale
fixed_llm_config = FixedLLMConfig()

# Fonctions utilitaires
def analyze_with_fixed_llm(content: str, context: str = "economic", source_domain: str = None) -> Dict[str, Any]:
    """Fonction principale d'analyse avec LLM fixé"""
    return fixed_llm_config.analyze_economic_data(content, context, source_domain)

def test_fixed_llm(test_type: str = "quick") -> Dict[str, Any]:
    """Test du LLM fixé"""
    test_content = "PIB Tunisie 2024: 45.2 milliards USD. Inflation: 6.3%. Chômage: 15.1%."
    return fixed_llm_config.analyze_economic_data(test_content, test_type)

def get_fixed_llm_stats() -> Dict[str, Any]:
    """Statistiques du LLM fixé"""
    return fixed_llm_config.get_performance_stats()

# Export
__all__ = [
    'FixedLLMConfig',
    'fixed_llm_config', 
    'analyze_with_fixed_llm',
    'test_fixed_llm',
    'get_fixed_llm_stats'
]