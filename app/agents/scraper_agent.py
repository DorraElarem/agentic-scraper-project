from app.scrapers.traditional import TunisianWebScraper
from app.scrapers.intelligent import IntelligentScraper
from app.models.schemas import ScrapeRequest, ScrapedContent, AnalysisType
from app.agents.analyzer_agent import AnalyzerAgent
from typing import Optional, Dict, Any
import logging
from app.config.settings import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class ScrapingResult:
    """Classe pour encapsuler les résultats de scraping"""
    
    def __init__(
        self,
        url: str,
        content: Optional[ScrapedContent] = None,
        status_code: int = 200,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
        analysis_type: AnalysisType = AnalysisType.STANDARD,
        llm_analysis: Optional[Dict[str, Any]] = None,
        timestamp: datetime = None
    ):
        self.url = url
        self.content = content
        self.status_code = status_code
        self.metadata = metadata or {}
        self.success = success
        self.error = error
        self.analysis_type = analysis_type
        self.llm_analysis = llm_analysis or {}
        self.timestamp = timestamp or datetime.utcnow()

    def dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire"""
        return {
            'url': self.url,
            'content': self.content.dict() if self.content else None,
            'status_code': self.status_code,
            'metadata': self.metadata,
            'success': self.success,
            'error': self.error,
            'analysis_type': self.analysis_type.value,
            'llm_analysis': self.llm_analysis,
            'timestamp': self.timestamp.isoformat()
        }

class ScraperAgent:
    """Agent principal de scraping avec support multi-mode"""
    
    def __init__(self, name: str = "default_scraper"):
        self.name = name
        self.traditional_scraper = TunisianWebScraper()
        self.intelligent_scraper = IntelligentScraper()
        self.analyzer = AnalyzerAgent() if settings.ENABLE_LLM_ANALYSIS else None
        logger.info(f"Initialized ScraperAgent: {self.name} (LLM: {bool(self.analyzer)})")

    def scrape(self, request: ScrapeRequest) -> ScrapingResult:
        """
        Méthode principale de scraping avec gestion des 3 modes d'analyse
        """
        try:
            if not request.urls:
                raise ValueError("No URLs provided in ScrapeRequest")
            
            target_url = request.urls[0]
            logger.info(f"Starting scraping for URL: {target_url} with analysis_type: {request.analysis_type}")

            # 🔧 NOUVEAU: Extraire enable_llm_analysis de la requête
            enable_llm = getattr(request, 'enable_llm_analysis', False)
            logger.info(f"LLM Analysis: {'Enabled' if enable_llm else 'Disabled'}")

            # ===============================
            # MODE STANDARD : Scraping de base uniquement
            # ===============================
            if request.analysis_type == AnalysisType.STANDARD:
                content = self.traditional_scraper.scrape(target_url)
                method = "traditional"
                llm_analysis = {}  # Pas de LLM en mode standard
                
                logger.info(f"Standard scraping completed for {target_url}")

            # ===============================
            # MODE ADVANCED : Scraping intelligent + LLM complet
            # ===============================
            elif request.analysis_type == AnalysisType.ADVANCED:
                # 🔧 CORRIGÉ: Passer enable_llm_analysis au scraper intelligent
                content = self.intelligent_scraper.scrape_with_analysis(target_url, enable_llm_analysis=enable_llm)
                method = "intelligent"

                # Fallback sur traditionnel si intelligent échoue
                if not content:
                    logger.warning(f"Intelligent scraping failed for {target_url}, falling back to traditional")
                    content = self.traditional_scraper.scrape(target_url)
                    method = "traditional_fallback"

                # 🔧 CORRIGÉ: Analyse LLM seulement si enable_llm=True ET analyzer disponible
                llm_analysis = {}
                if enable_llm and self.analyzer and content and content.raw_content:
                    logger.info(f"Starting LLM analysis for {target_url}")
                    llm_analysis = self._perform_llm_analysis(
                        content.raw_content,
                        request.analysis_type,
                        analysis_depth="complete"
                    )
                    logger.info(f"LLM analysis completed with keys: {list(llm_analysis.keys())}")
                elif not enable_llm:
                    logger.info(f"LLM analysis disabled for {target_url}")
                    llm_analysis = {
                        "message": "Analyse LLM désactivée par l'utilisateur",
                        "llm_status": "disabled_by_user"
                    }

            # ===============================
            # MODE CUSTOM : Analyse personnalisée
            # ===============================
            elif request.analysis_type == AnalysisType.CUSTOM:
                # 🔧 CORRIGÉ: Passer enable_llm_analysis au scraper intelligent
                content = self.intelligent_scraper.scrape_with_analysis(target_url, enable_llm_analysis=enable_llm)
                method = "intelligent_custom"

                if not content:
                    logger.warning(f"Intelligent scraping failed for {target_url}, falling back to traditional")
                    content = self.traditional_scraper.scrape(target_url)
                    method = "traditional_fallback"

                # 🔧 CORRIGÉ: Analyse LLM avec paramètres personnalisés seulement si enable_llm=True
                llm_analysis = {}
                if enable_llm and self.analyzer and content and content.raw_content:
                    custom_params = request.parameters or {}
                    logger.info(f"Starting custom LLM analysis for {target_url} with params: {list(custom_params.keys())}")
                    llm_analysis = self._perform_llm_analysis(
                        content.raw_content,
                        request.analysis_type,
                        analysis_depth="custom",
                        custom_parameters=custom_params
                    )
                elif not enable_llm:
                    logger.info(f"Custom LLM analysis disabled for {target_url}")
                    llm_analysis = {
                        "message": "Analyse LLM personnalisée désactivée par l'utilisateur",
                        "llm_status": "disabled_by_user"
                    }

            else:
                raise ValueError(f"Unknown analysis_type: {request.analysis_type}")

            # ===============================
            # CONSTRUCTION DU RÉSULTAT
            # ===============================
            if content:
                logger.info(f"Scraping successful for {target_url} using method: {method}")
                return ScrapingResult(
                    url=target_url,
                    content=content,
                    status_code=200,
                    metadata={
                        'method': method,
                        'analysis_type': request.analysis_type.value,
                        'llm_enabled': enable_llm,  # 🔧 CORRIGÉ: Utiliser enable_llm au lieu de bool(llm_analysis)
                        'content_length': len(content.raw_content) if content.raw_content else 0,
                        'structured_data_keys': list(content.structured_data.keys()) if content.structured_data else []
                    },
                    analysis_type=request.analysis_type,
                    llm_analysis=llm_analysis
                )

            logger.error(f"All scraping methods failed for {target_url}")
            return ScrapingResult(
                url=target_url,
                content=None,
                status_code=500,
                metadata={'error': 'All scraping methods failed'},
                success=False,
                error='All scraping methods failed',
                analysis_type=request.analysis_type
            )

        except Exception as e:
            target_url = request.urls[0] if request.urls else 'unknown_url'
            logger.error(f"Scraping failed for {target_url}: {str(e)}", exc_info=True)
            return ScrapingResult(
                url=target_url,
                content=None,
                status_code=500,
                metadata={'error': str(e), 'exception_type': type(e).__name__},
                success=False,
                error=str(e),
                analysis_type=getattr(request, 'analysis_type', AnalysisType.STANDARD)
            )

    def _perform_llm_analysis(self, raw_content: str, analysis_type: AnalysisType, 
                             analysis_depth: str = "standard", 
                             custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Effectue l'analyse LLM avec gestion d'erreurs robuste
        """
        try:
            if not self.analyzer:
                logger.warning("LLM analyzer not configured")
                return {"error": "analyzer_not_configured"}
            
            if not raw_content or len(raw_content) < 50:
                logger.warning("Insufficient content for LLM analysis")
                return {"error": "insufficient_content", "content_length": len(raw_content) if raw_content else 0}

            # Déterminer la catégorie d'analyse selon l'URL et le contenu
            analysis_category = self._determine_analysis_category(raw_content)
            
            # Préparer les données pour l'analyzer
            analyzer_data = {
                "content": raw_content[:10000],  # Limiter la taille pour éviter les timeouts
                "analysis_type": analysis_category,
                "source": self.name,
                "depth": analysis_depth,
                "request_timestamp": datetime.utcnow().isoformat()
            }
        
            # Ajouter paramètres personnalisés si mode CUSTOM
            if custom_parameters:
                analyzer_data.update(custom_parameters)
                logger.debug(f"Added custom parameters: {list(custom_parameters.keys())}")

            # Appeler l'analyzer avec gestion d'erreur et timeout
            logger.info(f"Starting LLM analysis with category: {analysis_category}")
            start_time = datetime.utcnow()
            
            result = self.analyzer.analyze_scraped_data(analyzer_data)
            
            analysis_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"LLM analysis completed in {analysis_time:.2f}s")

            if result and hasattr(result, 'insights'):
                logger.info(f"LLM analysis successful with confidence: {result.confidence_score}")
                return {
                    "analysis_category": analysis_category,
                    "insights": result.insights,
                    "confidence_score": result.confidence_score,
                    "processing_time": result.processing_time,
                    "analysis_depth": analysis_depth,
                    "total_analysis_time": analysis_time,
                    "analyzer_id": result.analysis_id if hasattr(result, 'analysis_id') else None
                }
            else:
                logger.warning("LLM analysis returned empty or invalid result")
                return {
                    "error": "empty_analysis_result",
                    "analysis_time": analysis_time,
                    "result_type": type(result).__name__ if result else "None"
                }

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "exception_type": type(e).__name__,
                "analysis_category": analysis_category if 'analysis_category' in locals() else "unknown"
            }

    def _determine_analysis_category(self, content: str) -> str:
        """
        Détermine la catégorie d'analyse basée sur le contenu
        """
        try:
            content_lower = content.lower()
            
            # Banque Centrale - données monétaires et financières
            if any(term in content_lower for term in ['bct', 'banque centrale', 'monétaire', 'taux directeur', 'inflation']):
                return "economic"
            
            # INS - données statistiques
            elif any(term in content_lower for term in ['ins', 'statistique', 'population', 'démographie', 'recensement']):
                return "statistical"
            
            # Industrie - données sectorielles
            elif any(term in content_lower for term in ['industrie', 'production', 'manufacturier', 'secteur']):
                return "industrial"
            
            # Commerce et échanges
            elif any(term in content_lower for term in ['export', 'import', 'commerce', 'échange']):
                return "trade"
            
            # Données financières générales
            elif any(term in content_lower for term in ['pib', 'croissance', 'économique', 'financier']):
                return "economic"
            
            else:
                return "general"
                
        except Exception as e:
            logger.warning(f"Error determining analysis category: {e}")
            return "general"

    def get_scraper_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'agent scraper"""
        return {
            "agent_name": self.name,
            "scrapers_available": {
                "traditional": True,
                "intelligent": True
            },
            "llm_analysis_enabled": bool(self.analyzer),
            "supported_analysis_types": [t.value for t in AnalysisType],
            "settings": {
                "default_delay": settings.DEFAULT_DELAY,
                "request_timeout": settings.REQUEST_TIMEOUT,
                "max_retries": settings.MAX_SCRAPE_RETRIES
            }
        }

    def test_scrapers(self, test_url: str = "https://httpbin.org/html") -> Dict[str, Any]:
        """🔧 CORRIGÉ: Teste les différents scrapers avec le paramètre LLM"""
        results = {}
        
        try:
            # Test scraper traditionnel
            logger.info(f"Testing traditional scraper with {test_url}")
            traditional_result = self.traditional_scraper.scrape(test_url)
            results["traditional"] = {
                "success": traditional_result is not None,
                "content_length": len(traditional_result.raw_content) if traditional_result else 0,
                "error": None if traditional_result else "No content returned"
            }
            
            # 🔧 CORRIGÉ: Test scraper intelligent sans LLM
            logger.info(f"Testing intelligent scraper with {test_url} (LLM disabled)")
            intelligent_result = self.intelligent_scraper.scrape_with_analysis(test_url, enable_llm_analysis=False)
            results["intelligent"] = {
                "success": intelligent_result is not None,
                "content_length": len(intelligent_result.raw_content) if intelligent_result else 0,
                "has_analysis": bool(intelligent_result and intelligent_result.structured_data.get('intelligent_analysis')),
                "error": None if intelligent_result else "No content returned"
            }
            
            # Test LLM si disponible
            if self.analyzer and traditional_result:
                logger.info("Testing LLM analyzer")
                llm_test = self._perform_llm_analysis(
                    traditional_result.raw_content[:1000], 
                    AnalysisType.STANDARD
                )
                results["llm_analysis"] = {
                    "success": "error" not in llm_test,
                    "has_insights": bool(llm_test.get("insights")),
                    "confidence": llm_test.get("confidence_score", 0),
                    "error": llm_test.get("error")
                }
            else:
                results["llm_analysis"] = {
                    "success": False,
                    "error": "LLM analyzer not available or no content to analyze"
                }
                
        except Exception as e:
            logger.error(f"Error testing scrapers: {e}")
            results["test_error"] = str(e)
        
        return results