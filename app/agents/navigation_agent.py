"""
Navigation Agent Complet et Optimisé pour Intelligence Automatique
Exploration intelligente de sites avec détection automatique de données riches
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor
import re

logger = logging.getLogger(__name__)

@dataclass
class NavigationResult:
    """Résultat de navigation intelligente"""
    discovered_urls: List[str]
    data_rich_pages: List[str]
    page_categories: Dict[str, str]
    navigation_depth: int
    exploration_time: float
    confidence_scores: Dict[str, float]
    exploration_metadata: Dict[str, Any]

class NavigationAgent:
    """Agent de navigation intelligente pour découverte automatique"""
    
    def __init__(self, agent_id: str = "smart_navigator_001"):
        self.agent_id = agent_id
        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        
        # Configuration optimisée
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; TunisianEconomicBot/2.0)'
        })
        
        # Patterns tunisiens optimisés
        self.tunisian_data_indicators = [
            # Mots-clés économiques généraux
            'statistique', 'données', 'indicateur', 'tableau', 'rapport',
            'publication', 'chiffres', 'analyse', 'enquête', 'résultats',
            # Spécifiques Tunisie
            'tunisie', 'tunisien', 'économie', 'social', 'démographie',
            'pib', 'inflation', 'emploi', 'chômage', 'commerce',
            # Institutions
            'bct', 'ins', 'banque centrale', 'institut statistique',
            # Secteurs
            'industrie', 'export', 'import', 'finance', 'monétaire'
        ]
        
        # Patterns à exclure
        self.excluded_patterns = [
            'contact', 'about', 'login', 'admin', 'search', 'sitemap',
            'css', 'js', 'img', 'pdf', 'doc', 'media', 'archive',
            'facebook', 'twitter', 'linkedin', 'youtube', 'instagram'
        ]
        
        # Patterns prioritaires
        self.priority_patterns = [
            'statistique', 'données', 'indicateur', 'rapport', 'publication',
            'économie', 'finance', 'social', 'démographie', 'emploi',
            'pib', 'inflation', 'commerce', 'industrie'
        ]
        
        # Métriques de performance
        self.performance_metrics = {
            'total_explorations': 0,
            'successful_discoveries': 0,
            'avg_discovery_rate': 0.0,
            'avg_exploration_time': 0.0
        }
        
        logger.info(f"Smart NavigationAgent initialized: {self.agent_id}")
    
    async def explore_site_intelligently(self, base_url: str, max_depth: int = 3, 
                                       max_pages: int = 50) -> NavigationResult:
        """Exploration intelligente automatique d'un site"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting smart exploration: {base_url} (depth: {max_depth}, max_pages: {max_pages})")
            
            # Réinitialiser l'état
            self.visited_urls.clear()
            
            discovered_urls = []
            data_rich_pages = []
            page_categories = {}
            confidence_scores = {}
            exploration_stats = {
                'pages_analyzed': 0,
                'data_pages_found': 0,
                'category_distribution': {},
                'errors_encountered': 0,
                'avg_content_score': 0
            }
            
            # Exploration récursive intelligente
            await self._smart_recursive_explore(
                base_url, max_depth, 0, discovered_urls, 
                data_rich_pages, page_categories, confidence_scores,
                exploration_stats, max_pages
            )
            
            exploration_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Trier par score de confiance
            data_rich_pages.sort(key=lambda url: confidence_scores.get(url, 0), reverse=True)
            
            # Finaliser les statistiques
            if discovered_urls:
                exploration_stats['avg_content_score'] = sum(confidence_scores.values()) / len(confidence_scores)
                exploration_stats['data_pages_found'] = len(data_rich_pages)
                
                # Distribution des catégories
                for category in page_categories.values():
                    exploration_stats['category_distribution'][category] = exploration_stats['category_distribution'].get(category, 0) + 1
            
            # Mise à jour des métriques de performance
            self._update_performance_metrics(True, len(data_rich_pages), exploration_time)
            
            logger.info(f"Smart exploration completed: {len(discovered_urls)} URLs, {len(data_rich_pages)} data-rich pages in {exploration_time:.2f}s")
            
            return NavigationResult(
                discovered_urls=discovered_urls[:max_pages],
                data_rich_pages=data_rich_pages[:20],  # Top 20 pages prometteuses
                page_categories=page_categories,
                navigation_depth=max_depth,
                exploration_time=exploration_time,
                confidence_scores=confidence_scores,
                exploration_metadata=exploration_stats
            )
            
        except Exception as e:
            exploration_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_performance_metrics(False, 0, exploration_time)
            logger.error(f"Smart exploration failed for {base_url}: {e}")
            
            return NavigationResult(
                discovered_urls=[], data_rich_pages=[], page_categories={},
                navigation_depth=0, exploration_time=exploration_time, confidence_scores={},
                exploration_metadata={'error': str(e)}
            )
    
    async def _smart_recursive_explore(self, url: str, max_depth: int, current_depth: int,
                                      discovered_urls: List[str], data_rich_pages: List[str],
                                      page_categories: Dict[str, str], confidence_scores: Dict[str, float],
                                      exploration_stats: Dict[str, Any], max_pages: int):
        """Exploration récursive intelligente"""
        
        # Conditions d'arrêt intelligentes
        if (current_depth >= max_depth or 
            url in self.visited_urls or 
            len(discovered_urls) >= max_pages):
            return
        
        self.visited_urls.add(url)
        discovered_urls.append(url)
        exploration_stats['pages_analyzed'] += 1
        
        try:
            # Récupération avec timeout optimisé
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                exploration_stats['errors_encountered'] += 1
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Analyse intelligente du contenu
            content_score = self._smart_analyze_page_content(soup, url)
            confidence_scores[url] = content_score
            
            # Classification automatique
            page_category = self._smart_classify_page(soup, url)
            page_categories[url] = page_category
            
            # Ajout si riche en données (seuil intelligent)
            if content_score > 0.6:
                data_rich_pages.append(url)
                logger.info(f"Data-rich page discovered: {url} (score: {content_score:.2f}, category: {page_category})")
            
            # Extraction et exploration des liens (si profondeur permise)
            if current_depth < max_depth - 1:
                links = self._extract_smart_links(soup, url)
                priority_links = self._prioritize_smart_links(links, url)
                
                # Limiter intelligemment les liens à explorer
                links_to_explore = priority_links[:min(5, max_pages - len(discovered_urls))]
                
                for link in links_to_explore:
                    await asyncio.sleep(0.5)  # Respect du serveur
                    await self._smart_recursive_explore(
                        link, max_depth, current_depth + 1,
                        discovered_urls, data_rich_pages, page_categories, 
                        confidence_scores, exploration_stats, max_pages
                    )
        
        except Exception as e:
            logger.warning(f"Failed to explore {url}: {e}")
            exploration_stats['errors_encountered'] += 1
    
    def _smart_analyze_page_content(self, soup: BeautifulSoup, url: str) -> float:
        """Analyse intelligente de la richesse en données"""
        score = 0.0
        text_content = soup.get_text().lower()
        
        # 1. Tableaux (fort indicateur de données)
        tables = soup.find_all('table')
        if tables:
            score += 0.3
            # Bonus pour tableaux avec données numériques
            for table in tables:
                table_text = table.get_text()
                if re.search(r'\d+[.,]?\d*', table_text):
                    score += 0.2
                    break
        
        # 2. Mots-clés tunisiens spécialisés
        keyword_matches = sum(1 for keyword in self.tunisian_data_indicators if keyword in text_content)
        score += min(keyword_matches * 0.04, 0.3)
        
        # 3. Densité numérique (indicateurs économiques)
        numbers = re.findall(r'\b\d+[.,]?\d*\b', text_content)
        if len(numbers) > 30:
            score += 0.25
        elif len(numbers) > 15:
            score += 0.15
        elif len(numbers) > 5:
            score += 0.1
        
        # 4. URLs suggestives pour l'économie tunisienne
        tunisian_url_keywords = ['stat', 'données', 'rapport', 'publication', 'indicateur', 'économie', 'pib', 'emploi']
        if any(keyword in url.lower() for keyword in tunisian_url_keywords):
            score += 0.2
        
        # 5. Structure de données économiques
        economic_structures = soup.find_all(['ul', 'ol', 'dl'])
        if len(economic_structures) > 3:
            score += 0.1
        
        # 6. Termes économiques spécialisés
        specialized_terms = ['inflation', 'pib', 'chômage', 'exportation', 'importation', 'balance', 'taux', 'indice']
        specialized_matches = sum(1 for term in specialized_terms if term in text_content)
        score += min(specialized_matches * 0.05, 0.2)
        
        # 7. Mentions institutionnelles tunisiennes
        institutions = ['bct', 'banque centrale', 'ins', 'institut national', 'ministère', 'gouvernement']
        institutional_matches = sum(1 for inst in institutions if inst in text_content)
        if institutional_matches > 0:
            score += 0.15
        
        return min(score, 1.0)
    
    def _smart_classify_page(self, soup: BeautifulSoup, url: str) -> str:
        """Classification intelligente par type de page"""
        text_content = soup.get_text().lower()
        url_lower = url.lower()
        
        # Classification spécialisée pour l'économie tunisienne
        if any(term in text_content for term in ['banque centrale', 'bct', 'monétaire', 'taux directeur']):
            return 'monetary_financial'
        elif any(term in text_content for term in ['ins', 'statistique', 'recensement', 'démographie']):
            return 'statistical_demographic'
        elif any(term in text_content for term in ['industrie', 'production', 'manufacturier', 'secteur']):
            return 'industrial_production'
        elif any(term in text_content for term in ['emploi', 'chômage', 'travail', 'social', 'salaire']):
            return 'employment_social'
        elif any(term in text_content for term in ['commerce', 'export', 'import', 'échange', 'balance']):
            return 'trade_commerce'
        elif any(term in text_content for term in ['actualité', 'news', 'communiqué', 'presse']):
            return 'news_communication'
        elif any(term in url_lower for term in ['publication', 'rapport', 'document']):
            return 'publication_document'
        elif any(term in url_lower for term in ['api', 'data', 'json', 'xml']):
            return 'api_data'
        else:
            return 'general_economic'
    
    def _extract_smart_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extraction intelligente de liens pertinents"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            try:
                # Construire l'URL complète
                full_url = urljoin(base_url, href)
                parsed_url = urlparse(full_url)
                
                # Garder seulement les liens du même domaine
                if parsed_url.netloc != base_domain:
                    continue
                
                # Exclure les ancres et paramètres complexes
                if '#' in href or (href.count('?') > 0 and href.count('&') > 3):
                    continue
                
                # Exclure les patterns non pertinents
                if any(pattern in full_url.lower() for pattern in self.excluded_patterns):
                    continue
                
                # Exclure les fichiers binaires
                if any(full_url.lower().endswith(ext) for ext in ['.pdf', '.doc', '.xls', '.zip', '.jpg', '.png', '.gif']):
                    continue
                
                links.append(full_url)
                
            except Exception as e:
                logger.debug(f"Error processing link {href}: {e}")
                continue
        
        return list(set(links))  # Supprimer doublons
    
    def _prioritize_smart_links(self, links: List[str], base_url: str) -> List[str]:
        """Priorisation intelligente des liens"""
        priority_links = []
        normal_links = []
        
        for link in links:
            link_lower = link.lower()
            
            # Haute priorité pour mots-clés économiques pertinents
            if any(keyword in link_lower for keyword in self.priority_patterns):
                priority_links.append(link)
            else:
                normal_links.append(link)
        
        # Retourner les liens prioritaires en premier
        return priority_links + normal_links
    
    async def quick_site_assessment(self, url: str) -> Dict[str, Any]:
        """Évaluation rapide et intelligente d'un site"""
        try:
            logger.info(f"Quick smart assessment for: {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'error': f'HTTP {response.status_code}', 'accessible': False}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Analyse rapide mais intelligente
            content_score = self._smart_analyze_page_content(soup, url)
            page_category = self._smart_classify_page(soup, url)
            links = self._extract_smart_links(soup, url)
            priority_links = self._prioritize_smart_links(links, url)
            
            # Évaluation du potentiel d'exploration
            exploration_potential = 'high' if content_score > 0.7 else 'medium' if content_score > 0.4 else 'low'
            recommended_depth = 3 if len(priority_links) > 10 else 2 if len(priority_links) > 5 else 1
            
            assessment = {
                'accessible': True,
                'content_score': content_score,
                'category': page_category,
                'total_links_found': len(links),
                'priority_links_count': len(priority_links),
                'exploration_potential': exploration_potential,
                'recommended_depth': recommended_depth,
                'tunisian_context_detected': self._detect_tunisian_context(soup),
                'assessment_timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Quick assessment completed: {url} (score: {content_score:.2f}, potential: {exploration_potential})")
            return assessment
            
        except Exception as e:
            logger.error(f"Quick assessment failed for {url}: {e}")
            return {'error': str(e), 'accessible': False}
    
    def _detect_tunisian_context(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Détection du contexte tunisien"""
        text_content = soup.get_text().lower()
        
        tunisian_indicators = {
            'country_refs': ['tunisie', 'tunisia', 'tunisien', 'tunisian'],
            'cities': ['tunis', 'sfax', 'sousse', 'kairouan', 'bizerte'],
            'institutions': ['bct', 'ins', 'gouvernement tunisien', 'république tunisienne'],
            'currency': ['dinar', 'tnd', 'millimes'],
            'language': ['arabe', 'arabic', 'français', 'french']
        }
        
        context_score = 0
        detected_elements = {}
        
        for category, indicators in tunisian_indicators.items():
            matches = [indicator for indicator in indicators if indicator in text_content]
            if matches:
                detected_elements[category] = matches[:3]  # Limiter à 3
                context_score += len(matches)
        
        return {
            'context_score': min(context_score / 10, 1.0),  # Normaliser
            'detected_elements': detected_elements,
            'is_tunisian_site': context_score > 2
        }
    
    def _update_performance_metrics(self, success: bool, discoveries: int, exploration_time: float):
        """Mise à jour intelligente des métriques"""
        try:
            self.performance_metrics['total_explorations'] += 1
            
            if success and discoveries > 0:
                self.performance_metrics['successful_discoveries'] += 1
                
                # Moyenne mobile du taux de découverte
                total = self.performance_metrics['total_explorations']
                current_avg = self.performance_metrics['avg_discovery_rate']
                discovery_rate = discoveries / 10  # Normaliser sur 10
                
                self.performance_metrics['avg_discovery_rate'] = (
                    (current_avg * (total - 1)) + discovery_rate
                ) / total
            
            # Moyenne mobile du temps d'exploration
            total = self.performance_metrics['total_explorations']
            current_avg_time = self.performance_metrics['avg_exploration_time']
            self.performance_metrics['avg_exploration_time'] = (
                (current_avg_time * (total - 1)) + exploration_time
            ) / total
            
        except Exception as e:
            logger.warning(f"Performance metrics update failed: {e}")
    
    # MÉTHODES DE STATUT ET CONFIGURATION
    
    def get_navigation_status(self) -> Dict[str, Any]:
        """Statut intelligent de l'agent de navigation"""
        success_rate = 0
        if self.performance_metrics['total_explorations'] > 0:
            success_rate = self.performance_metrics['successful_discoveries'] / self.performance_metrics['total_explorations']
        
        return {
            'agent_id': self.agent_id,
            'agent_type': 'SmartNavigationAgent',
            'version': '2.0_intelligent_auto',
            'total_urls_visited': len(self.visited_urls),
            'performance_metrics': {
                **self.performance_metrics,
                'success_rate': success_rate
            },
            'tunisian_indicators': len(self.tunisian_data_indicators),
            'capabilities': [
                'intelligent_site_exploration',
                'tunisian_context_detection',
                'automatic_content_scoring',
                'smart_page_categorization',
                'priority_link_detection',
                'performance_optimization'
            ],
            'configuration': {
                'max_concurrent_requests': 5,
                'request_timeout': 10,
                'tunisian_optimization': True,
                'intelligent_filtering': True
            }
        }
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Analytiques de performance détaillées"""
        if self.performance_metrics['total_explorations'] == 0:
            return {'message': 'No explorations performed yet'}
        
        try:
            metrics = self.performance_metrics
            success_rate = metrics['successful_discoveries'] / metrics['total_explorations']
            
            return {
                'summary': {
                    'total_explorations': metrics['total_explorations'],
                    'success_rate': success_rate,
                    'average_discovery_rate': metrics['avg_discovery_rate'],
                    'average_exploration_time': metrics['avg_exploration_time']
                },
                'performance_level': (
                    'excellent' if success_rate > 0.8 and metrics['avg_discovery_rate'] > 0.6
                    else 'good' if success_rate > 0.6 and metrics['avg_discovery_rate'] > 0.4
                    else 'needs_improvement'
                ),
                'intelligence_status': 'fully_automatic',
                'tunisian_optimization': True,
                'recommendations': self._generate_navigation_recommendations(success_rate, metrics)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate navigation analytics: {e}")
            return {'error': str(e)}
    
    def _generate_navigation_recommendations(self, success_rate: float, metrics: Dict[str, Any]) -> List[str]:
        """Génération de recommandations de navigation"""
        recommendations = []
        
        if success_rate > 0.8:
            recommendations.append("Performance de navigation excellente - système optimisé")
        elif success_rate > 0.6:
            recommendations.append("Bonne performance - optimisations mineures possibles")
        else:
            recommendations.append("Performance de navigation à améliorer")
        
        if metrics['avg_discovery_rate'] < 0.3:
            recommendations.append("Taux de découverte faible - réviser les patterns de détection")
        
        if metrics['avg_exploration_time'] > 60:
            recommendations.append("Temps d'exploration élevé - optimiser la profondeur")
        elif metrics['avg_exploration_time'] < 10:
            recommendations.append("Exploration rapide - capacité pour plus de profondeur")
        
        return recommendations
    
    def clear_navigation_history(self):
        """Nettoyage de l'historique de navigation"""
        self.visited_urls.clear()
        logger.info(f"Navigation history cleared for {self.agent_id}")
    
    def reset_performance_metrics(self):
        """Reset des métriques de performance"""
        self.performance_metrics = {
            'total_explorations': 0,
            'successful_discoveries': 0,
            'avg_discovery_rate': 0.0,
            'avg_exploration_time': 0.0
        }
        logger.info(f"Performance metrics reset for {self.agent_id}")
    
    def configure_navigation(self, **config_updates):
        """Configuration de la navigation intelligente"""
        # Patterns configurables
        configurable_params = {
            'priority_patterns': self.priority_patterns,
            'excluded_patterns': self.excluded_patterns,
            'tunisian_data_indicators': self.tunisian_data_indicators
        }
        
        updated = []
        for key, value in config_updates.items():
            if key in configurable_params and isinstance(value, list):
                setattr(self, key, value)
                updated.append(key)
                logger.info(f"Updated navigation config: {key}")
            else:
                logger.warning(f"Invalid navigation config key: {key}")
        
        return {
            'updated_keys': updated,
            'current_patterns': {
                'priority_count': len(self.priority_patterns),
                'excluded_count': len(self.excluded_patterns),
                'indicators_count': len(self.tunisian_data_indicators)
            }
        }
    
    def export_navigation_data(self) -> Dict[str, Any]:
        """Export des données de navigation"""
        return {
            'agent_id': self.agent_id,
            'agent_type': 'SmartNavigationAgent',
            'version': '2.0_intelligent_auto',
            'performance_metrics': self.performance_metrics,
            'patterns': {
                'tunisian_indicators': self.tunisian_data_indicators,
                'priority_patterns': self.priority_patterns,
                'excluded_patterns': self.excluded_patterns
            },
            'visited_urls_count': len(self.visited_urls),
            'export_timestamp': datetime.utcnow().isoformat()
        }