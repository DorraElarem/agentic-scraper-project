"""
🤖 SCRAPER AGENT SIMPLIFIÉ - Intelligence Automatique
Version refactorisée : Plus de paramètres confus, le système décide tout intelligemment !
"""

from app.scrapers.traditional import TunisianWebScraper
from app.scrapers.intelligent import IntelligentScraper
from app.models.schemas import ScrapeRequest, ScrapedContent, AnalysisType
from app.agents.analyzer_agent import AnalyzerAgent
from typing import Optional, Dict, Any, List
import logging
from app.config.settings import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class ScrapingResult:
    """Classe pour encapsuler les résultats de scraping - VERSION SIMPLIFIÉE"""
    
    def __init__(
        self,
        url: str,
        content: Optional[ScrapedContent] = None,
        success: bool = True,
        error: Optional[str] = None,
        llm_analysis: Optional[Dict[str, Any]] = None,
        timestamp: datetime = None,
        # Métadonnées simplifiées
        strategy_used: str = "auto",
        confidence_score: float = 0.0,
        processing_time: float = 0.0
    ):
        self.url = url
        self.content = content
        self.success = success
        self.error = error
        self.llm_analysis = llm_analysis or {}
        self.timestamp = timestamp or datetime.utcnow()
        self.strategy_used = strategy_used
        self.confidence_score = confidence_score
        self.processing_time = processing_time

    def dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire"""
        return {
            'url': self.url,
            'content': self.content.dict() if self.content else None,
            'success': self.success,
            'error': self.error,
            'llm_analysis': self.llm_analysis,
            'timestamp': self.timestamp.isoformat(),
            'strategy_used': self.strategy_used,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
            'intelligent_features': True
        }

class ScraperAgent:
    """Agent principal de scraping avec INTELLIGENCE AUTOMATIQUE"""
    
    def __init__(self, name: str = "smart_scraper"):
        self.name = name
        self.traditional_scraper = TunisianWebScraper()
        self.intelligent_scraper = IntelligentScraper()
        self.analyzer = AnalyzerAgent() if settings.ENABLE_LLM_ANALYSIS else None
        
        # Configuration d'intelligence automatique
        self.auto_intelligence = {
            'strategy_selection': 'automatic',
            'fallback_enabled': True,
            'learning_enabled': True,
            'quality_optimization': True
        }
        
        # Métriques simplifiées
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'avg_processing_time': 0,
            'best_strategy': 'intelligent'
        }
        
        logger.info(f"🤖 ScraperAgent initialized: {self.name} - Intelligence automatique activée")

    async def scrape(self, request: ScrapeRequest) -> ScrapingResult:
        """🧠 Méthode principale de scraping INTELLIGENTE ET SIMPLIFIÉE"""
        start_time = datetime.utcnow()
        
        try:
            if not request.urls:
                raise ValueError("No URLs provided in ScrapeRequest")
            
            target_url = request.urls[0]
            logger.info(f"🚀 Smart scraping: {target_url}")

            # 1️⃣ SÉLECTION AUTOMATIQUE DE STRATÉGIE
            optimal_strategy = self._select_strategy_automatically(target_url)
            
            # 2️⃣ DÉTECTION AUTOMATIQUE DU MODE LLM
            enable_llm = self._should_enable_llm(request, target_url)
            
            logger.info(f"🎯 Auto-selected: {optimal_strategy} strategy, LLM: {'On' if enable_llm else 'Off'}")

            # 3️⃣ EXÉCUTION INTELLIGENTE
            content = await self._execute_intelligent_scraping(
                target_url, optimal_strategy, enable_llm
            )
            
            # 4️⃣ ANALYSE LLM AUTOMATIQUE (si approprié)
            llm_analysis = {}
            if enable_llm and self.analyzer and content and content.raw_content:
                llm_analysis = self._perform_smart_llm_analysis(content.raw_content, target_url)
            
            # 5️⃣ CALCUL AUTOMATIQUE DE QUALITÉ
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            confidence_score = self._calculate_smart_confidence(content, processing_time)
            
            # 6️⃣ MISE À JOUR DES MÉTRIQUES
            self._update_performance_stats(True, processing_time, optimal_strategy)
            
            if content:
                logger.info(f"✅ Smart scraping successful: {optimal_strategy} strategy")
                return ScrapingResult(
                    url=target_url,
                    content=content,
                    success=True,
                    llm_analysis=llm_analysis,
                    strategy_used=optimal_strategy,
                    confidence_score=confidence_score,
                    processing_time=processing_time
                )
            else:
                self._update_performance_stats(False, processing_time, optimal_strategy)
                logger.error(f"❌ Smart scraping failed for {target_url}")
                return ScrapingResult(
                    url=target_url,
                    content=None,
                    success=False,
                    error='All intelligent methods failed',
                    strategy_used=optimal_strategy,
                    processing_time=processing_time
                )

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            target_url = request.urls[0] if request.urls else 'unknown_url'
            self._update_performance_stats(False, processing_time, 'error')
            logger.error(f"❌ Smart scraping error for {target_url}: {str(e)}")
            return ScrapingResult(
                url=target_url,
                content=None,
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def _select_strategy_automatically(self, url: str) -> str:
        """🎯 Sélection automatique de stratégie (plus d'options confuses)"""
        url_lower = url.lower()
        
        # Logique intelligente simplifiée
        if any(indicator in url_lower for indicator in ['api.', '/api/', '.json', 'worldbank.org']):
            return 'traditional'  # APIs -> Rapide et efficace
        elif any(indicator in url_lower for indicator in ['bct.gov.tn', 'ins.tn', '.gov.']):
            return 'intelligent'  # Sites gouvernementaux -> Complexe
        else:
            return 'intelligent'  # Par défaut -> Sécurité maximale
    
    def _should_enable_llm(self, request: ScrapeRequest, url: str) -> bool:
        """🧠 Décision automatique d'activation LLM"""
        # 1. Si l'utilisateur l'a demandé explicitement
        if hasattr(request, 'enable_llm_analysis') and request.enable_llm_analysis:
            return True
        
        # 2. Si LLM n'est pas disponible
        if not self.analyzer:
            return False
        
        # 3. Décision intelligente basée sur l'URL
        url_lower = url.lower()
        
        # Activer LLM pour sites complexes/gouvernementaux
        if any(indicator in url_lower for indicator in ['bct.gov.tn', 'ins.tn', 'actualites']):
            return True
        
        # Désactiver pour APIs simples
        if any(indicator in url_lower for indicator in ['api.', '.json', 'worldbank.org']):
            return False
        
        # Par défaut : désactivé pour performance
        return False
    
    async def _execute_intelligent_scraping(self, url: str, strategy: str, enable_llm: bool) -> Optional[ScrapedContent]:
        """🚀 Exécution intelligente avec fallback automatique"""
        try:
            # Exécution primaire
            if strategy == 'traditional':
                content = self.traditional_scraper.scrape(url)
            else:
                content = self.intelligent_scraper.scrape_with_analysis(url, enable_llm_analysis=enable_llm)
            
            # Fallback automatique si échec
            if not content and strategy == 'traditional':
                logger.warning(f"⚡ Auto-fallback: traditional → intelligent for {url}")
                content = self.intelligent_scraper.scrape_with_analysis(url, enable_llm_analysis=enable_llm)
            elif not content and strategy == 'intelligent':
                logger.warning(f"⚡ Auto-fallback: intelligent → traditional for {url}")
                content = self.traditional_scraper.scrape(url)
            
            return content
            
        except Exception as e:
            logger.error(f"❌ Intelligent scraping execution failed: {e}")
            return None
    
    def _perform_smart_llm_analysis(self, content: str, url: str) -> Dict[str, Any]:
        """🧠 Analyse LLM intelligente et robuste"""
        try:
            if not self.analyzer or not content or len(content) < 50:
                return {"message": "Analyse LLM non applicable", "reason": "insufficient_content"}
            
            # Détection automatique de catégorie
            analysis_category = self._detect_content_category(content, url)
            
            # Préparer les données
            analyzer_data = {
                "content": content[:8000],  # Limite pour éviter timeout
                "analysis_type": analysis_category,
                "source": url,
                "request_timestamp": datetime.utcnow().isoformat()
            }
            
            # Analyse avec gestion d'erreur
            result = self.analyzer.analyze_scraped_data(analyzer_data)
            
            if result and hasattr(result, 'insights'):
                return {
                    "analysis_category": analysis_category,
                    "insights": result.insights,
                    "confidence_score": result.confidence_score,
                    "analyzer_status": "success",
                    "enhanced_features": getattr(result, 'enhanced_insights', {})
                }
            else:
                return {
                    "message": "Analyse LLM incomplète",
                    "analyzer_status": "partial_failure"
                }

        except Exception as e:
            logger.warning(f"⚠️ LLM analysis failed: {e}")
            return {
                "message": "Analyse LLM échouée",
                "error": str(e),
                "analyzer_status": "failed"
            }
    
    def _detect_content_category(self, content: str, url: str) -> str:
        """🏷️ Détection automatique de catégorie pour analyse"""
        content_lower = content.lower()
        url_lower = url.lower()
        
        if 'bct.gov.tn' in url_lower or any(term in content_lower for term in ['banque centrale', 'monétaire']):
            return "economic"
        elif 'ins.tn' in url_lower or any(term in content_lower for term in ['statistique', 'démographie']):
            return "statistical"
        elif any(term in content_lower for term in ['industrie', 'production']):
            return "industrial"
        else:
            return "general"
    
    def _calculate_smart_confidence(self, content: Optional[ScrapedContent], processing_time: float) -> float:
        """🎯 Calcul intelligent de confiance"""
        if not content:
            return 0.0
        
        confidence_factors = []
        
        # Facteur de contenu
        if content.raw_content:
            content_length = len(content.raw_content)
            confidence_factors.append(min(content_length / 1000, 1.0) * 0.4)
        
        # Facteur de données structurées
        if content.structured_data:
            data_richness = len(content.structured_data)
            confidence_factors.append(min(data_richness / 5, 1.0) * 0.3)
        
        # Facteur de performance (temps)
        time_factor = max(0, 1 - (processing_time / 60))  # Pénalité si > 60s
        confidence_factors.append(time_factor * 0.2)
        
        # Facteur de métadonnées
        if content.metadata:
            confidence_factors.append(0.1)
        
        return sum(confidence_factors)
    
    def _update_performance_stats(self, success: bool, processing_time: float, strategy: str):
        """Mise à jour des statistiques de performance"""
        try:
            self.performance_stats['total_requests'] += 1
            
            if success:
                self.performance_stats['successful_requests'] += 1
                # Mettre à jour la meilleure stratégie
                self.performance_stats['best_strategy'] = strategy
            
            # Moyenne mobile du temps de traitement
            current_avg = self.performance_stats['avg_processing_time']
            total = self.performance_stats['total_requests']
            
            self.performance_stats['avg_processing_time'] = (
                (current_avg * (total - 1)) + processing_time
            ) / total
            
        except Exception as e:
            logger.warning(f"Failed to update performance stats: {e}")
    
    def get_scraper_status(self) -> Dict[str, Any]:
        """Statut de l'agent scraper intelligent"""
        success_rate = 0
        if self.performance_stats['total_requests'] > 0:
            success_rate = self.performance_stats['successful_requests'] / self.performance_stats['total_requests']
        
        return {
            "agent_name": self.name,
            "agent_type": "SmartScraperAgent",
            "version": "2.0_simplified_auto",
            "scrapers_available": {
                "traditional": True,
                "intelligent": True
            },
            "llm_analysis_available": bool(self.analyzer),
            "auto_intelligence": self.auto_intelligence,
            "performance_stats": {
                **self.performance_stats,
                "success_rate": success_rate
            },
            "features": [
                "automatic_strategy_selection",
                "intelligent_llm_activation", 
                "automatic_fallback",
                "smart_quality_assessment",
                "zero_configuration_scraping"
            ]
        }

    def test_scrapers(self, test_url: str = "https://httpbin.org/html") -> Dict[str, Any]:
        """Test intelligent des scrapers"""
        results = {
            "test_url": test_url,
            "timestamp": datetime.utcnow().isoformat(),
            "intelligent_features": True
        }
        
        try:
            # Test automatique de stratégie
            auto_strategy = self._select_strategy_automatically(test_url)
            results["auto_selected_strategy"] = auto_strategy
            
            # Test scraper traditionnel
            traditional_result = self.traditional_scraper.scrape(test_url)
            results["traditional"] = {
                "success": traditional_result is not None,
                "content_length": len(traditional_result.raw_content) if traditional_result else 0
            }
            
            # Test scraper intelligent
            intelligent_result = self.intelligent_scraper.scrape_with_analysis(test_url, enable_llm_analysis=False)
            results["intelligent"] = {
                "success": intelligent_result is not None,
                "content_length": len(intelligent_result.raw_content) if intelligent_result else 0
            }
            
            # Test LLM si disponible
            if self.analyzer and traditional_result:
                llm_test = self._perform_smart_llm_analysis(
                    traditional_result.raw_content[:1000], test_url
                )
                results["llm_analysis"] = {
                    "success": llm_test.get("analyzer_status") == "success",
                    "category": llm_test.get("analysis_category", "unknown")
                }
            else:
                results["llm_analysis"] = {
                    "success": False,
                    "reason": "LLM analyzer not available"
                }
                
        except Exception as e:
            results["test_error"] = str(e)
        
        return results
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Analytiques de performance simplifiées"""
        stats = self.performance_stats
        
        if stats['total_requests'] == 0:
            return {'message': 'No operations performed yet'}
        
        success_rate = stats['successful_requests'] / stats['total_requests']
        
        return {
            'summary': {
                'total_operations': stats['total_requests'],
                'success_rate': success_rate,
                'average_processing_time': stats['avg_processing_time'],
                'best_strategy': stats['best_strategy']
            },
            'performance_level': 'excellent' if success_rate > 0.8 else 'good' if success_rate > 0.6 else 'needs_improvement',
            'intelligence_status': 'fully_automatic',
            'recommendations': self._generate_performance_recommendations(success_rate)
        }
    
    def _generate_performance_recommendations(self, success_rate: float) -> List[str]:
        """Recommandations basées sur la performance"""
        recommendations = []
        
        if success_rate > 0.9:
            recommendations.append("Performance excellente - système optimal")
        elif success_rate > 0.7:
            recommendations.append("Bonne performance - quelques optimisations possibles")
        elif success_rate > 0.5:
            recommendations.append("Performance acceptable - révision des sources recommandée")
        else:
            recommendations.append("Performance faible - vérifier la connectivité et les sources")
        
        avg_time = self.performance_stats['avg_processing_time']
        if avg_time > 30:
            recommendations.append("Temps de traitement élevé - optimisation recommandée")
        elif avg_time < 5:
            recommendations.append("Traitement très rapide - capacité disponible pour plus de sources")
        
        return recommendations
    
    def configure_intelligence(self, **config_updates):
        """Configuration de l'intelligence automatique"""
        valid_keys = self.auto_intelligence.keys()
        updated = []
        
        for key, value in config_updates.items():
            if key in valid_keys:
                self.auto_intelligence[key] = value
                updated.append(key)
                logger.info(f"Updated intelligence config: {key} = {value}")
            else:
                logger.warning(f"Invalid intelligence config key: {key}")
        
        return {
            'updated_keys': updated,
            'current_config': self.auto_intelligence
        }
    
    def reset_performance_stats(self):
        """Remet à zéro les statistiques"""
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'avg_processing_time': 0,
            'best_strategy': 'intelligent'
        }
        logger.info(f"Performance stats reset for {self.name}")
    
    def export_intelligence_data(self) -> Dict[str, Any]:
        """Export des données d'intelligence"""
        return {
            'agent_name': self.name,
            'agent_type': 'SmartScraperAgent',
            'version': '2.0_simplified_auto',
            'auto_intelligence': self.auto_intelligence,
            'performance_stats': self.performance_stats,
            'export_timestamp': datetime.utcnow().isoformat()
        }
    
    def _update_performance_stats(self, success: bool, processing_time: float, strategy: str):
        """📊 Mise à jour des statistiques de performance"""
        try:
            self.performance_stats['total_requests'] += 1
            
            if success:
                self.performance_stats['successful_requests'] += 1
                # Mettre à jour la meilleure stratégie
                self.performance_stats['best_strategy'] = strategy
            
            # Moyenne mobile du temps de traitement
            current_avg = self.performance_stats['avg_processing_time']
            total = self.performance_stats['total_requests']
            
            self.performance_stats['avg_processing_time'] = (
                (current_avg * (total - 1)) + processing_time
            ) / total
            
        except Exception as e:
            logger.warning(f"Failed to update performance stats: {e}")
    
    # MÉTHODES DE STATUT ET INFORMATIONS
    
    def get_scraper_status(self) -> Dict[str, Any]:
        """📋 Statut de l'agent scraper intelligent"""
        success_rate = 0
        if self.performance_stats['total_requests'] > 0:
            success_rate = self.performance_stats['successful_requests'] / self.performance_stats['total_requests']
        
        return {
            "agent_name": self.name,
            "agent_type": "SmartScraperAgent",
            "version": "2.0_simplified_auto",
            "scrapers_available": {
                "traditional": True,
                "intelligent": True
            },
            "llm_analysis_available": bool(self.analyzer),
            "auto_intelligence": self.auto_intelligence,
            "performance_stats": {
                **self.performance_stats,
                "success_rate": success_rate
            },
            "features": [
                "automatic_strategy_selection",
                "intelligent_llm_activation",
                "automatic_fallback",
                "smart_quality_assessment",
                "zero_configuration_scraping"
            ]
        }

    def test_scrapers(self, test_url: str = "https://httpbin.org/html") -> Dict[str, Any]:
        """🔧 Test intelligent des scrapers"""
        results = {
            "test_url": test_url,
            "timestamp": datetime.utcnow().isoformat(),
            "intelligent_features": True
        }
        
        try:
            # Test automatique de stratégie
            auto_strategy = self._select_strategy_automatically(test_url)
            results["auto_selected_strategy"] = auto_strategy
            
            # Test scraper traditionnel
            traditional_result = self.traditional_scraper.scrape(test_url)
            results["traditional"] = {
                "success": traditional_result is not None,
                "content_length": len(traditional_result.raw_content) if traditional_result else 0
            }
            
            # Test scraper intelligent
            intelligent_result = self.intelligent_scraper.scrape_with_analysis(test_url, enable_llm_analysis=False)
            results["intelligent"] = {
                "success": intelligent_result is not None,
                "content_length": len(intelligent_result.raw_content) if intelligent_result else 0
            }
            
            # Test LLM si disponible
            if self.analyzer and traditional_result:
                llm_test = self._perform_smart_llm_analysis(
                    traditional_result.raw_content[:1000], test_url
                )
                results["llm_analysis"] = {
                    "success": llm_test.get("analyzer_status") == "success",
                    "category": llm_test.get("analysis_category", "unknown")
                }
            else:
                results["llm_analysis"] = {
                    "success": False,
                    "reason": "LLM analyzer not available"
                }
                
        except Exception as e:
            results["test_error"] = str(e)
        
        return results
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """📈 Analytiques de performance simplifiées"""
        stats = self.performance_stats
        
        if stats['total_requests'] == 0:
            return {'message': 'No operations performed yet'}
        
        success_rate = stats['successful_requests'] / stats['total_requests']
        
        return {
            'summary': {
                'total_operations': stats['total_requests'],
                'success_rate': success_rate,
                'average_processing_time': stats['avg_processing_time'],
                'best_strategy': stats['best_strategy']
            },
            'performance_level': 'excellent' if success_rate > 0.8 else 'good' if success_rate > 0.6 else 'needs_improvement',
            'intelligence_status': 'fully_automatic',
            'recommendations': self._generate_performance_recommendations(success_rate)
        }
    
    def _generate_performance_recommendations(self, success_rate: float) -> List[str]:
        """💡 Recommandations basées sur la performance"""
        recommendations = []
        
        if success_rate > 0.9:
            recommendations.append("Performance excellente - système optimal")
        elif success_rate > 0.7:
            recommendations.append("Bonne performance - quelques optimisations possibles")
        elif success_rate > 0.5:
            recommendations.append("Performance acceptable - révision des sources recommandée")
        else:
            recommendations.append("Performance faible - vérifier la connectivité et les sources")
        
        avg_time = self.performance_stats['avg_processing_time']
        if avg_time > 30:
            recommendations.append("Temps de traitement élevé - optimisation recommandée")
        elif avg_time < 5:
            recommendations.append("Traitement très rapide - capacité disponible pour plus de sources")
        
        return recommendations
    
    # MÉTHODES DE CONFIGURATION SIMPLIFIÉES
    
    def configure_intelligence(self, **config_updates):
        """⚙️ Configuration de l'intelligence automatique"""
        valid_keys = self.auto_intelligence.keys()
        updated = []
        
        for key, value in config_updates.items():
            if key in valid_keys:
                self.auto_intelligence[key] = value
                updated.append(key)
                logger.info(f"Updated intelligence config: {key} = {value}")
            else:
                logger.warning(f"Invalid intelligence config key: {key}")
        
        return {
            'updated_keys': updated,
            'current_config': self.auto_intelligence
        }
    
    def reset_performance_stats(self):
        """🔄 Remet à zéro les statistiques"""
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'avg_processing_time': 0,
            'best_strategy': 'intelligent'
        }
        logger.info(f"Performance stats reset for {self.name}")
    
    def export_intelligence_data(self) -> Dict[str, Any]:
        """📤 Export des données d'intelligence"""
        return {
            'agent_name': self.name,
            'agent_type': 'SmartScraperAgent',
            'version': '2.0_simplified_auto',
            'auto_intelligence': self.auto_intelligence,
            'performance_stats': self.performance_stats,
            'export_timestamp': datetime.utcnow().isoformat()
        }