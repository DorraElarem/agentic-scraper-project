"""
MULTI-AGENT ORCHESTRATOR SIMPLIFIÉ - Intelligence Automatique
Architecture refactorisée : Le système décide automatiquement de tout !
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Imports des agents simplifiés
from app.agents.navigation_agent import NavigationAgent
from app.agents.analyzer_agent import AnalyzerAgent
from app.agents.smart_coordinator import SmartScrapingCoordinator

logger = logging.getLogger(__name__)

@dataclass
class SmartOrchestrationTask:
    """Tâche d'orchestration simplifiée"""
    task_id: str
    urls: List[str]
    enable_llm_analysis: bool = False
    quality_threshold: float = 0.6
    timeout: int = 120

@dataclass
class SmartOrchestrationResult:
    """Résultat d'orchestration intelligent"""
    task_id: str
    status: str
    total_processing_time: float
    agents_used: List[str]
    results_summary: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    auto_recommendations: List[str]
    timestamp: str

class SmartMultiAgentOrchestrator:
    """Orchestrateur multi-agents avec intelligence automatique complète"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.orchestrator_id = f"smart_orchestrator_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Agents intelligents
        self.agents = {
            'smart_coordinator': SmartScrapingCoordinator(),
            'navigation': NavigationAgent(f"nav_{self.orchestrator_id}"),
            'analyzer': AnalyzerAgent(f"analyzer_{self.orchestrator_id}")
        }
        
        # Configuration d'intelligence automatique
        self.auto_config = {
            'strategy': 'intelligent_auto',
            'enable_navigation_discovery': True,
            'enable_quality_optimization': True,
            'enable_performance_learning': True,
            'fallback_strategy': 'resilient'
        }
        
        # Métriques de performance simplifiées
        self.performance_metrics = {
            'total_orchestrations': 0,
            'successful_orchestrations': 0,
            'avg_processing_time': 0.0,
            'avg_quality_score': 0.0
        }
        
        logger.info(f"Smart MultiAgentOrchestrator initialized: {self.orchestrator_id}")
    
    async def orchestrate_smart_task(self, task: SmartOrchestrationTask) -> SmartOrchestrationResult:
        """Orchestration intelligente automatique"""
        
        start_time = datetime.utcnow()
        logger.info(f"Starting smart orchestration: {task.task_id}")
        
        result = SmartOrchestrationResult(
            task_id=task.task_id,
            status='in_progress',
            total_processing_time=0.0,
            agents_used=[],
            results_summary={},
            quality_metrics={},
            auto_recommendations=[],
            timestamp=start_time.isoformat()
        )
        
        try:
            # PHASE 1: Découverte intelligente (optionnelle)
            discovered_urls = []
            if self.auto_config['enable_navigation_discovery'] and len(task.urls) <= 3:
                discovered_urls = await self._smart_navigation_phase(task.urls[:2])
                result.agents_used.append('navigation')
            
            # PHASE 2: Scraping intelligent coordonné
            all_urls = task.urls + discovered_urls[:5]  # Max 5 URLs découvertes
            scraping_results = await self._smart_scraping_phase(all_urls, task)
            result.agents_used.append('smart_coordinator')
            
            # PHASE 3: Analyse intelligente (si demandée)
            analysis_results = {}
            if task.enable_llm_analysis:
                analysis_results = await self._smart_analysis_phase(scraping_results, task)
                result.agents_used.append('analyzer')
            
            # PHASE 4: Synthèse intelligente automatique
            synthesis = self._synthesize_smart_results(scraping_results, analysis_results, discovered_urls)
            
            # Finalisation
            total_time = (datetime.utcnow() - start_time).total_seconds()
            result.total_processing_time = total_time
            result.status = 'completed'
            result.results_summary = synthesis['summary']
            result.quality_metrics = synthesis['quality']
            result.auto_recommendations = synthesis['recommendations']
            
            # Mise à jour des métriques
            self._update_performance_metrics(True, total_time, synthesis['quality'].get('overall_score', 0))
            
            logger.info(f"Smart orchestration completed: {task.task_id} in {total_time:.2f}s")
            return result
            
        except Exception as e:
            total_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Smart orchestration failed for {task.task_id}: {e}")
            
            result.status = 'failed'
            result.total_processing_time = total_time
            result.results_summary = {'error': str(e)}
            
            self._update_performance_metrics(False, total_time, 0)
            return result
    
    async def _smart_navigation_phase(self, base_urls: List[str]) -> List[str]:
        """Phase de navigation intelligente"""
        discovered = []
        
        try:
            for url in base_urls:
                # Assessment rapide d'abord
                assessment = await self.agents['navigation'].quick_site_assessment(url)
                
                if assessment.get('exploration_potential') in ['high', 'medium']:
                    # Exploration approfondie
                    exploration = await self.agents['navigation'].explore_site_intelligently(
                        url, max_depth=2, max_pages=10
                    )
                    
                    if exploration.data_rich_pages:
                        discovered.extend(exploration.data_rich_pages[:3])  # Top 3 par site
            
            logger.info(f"Navigation discovered {len(discovered)} promising URLs")
            return discovered
            
        except Exception as e:
            logger.warning(f"Navigation phase failed: {e}")
            return []
    
    async def _smart_scraping_phase(self, urls: List[str], task: SmartOrchestrationTask) -> Dict[str, Any]:
        """Phase de scraping intelligent coordonné"""
        scraping_results = {
            'successful': [],
            'failed': [],
            'total_processed': 0,
            'success_rate': 0,
            'processing_details': {}
        }
        
        try:
            # Scraping parallèle intelligent
            scraping_tasks = []
            for url in urls[:10]:  # Limiter à 10 URLs max
                task_coro = self._smart_scrape_single_url(url, task.enable_llm_analysis)
                scraping_tasks.append(task_coro)
            
            if scraping_tasks:
                results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    url = urls[i] if i < len(urls) else f"url_{i}"
                    
                    if isinstance(result, Exception):
                        scraping_results['failed'].append({
                            'url': url,
                            'error': str(result)
                        })
                    elif result and result.get('success'):
                        scraping_results['successful'].append(result)
                    else:
                        scraping_results['failed'].append({
                            'url': url,
                            'error': 'Scraping failed'
                        })
                
                scraping_results['total_processed'] = len(results)
                scraping_results['success_rate'] = len(scraping_results['successful']) / len(results)
                
                logger.info(f"Scraping completed: {len(scraping_results['successful'])}/{len(results)} successful")
            
            return scraping_results
            
        except Exception as e:
            logger.error(f"Scraping phase failed: {e}")
            return scraping_results
    
    async def _smart_scrape_single_url(self, url: str, enable_llm: bool) -> Optional[Dict[str, Any]]:
        """Scraping intelligent d'une URL"""
        try:
            result = self.agents['smart_coordinator'].scrape(
                url=url,
                enable_llm_analysis=enable_llm,
                quality_threshold=0.6,
                timeout=60
            )
            
            if result:
                return {
                    'url': url,
                    'success': True,
                    'content_length': len(result.raw_content) if result.raw_content else 0,
                    'structured_data': result.structured_data,
                    'metadata': result.metadata,
                    'strategy_used': result.metadata.get('smart_coordinator', {}).get('strategy_used', 'unknown')
                }
            else:
                return {
                    'url': url,
                    'success': False,
                    'error': 'No content extracted'
                }
                
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    async def _smart_analysis_phase(self, scraping_results: Dict[str, Any], 
                                   task: SmartOrchestrationTask) -> Dict[str, Any]:
        """Phase d'analyse intelligente"""
        analysis_results = {
            'analyses_performed': 0,
            'successful_analyses': 0,
            'analysis_summaries': [],
            'combined_insights': {}
        }
        
        try:
            successful_scraping = scraping_results.get('successful', [])
            
            for scraping_result in successful_scraping[:5]:  # Analyser max 5 résultats
                content = scraping_result.get('structured_data', {})
                raw_content = content.get('raw_content') if isinstance(content, dict) else None
                
                if not raw_content:
                    continue
                
                # Analyse intelligente
                analysis_data = {
                    'content': raw_content[:5000],
                    'source': scraping_result.get('url'),
                    'analysis_type': 'auto_detected'
                }
                
                analysis_result = self.agents['analyzer'].analyze_scraped_data(analysis_data)
                
                if analysis_result and analysis_result.confidence_score > 0.3:
                    analysis_results['successful_analyses'] += 1
                    analysis_results['analysis_summaries'].append({
                        'url': scraping_result.get('url'),
                        'category': analysis_result.economic_category,
                        'confidence': analysis_result.confidence_score,
                        'quality': analysis_result.quality_score,
                        'recommendations': analysis_result.auto_recommendations
                    })
                
                analysis_results['analyses_performed'] += 1
            
            # Synthèse des insights combinés
            if analysis_results['analysis_summaries']:
                analysis_results['combined_insights'] = self._combine_analysis_insights(
                    analysis_results['analysis_summaries']
                )
            
            logger.info(f"Analysis completed: {analysis_results['successful_analyses']}/{analysis_results['analyses_performed']} successful")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Analysis phase failed: {e}")
            return analysis_results
    
    def _combine_analysis_insights(self, summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine les insights d'analyse"""
        try:
            categories = [s['category'] for s in summaries]
            avg_confidence = sum(s['confidence'] for s in summaries) / len(summaries)
            avg_quality = sum(s['quality'] for s in summaries) / len(summaries)
            
            # Catégorie dominante
            most_common_category = max(set(categories), key=categories.count) if categories else 'general'
            
            # Recommandations combinées
            all_recommendations = []
            for summary in summaries:
                all_recommendations.extend(summary.get('recommendations', []))
            
            # Top recommandations (par fréquence)
            rec_frequency = {}
            for rec in all_recommendations:
                rec_frequency[rec] = rec_frequency.get(rec, 0) + 1
            
            top_recommendations = sorted(rec_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                'dominant_category': most_common_category,
                'average_confidence': avg_confidence,
                'average_quality': avg_quality,
                'sources_analyzed': len(summaries),
                'top_recommendations': [rec[0] for rec in top_recommendations],
                'category_distribution': {cat: categories.count(cat) for cat in set(categories)}
            }
            
        except Exception as e:
            logger.warning(f"Failed to combine insights: {e}")
            return {}
    
    def _synthesize_smart_results(self, scraping_results: Dict[str, Any], 
                                 analysis_results: Dict[str, Any], 
                                 discovered_urls: List[str]) -> Dict[str, Any]:
        """Synthèse intelligente automatique des résultats"""
        
        synthesis = {
            'summary': {},
            'quality': {},
            'recommendations': []
        }
        
        try:
            # Résumé des résultats
            synthesis['summary'] = {
                'urls_discovered': len(discovered_urls),
                'urls_scraped': scraping_results.get('total_processed', 0),
                'scraping_success_rate': scraping_results.get('success_rate', 0),
                'successful_extractions': len(scraping_results.get('successful', [])),
                'analyses_performed': analysis_results.get('analyses_performed', 0),
                'analysis_success_rate': (
                    analysis_results.get('successful_analyses', 0) / 
                    max(analysis_results.get('analyses_performed', 1), 1)
                )
            }
            
            # Métriques de qualité
            scraping_success_rate = scraping_results.get('success_rate', 0)
            analysis_avg_quality = analysis_results.get('combined_insights', {}).get('average_quality', 0)
            
            overall_quality = (scraping_success_rate + analysis_avg_quality) / 2
            
            synthesis['quality'] = {
                'overall_score': overall_quality,
                'scraping_quality': scraping_success_rate,
                'analysis_quality': analysis_avg_quality,
                'data_richness': len(scraping_results.get('successful', [])) / 10,
                'quality_level': (
                    'excellent' if overall_quality > 0.8 
                    else 'good' if overall_quality > 0.6 
                    else 'acceptable' if overall_quality > 0.4 
                    else 'poor'
                )
            }
            
            # Recommandations automatiques
            recommendations = []
            
            if scraping_success_rate > 0.8:
                recommendations.append("Extraction excellente - données fiables pour analyse")
            elif scraping_success_rate < 0.5:
                recommendations.append("Taux d'extraction faible - réviser les sources")
            
            if analysis_results.get('combined_insights'):
                insights = analysis_results['combined_insights']
                recommendations.extend(insights.get('top_recommendations', [])[:2])
                
                dominant_category = insights.get('dominant_category', 'general')
                if dominant_category != 'general':
                    recommendations.append(f"Focus sur {dominant_category} - spécialisation détectée")
            
            if len(discovered_urls) > 5:
                recommendations.append("Nombreuses sources découvertes - potentiel d'expansion")
            
            synthesis['recommendations'] = recommendations[:5]
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {
                'summary': {'error': str(e)},
                'quality': {'overall_score': 0, 'quality_level': 'unknown'},
                'recommendations': ['Erreur de synthèse - vérifier les logs']
            }
    
    def _update_performance_metrics(self, success: bool, processing_time: float, quality_score: float):
        """Mise à jour des métriques de performance"""
        try:
            self.performance_metrics['total_orchestrations'] += 1
            
            if success:
                self.performance_metrics['successful_orchestrations'] += 1
            
            # Mise à jour moyennes mobiles
            total = self.performance_metrics['total_orchestrations']
            
            current_avg_time = self.performance_metrics['avg_processing_time']
            self.performance_metrics['avg_processing_time'] = (
                (current_avg_time * (total - 1)) + processing_time
            ) / total
            
            if success and quality_score > 0:
                current_avg_quality = self.performance_metrics['avg_quality_score']
                self.performance_metrics['avg_quality_score'] = (
                    (current_avg_quality * (total - 1)) + quality_score
                ) / total
            
        except Exception as e:
            logger.warning(f"Performance metrics update failed: {e}")
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Statut de l'orchestrateur intelligent"""
        success_rate = 0
        if self.performance_metrics['total_orchestrations'] > 0:
            success_rate = (
                self.performance_metrics['successful_orchestrations'] / 
                self.performance_metrics['total_orchestrations']
            )
        
        return {
            'orchestrator_id': self.orchestrator_id,
            'orchestrator_type': 'SmartMultiAgentOrchestrator',
            'version': '2.0_smart_auto',
            'status': 'active',
            'agents_available': list(self.agents.keys()),
            'auto_config': self.auto_config,
            'performance_metrics': {
                **self.performance_metrics,
                'success_rate': success_rate
            },
            'capabilities': [
                'intelligent_auto_orchestration',
                'smart_navigation_discovery',
                'coordinated_intelligent_scraping',
                'automatic_analysis',
                'performance_optimization',
                'zero_configuration_required'
            ]
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Rapport de performance intelligent"""
        if self.performance_metrics['total_orchestrations'] == 0:
            return {'message': 'No orchestrations performed yet'}
        
        try:
            metrics = self.performance_metrics
            success_rate = metrics['successful_orchestrations'] / metrics['total_orchestrations']
            
            return {
                'summary': {
                    'total_orchestrations': metrics['total_orchestrations'],
                    'success_rate': success_rate,
                    'average_processing_time': metrics['avg_processing_time'],
                    'average_quality_score': metrics['avg_quality_score']
                },
                'performance_level': (
                    'excellent' if success_rate > 0.9 and metrics['avg_quality_score'] > 0.8
                    else 'good' if success_rate > 0.7 and metrics['avg_quality_score'] > 0.6
                    else 'needs_improvement'
                ),
                'intelligence_status': 'fully_automatic',
                'recommendations': self._generate_orchestrator_recommendations(success_rate, metrics)
            }
            
        except Exception as e:
            logger.error(f"Performance report generation failed: {e}")
            return {'error': str(e)}
    
    def _generate_orchestrator_recommendations(self, success_rate: float, metrics: Dict[str, Any]) -> List[str]:
        """Génération de recommandations pour l'orchestrateur"""
        recommendations = []
        
        if success_rate > 0.9:
            recommendations.append("Performance excellente - système optimal")
        elif success_rate > 0.7:
            recommendations.append("Bonne performance - optimisations mineures possibles")
        else:
            recommendations.append("Performance à améliorer - révision nécessaire")
        
        if metrics['avg_processing_time'] > 120:
            recommendations.append("Temps de traitement élevé - considérer plus de workers")
        elif metrics['avg_processing_time'] < 30:
            recommendations.append("Traitement rapide - capacité pour plus de sources")
        
        if metrics['avg_quality_score'] < 0.5:
            recommendations.append("Qualité faible - améliorer la sélection des sources")
        
        return recommendations
    
    def configure_intelligence(self, **config_updates):
        """Configuration de l'intelligence automatique"""
        valid_keys = self.auto_config.keys()
        updated = []
        
        for key, value in config_updates.items():
            if key in valid_keys:
                self.auto_config[key] = value
                updated.append(key)
                logger.info(f"Updated orchestrator config: {key} = {value}")
            else:
                logger.warning(f"Invalid orchestrator config key: {key}")
        
        return {
            'updated_keys': updated,
            'current_config': self.auto_config
        }
    
    def reset_performance_metrics(self):
        """Reset des métriques de performance"""
        self.performance_metrics = {
            'total_orchestrations': 0,
            'successful_orchestrations': 0,
            'avg_processing_time': 0.0,
            'avg_quality_score': 0.0
        }
        logger.info(f"Performance metrics reset for {self.orchestrator_id}")
    
    async def cleanup_resources(self):
        """Nettoyage des ressources de l'orchestrateur"""
        try:
            if hasattr(self.agents.get('navigation'), 'clear_navigation_history'):
                self.agents['navigation'].clear_navigation_history()
            
            logger.info(f"Resources cleaned up for orchestrator: {self.orchestrator_id}")
            
        except Exception as e:
            logger.error(f"Resource cleanup failed: {e}")
    
    # MÉTHODES SIMPLIFIÉES POUR L'API
    
    async def simple_orchestrate(self, urls: List[str], enable_llm: bool = False) -> Dict[str, Any]:
        """Orchestration simplifiée pour l'API"""
        task = SmartOrchestrationTask(
            task_id=f"simple_{datetime.utcnow().strftime('%H%M%S')}",
            urls=urls,
            enable_llm_analysis=enable_llm,
            quality_threshold=0.6,
            timeout=120
        )
        
        result = await self.orchestrate_smart_task(task)
        
        return {
            'task_id': result.task_id,
            'status': result.status,
            'processing_time': result.total_processing_time,
            'agents_used': result.agents_used,
            'summary': result.results_summary,
            'quality': result.quality_metrics,
            'recommendations': result.auto_recommendations,
            'intelligent_orchestration': True
        }
    
    def get_simple_status(self) -> Dict[str, Any]:
        """Statut simplifié pour l'API"""
        status = self.get_orchestrator_status()
        
        return {
            'orchestrator_ready': True,
            'intelligence_mode': 'automatic',
            'agents_available': len(status['agents_available']),
            'success_rate': status['performance_metrics']['success_rate'],
            'total_operations': status['performance_metrics']['total_orchestrations']
        }
    
    def export_orchestration_data(self) -> Dict[str, Any]:
        """Export des données d'orchestration"""
        return {
            'orchestrator_id': self.orchestrator_id,
            'orchestrator_type': 'SmartMultiAgentOrchestrator', 
            'version': '2.0_smart_auto',
            'auto_config': self.auto_config,
            'performance_metrics': self.performance_metrics,
            'agents_config': {
                agent_name: agent.get_smart_status() if hasattr(agent, 'get_smart_status') 
                else {'available': True} for agent_name, agent in self.agents.items()
            },
            'export_timestamp': datetime.utcnow().isoformat()
        }