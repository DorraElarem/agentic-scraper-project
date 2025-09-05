"""
SMART COORDINATOR INTÉGRÉ - CORRECTIFS CRITIQUES TIMEOUTS
Solution de cohérence complète avec timeouts adaptatifs pour sites tunisiens
"""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse

# Import des scrapers avec gestion d'erreur robuste
try:
    from app.scrapers.traditional import TunisianWebScraper
    TRADITIONAL_AVAILABLE = True
except ImportError as e:
    logging.error(f"TunisianWebScraper import failed: {e}")
    TRADITIONAL_AVAILABLE = False

try:
    from app.scrapers.intelligent import IntelligentScraper
    INTELLIGENT_AVAILABLE = True
except ImportError as e:
    logging.error(f"IntelligentScraper import failed: {e}")
    INTELLIGENT_AVAILABLE = False

# Import des schemas
from app.models.schemas import ScrapedContent

# Import de la configuration
from app.config.settings import settings
try:
    from app.config.llm_config import fixed_llm_config, analyze_with_fixed_llm
    LLM_CONFIG_AVAILABLE = True
except ImportError:
    LLM_CONFIG_AVAILABLE = False

# INTÉGRATION CRITIQUE : Import des utils avec gestion d'erreur
try:
    from app.utils.data_validator import validate_indicators_strict, strict_validator
    DATA_VALIDATOR_AVAILABLE = True
except ImportError:
    DATA_VALIDATOR_AVAILABLE = False

try:
    from app.utils.temporal_filter import filter_by_temporal_period, temporal_filter
    TEMPORAL_FILTER_AVAILABLE = True
except ImportError:
    TEMPORAL_FILTER_AVAILABLE = False

try:
    from app.utils.clean_extraction_patterns import extract_clean_economic_data, clean_extractor
    CLEAN_EXTRACTOR_AVAILABLE = True
except ImportError:
    CLEAN_EXTRACTOR_AVAILABLE = False

try:
    from app.utils.helpers import (
        validate_task_parameters, suggest_optimal_strategy, 
        detect_tunisian_content_patterns, debug_extraction_data
    )
    HELPERS_AVAILABLE = True
except ImportError:
    HELPERS_AVAILABLE = False

try:
    from app.utils.storage import smart_storage
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False

# INTÉGRATION : Import des agents avec gestion d'erreur
try:
    from app.agents.analyzer_agent import AnalyzerAgent
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    logging.warning("AnalyzerAgent not available")

try:
    from app.agents.navigation_agent import NavigationAgent
    NAVIGATION_AVAILABLE = True
except ImportError:
    NAVIGATION_AVAILABLE = False
    logging.warning("NavigationAgent not available")

try:
    from app.agents.langgraph_agent import get_langgraph_integration
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logging.warning("LangGraph not available")

logger = logging.getLogger(__name__)

class IntegratedSmartCoordinator:
    """Coordinateur intégré avec timeouts adaptatifs pour sites tunisiens"""
    
    def __init__(self):
        # Configuration des timeouts spécialisés par domaine
        self.domain_timeouts = {
            'bct.gov.tn': getattr(settings, 'BCT_TIMEOUT', 300),        # 5 minutes pour BCT
            'ins.tn': getattr(settings, 'INS_TIMEOUT', 240),            # 4 minutes pour INS
            'finances.gov.tn': getattr(settings, 'GOV_TN_TIMEOUT', 200), # 3.3 minutes
            '.gov.tn': getattr(settings, 'GOV_TN_TIMEOUT', 200),        # Sites gouvernementaux génériques
            'api.worldbank.org': 60,                                     # 1 minute pour APIs
            'restcountries.com': 30,                                     # 30s pour APIs simples
            'default': getattr(settings, 'REQUEST_TIMEOUT', 180)        # 3 minutes par défaut
        }
        
        # Scrapers de base avec gestion d'erreur
        self.traditional_scraper = None
        self.intelligent_scraper = None
        
        if TRADITIONAL_AVAILABLE:
            try:
                self.traditional_scraper = TunisianWebScraper()
                logger.info("TunisianWebScraper initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize TunisianWebScraper: {e}")
        
        if INTELLIGENT_AVAILABLE:
            try:
                self.intelligent_scraper = IntelligentScraper()
                logger.info("IntelligentScraper initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize IntelligentScraper: {e}")
        
        # INTÉGRATION : Agents optionnels
        self.analyzer_agent = None
        self.navigation_agent = None
        self.langgraph_integration = None
        
        if ANALYZER_AVAILABLE:
            try:
                self.analyzer_agent = AnalyzerAgent()
            except Exception as e:
                logger.error(f"Failed to initialize AnalyzerAgent: {e}")
        
        if NAVIGATION_AVAILABLE:
            try:
                self.navigation_agent = NavigationAgent("coordinator_nav")
            except Exception as e:
                logger.error(f"Failed to initialize NavigationAgent: {e}")
                
        if LANGGRAPH_AVAILABLE:
            try:
                self.langgraph_integration = get_langgraph_integration()
            except Exception as e:
                logger.error(f"Failed to initialize LangGraph: {e}")
        
        # INTÉGRATION : Configuration cohérente
        self.config = {
            'llm_timeout': getattr(settings, 'OLLAMA_TIMEOUT', 900),
            'request_timeout': getattr(settings, 'REQUEST_TIMEOUT', 180),
            'quality_threshold': getattr(settings, 'LLM_QUALITY_THRESHOLD', 0.1),
            'enable_llm': getattr(settings, 'ENABLE_LLM_ANALYSIS', True),
            'tunisian_optimization': True,
            'use_all_utils': True,
            'domain_timeouts': self.domain_timeouts
        }
        
        # Métriques intégrées
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'timeout_failures': 0,
            'fallback_successes': 0,
            'strategy_usage': {'traditional': 0, 'intelligent': 0, 'langgraph': 0},
            'timeout_usage': {domain: 0 for domain in self.domain_timeouts.keys()},
            'utils_usage': {
                'data_validator': 0,
                'temporal_filter': 0,
                'clean_extractor': 0,
                'helpers': 0
            },
            'agents_usage': {
                'analyzer': 0,
                'navigation': 0,
                'langgraph': 0
            }
        }
        
        logger.info("🎯 IntegratedSmartCoordinator initialized with TIMEOUT FIXES")
        logger.info(f"   - Traditional Scraper: {'Available' if self.traditional_scraper else 'Missing'}")
        logger.info(f"   - Intelligent Scraper: {'Available' if self.intelligent_scraper else 'Missing'}")
        logger.info(f"   - Analyzer: {'Available' if self.analyzer_agent else 'Missing'}")
        logger.info(f"   - Navigation: {'Available' if self.navigation_agent else 'Missing'}")
        logger.info(f"   - LangGraph: {'Available' if self.langgraph_integration else 'Missing'}")
        logger.info(f"   - Domain timeouts: {self.domain_timeouts}")
    
    def scrape(self, url: str, enable_llm_analysis: bool = False, 
               quality_threshold: float = 0.1, timeout: int = None) -> Optional[ScrapedContent]:
        """Coordinateur intelligent avec timeouts adaptatifs CORRIGÉ"""
        
        start_time = time.time()
        self.performance_metrics['total_requests'] += 1
        
        domain = self._extract_domain(url)
        optimal_timeout = timeout or self._get_domain_timeout(domain)
        
        logger.info(f"🎯 Smart Coordinator FIXED: Processing {url}")
        logger.info(f"   Domain: {domain}, Timeout: {optimal_timeout}s")
        
        try:
            # ÉTAPE 1: Sélection de stratégie intelligente
            strategy = self._select_smart_strategy_with_domain(url, domain)
            
            # ÉTAPE 2: Exécution avec timeout adaptatif
            result = self._execute_with_adaptive_timeout(
                url, strategy, enable_llm_analysis, optimal_timeout
            )
            
            if result:
                # ÉTAPE 3: Post-processing intégré si réussite
                if self._has_valid_content(result):
                    result = self._apply_integrated_post_processing(result, url, domain)
                    
                    execution_time = time.time() - start_time
                    self.performance_metrics['successful_requests'] += 1
                    
                    logger.info(f"✅ Success: {url} in {execution_time:.1f}s with {strategy}")
                    return result
                else:
                    logger.warning(f"Empty result from {strategy}, trying fallback")
                    # Fallback automatique
                    return self._try_fallback_strategy(url, strategy, enable_llm_analysis, optimal_timeout)
            else:
                logger.warning(f"❌ Primary strategy {strategy} failed, trying fallback")
                # Fallback automatique
                return self._try_fallback_strategy(url, strategy, enable_llm_analysis, optimal_timeout)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Smart coordinator failed for {url} after {execution_time:.1f}s: {e}")
            
            # Tentative de récupération d'urgence
            return self._emergency_fallback(url, enable_llm_analysis)
    
    def _extract_domain(self, url: str) -> str:
        """Extraction sécurisée du domaine"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception as e:
            logger.warning(f"Failed to parse URL {url}: {e}")
            return "unknown"
    
    def _get_domain_timeout(self, domain: str) -> int:
        """Timeout adaptatif selon le domaine avec fallback intelligent"""
        
        # Recherche exacte d'abord
        if domain in self.domain_timeouts:
            timeout = self.domain_timeouts[domain]
            self.performance_metrics['timeout_usage'][domain] += 1
            return timeout
        
        # Recherche par pattern
        for domain_pattern, timeout in self.domain_timeouts.items():
            if domain_pattern != 'default' and domain_pattern in domain:
                self.performance_metrics['timeout_usage'][domain_pattern] += 1
                logger.debug(f"Domain {domain} matched pattern {domain_pattern}, timeout: {timeout}s")
                return timeout
        
        # Fallback
        default_timeout = self.domain_timeouts['default']
        self.performance_metrics['timeout_usage']['default'] += 1
        logger.debug(f"Domain {domain} using default timeout: {default_timeout}s")
        return default_timeout
    
    def _select_smart_strategy_with_domain(self, url: str, domain: str) -> str:
        """Sélection de stratégie basée sur l'URL et le domaine"""
        
        url_lower = url.lower()
        
        # 1. APIs et données structurées → Traditional (rapide et efficace)
        api_indicators = ['api.', '/api/', 'format=json', 'format=xml', 'restcountries']
        if any(indicator in url_lower for indicator in api_indicators):
            logger.debug(f"API detected, using traditional strategy")
            return 'traditional'
        
        # 2. Sites gouvernementaux tunisiens → Intelligent (contenu complexe)
        gov_patterns = ['bct.gov.tn', 'ins.tn', 'finances.gov.tn', '.gov.tn']
        if any(pattern in domain for pattern in gov_patterns):
            logger.debug(f"Tunisian government site detected, using intelligent strategy")
            return 'intelligent'
        
        # 3. Contenu dynamique → Intelligent
        dynamic_indicators = ['.jsp', '.asp', '.php', 'javascript:', 'tableau']
        if any(indicator in url_lower for indicator in dynamic_indicators):
            logger.debug(f"Dynamic content detected, using intelligent strategy")
            return 'intelligent'
        
        # 4. Par défaut → Traditional (plus fiable et rapide)
        logger.debug(f"Using default traditional strategy")
        return 'traditional'
    
    def _execute_with_adaptive_timeout(self, url: str, strategy: str, 
                                     enable_llm: bool, timeout: int) -> Optional[ScrapedContent]:
        """Exécution avec timeout adaptatif et gestion d'erreur robuste"""
        
        self.performance_metrics['strategy_usage'][strategy] += 1
        
        try:
            if strategy == 'traditional' and self.traditional_scraper:
                logger.debug(f"Executing traditional scrape with {timeout}s timeout")
                return self._scrape_with_timeout(
                    self.traditional_scraper, 'scrape', url, 
                    timeout, enable_llm_analysis=enable_llm
                )
                
            elif strategy == 'intelligent' and self.intelligent_scraper:
                logger.debug(f"Executing intelligent scrape with {timeout}s timeout")
                return self._scrape_with_timeout(
                    self.intelligent_scraper, 'scrape_with_analysis', url,
                    timeout, enable_llm_analysis=enable_llm
                )
            
            elif strategy == 'langgraph' and self.langgraph_integration:
                logger.debug(f"Executing LangGraph workflow with {timeout}s timeout")
                self.performance_metrics['agents_usage']['langgraph'] += 1
                return self.langgraph_integration.process_with_langgraph(url)
            
            else:
                logger.error(f"Strategy {strategy} not available or scraper not initialized")
                return None
                
        except Exception as e:
            if "timeout" in str(e).lower():
                self.performance_metrics['timeout_failures'] += 1
                logger.error(f"Timeout failure for {url} with {strategy} after {timeout}s: {e}")
            else:
                logger.error(f"Execution failed for {url} with {strategy}: {e}")
            return None
    
    def _scrape_with_timeout(self, scraper, method_name: str, url: str, 
                           timeout: int, **kwargs) -> Optional[ScrapedContent]:
        """Exécution de scraping avec timeout configuré"""
        
        try:
            # Configuration du timeout sur le scraper si possible
            if hasattr(scraper, 'session') and hasattr(scraper.session, 'timeout'):
                original_timeout = getattr(scraper.session, 'timeout', None)
                scraper.session.timeout = timeout
                
                try:
                    method = getattr(scraper, method_name)
                    result = method(url, **kwargs)
                    return result
                finally:
                    # Restaurer le timeout original
                    if original_timeout is not None:
                        scraper.session.timeout = original_timeout
            else:
                # Fallback sans configuration de timeout
                method = getattr(scraper, method_name)
                return method(url, **kwargs)
                
        except Exception as e:
            logger.error(f"Scraping with timeout failed: {e}")
            return None
    
    def _try_fallback_strategy(self, url: str, primary_strategy: str, 
                             enable_llm: bool, timeout: int) -> Optional[ScrapedContent]:
        """Tentative de stratégie de fallback"""
        
        fallback_strategy = 'intelligent' if primary_strategy == 'traditional' else 'traditional'
        
        logger.info(f"🔄 Trying fallback strategy: {primary_strategy} → {fallback_strategy}")
        
        result = self._execute_with_adaptive_timeout(
            url, fallback_strategy, enable_llm, timeout
        )
        
        if result and self._has_valid_content(result):
            self.performance_metrics['fallback_successes'] += 1
            logger.info(f"✅ Fallback successful with {fallback_strategy}")
            return result
        else:
            logger.warning(f"❌ Fallback {fallback_strategy} also failed")
            return None
    
    def _emergency_fallback(self, url: str, enable_llm: bool) -> Optional[ScrapedContent]:
        """Fallback d'urgence avec timeout minimal"""
        
        logger.warning(f"🚨 Emergency fallback for {url}")
        
        # Essayer traditional avec timeout très court
        if self.traditional_scraper:
            try:
                return self._scrape_with_timeout(
                    self.traditional_scraper, 'scrape', url, 
                    30, enable_llm_analysis=False  # Force disable LLM
                )
            except Exception as e:
                logger.error(f"Emergency fallback failed: {e}")
        
        return None
    
    def _has_valid_content(self, result: ScrapedContent) -> bool:
        """Vérifie si le résultat contient du contenu valide"""
        
        if not result:
            return False
        
        # Vérifier le contenu brut
        if result.raw_content and len(result.raw_content.strip()) > 50:
            return True
        
        # Vérifier les données structurées
        if (result.structured_data and 
            isinstance(result.structured_data, dict) and 
            result.structured_data.get('extracted_values')):
            return True
        
        return False
    
    def _apply_integrated_post_processing(self, result: ScrapedContent, url: str, domain: str) -> ScrapedContent:
        """Post-traitement intégré avec gestion d'erreur robuste"""
        
        try:
            extracted_values = result.structured_data.get('extracted_values', {}) if result.structured_data else {}
            
            if not extracted_values:
                logger.debug("No extracted values for post-processing")
                return result
            
            logger.info(f"📊 Post-processing {len(extracted_values)} extracted values")
            
            # 1. NETTOYAGE avec clean_extraction_patterns (si disponible)
            if CLEAN_EXTRACTOR_AVAILABLE and result.raw_content and len(extracted_values) < 3:
                try:
                    self.performance_metrics['utils_usage']['clean_extractor'] += 1
                    logger.debug("🧹 Applying clean extraction patterns")
                    clean_values = extract_clean_economic_data(result.raw_content, url)
                    if clean_values and len(clean_values) > len(extracted_values):
                        logger.info(f"✨ Clean extraction improved: {len(extracted_values)} → {len(clean_values)}")
                        extracted_values.update(clean_values)
                except Exception as e:
                    logger.warning(f"Clean extraction failed: {e}")
            
            # 2. FILTRAGE TEMPOREL (si disponible)
            if TEMPORAL_FILTER_AVAILABLE:
                try:
                    self.performance_metrics['utils_usage']['temporal_filter'] += 1
                    filtered_values = filter_by_temporal_period(extracted_values, result.raw_content or "")
                    logger.info(f"📅 Temporal filtering: {len(extracted_values)} → {len(filtered_values)}")
                    extracted_values = filtered_values
                except Exception as e:
                    logger.warning(f"Temporal filtering failed: {e}")
            
            # 3. VALIDATION STRICTE (si disponible)
            if DATA_VALIDATOR_AVAILABLE:
                try:
                    self.performance_metrics['utils_usage']['data_validator'] += 1
                    
                    validation_result = validate_indicators_strict(
                        [v for v in extracted_values.values() if isinstance(v, dict)],
                        content=result.raw_content or ""
                    )
                    
                    logger.info(f"✅ Validation: {validation_result['summary']['valid_output']} valid indicators")
                    
                    # Mise à jour si validation réussie
                    if validation_result['valid'] and validation_result['valid_data']:
                        validated_dict = {
                            f"validated_{i}": item for i, item in enumerate(validation_result['valid_data'])
                        }
                        result.structured_data['extracted_values'] = validated_dict
                        
                        # Métadonnées de post-processing
                        result.structured_data['post_processing'] = {
                            'clean_extraction_applied': CLEAN_EXTRACTOR_AVAILABLE,
                            'temporal_filtering_applied': TEMPORAL_FILTER_AVAILABLE,
                            'strict_validation_applied': True,
                            'original_count': len(extracted_values),
                            'validated_count': len(validated_dict),
                            'validation_summary': validation_result['summary'],
                            'domain_timeout_used': self._get_domain_timeout(domain)
                        }
                    
                except Exception as e:
                    logger.warning(f"Validation failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Post-processing failed: {e}")
            return result
    
    def get_integrated_status(self) -> Dict[str, Any]:
        """Statut complet du coordinateur intégré avec métriques de timeout"""
        
        total_requests = self.performance_metrics['total_requests']
        success_rate = (
            self.performance_metrics['successful_requests'] / max(total_requests, 1)
        )
        
        return {
            'coordinator_type': 'IntegratedSmartCoordinator',
            'version': 'timeout_fixes_v1.0',
            'status': 'operational_with_timeout_management',
            
            # Modules intégrés avec disponibilité
            'integrated_modules': {
                'scrapers': {
                    'traditional': TRADITIONAL_AVAILABLE and (self.traditional_scraper is not None),
                    'intelligent': INTELLIGENT_AVAILABLE and (self.intelligent_scraper is not None)
                },
                'utils': {
                    'data_validator': DATA_VALIDATOR_AVAILABLE,
                    'temporal_filter': TEMPORAL_FILTER_AVAILABLE,
                    'clean_extractor': CLEAN_EXTRACTOR_AVAILABLE,
                    'helpers': HELPERS_AVAILABLE,
                    'storage': STORAGE_AVAILABLE
                },
                'agents': {
                    'analyzer': ANALYZER_AVAILABLE and (self.analyzer_agent is not None),
                    'navigation': NAVIGATION_AVAILABLE and (self.navigation_agent is not None),
                    'langgraph': LANGGRAPH_AVAILABLE and (self.langgraph_integration is not None)
                },
                'config': {
                    'settings': True,
                    'llm_config': LLM_CONFIG_AVAILABLE
                }
            },
            
            # Métriques de performance avec timeouts
            'performance_metrics': {
                **self.performance_metrics,
                'success_rate': success_rate,
                'timeout_failure_rate': self.performance_metrics['timeout_failures'] / max(total_requests, 1),
                'fallback_success_rate': self.performance_metrics['fallback_successes'] / max(total_requests, 1)
            },
            
            # Configuration des timeouts
            'timeout_configuration': self.domain_timeouts,
            
            # Capacités avec corrections
            'capabilities': [
                'adaptive_timeout_management',
                'domain_specific_timeouts',
                'intelligent_fallback_strategy',
                'robust_error_handling',
                'multi_strategy_execution',
                'integrated_post_processing',
                'tunisian_government_optimization',
                'emergency_recovery'
            ]
        }
    
    def test_coordinator_functionality(self) -> Dict[str, Any]:
        """Test des fonctionnalités avec timeouts"""
        
        test_results = {
            'coordinator_available': True,
            'timeout_configuration': self.domain_timeouts,
            'scrapers_available': {
                'traditional': self.traditional_scraper is not None,
                'intelligent': self.intelligent_scraper is not None
            },
            'test_timestamp': datetime.utcnow().isoformat()
        }
        
        # Test simple avec URL de test
        try:
            test_url = "https://httpbin.org/json"
            test_timeout = 30
            
            logger.info(f"Testing coordinator with {test_url} (timeout: {test_timeout}s)")
            test_result = self.scrape(test_url, enable_llm_analysis=False, timeout=test_timeout)
            
            test_results['functionality_test'] = {
                'test_url': test_url,
                'timeout_used': test_timeout,
                'success': test_result is not None,
                'has_content': self._has_valid_content(test_result) if test_result else False
            }
            
        except Exception as e:
            test_results['functionality_test'] = {
                'success': False,
                'error': str(e)
            }
        
        return test_results
    
    def debug_extraction(self, url: str) -> Dict[str, Any]:
        """Debug de l'extraction avec informations de timeout"""
        
        domain = self._extract_domain(url)
        timeout = self._get_domain_timeout(domain)
        strategy = self._select_smart_strategy_with_domain(url, domain)
        
        debug_info = {
            'url': url,
            'domain': domain,
            'selected_strategy': strategy,
            'timeout': timeout,
            'debug_timestamp': datetime.utcnow().isoformat(),
            'timeout_source': 'domain_specific' if domain in self.domain_timeouts else 'pattern_match'
        }
        
        try:
            result = self.scrape(url, enable_llm_analysis=False, timeout=timeout)
            
            debug_info['extraction_result'] = {
                'success': result is not None,
                'has_valid_content': self._has_valid_content(result),
                'content_length': len(result.raw_content) if result and result.raw_content else 0,
                'has_structured_data': bool(result and result.structured_data) if result else False,
                'extraction_count': len(result.structured_data.get('extracted_values', {})) if result and result.structured_data else 0
            }
            
        except Exception as e:
            debug_info['extraction_result'] = {
                'success': False,
                'error': str(e)
            }
        
        return debug_info

# Alias pour compatibilité
SmartScrapingCoordinator = IntegratedSmartCoordinator