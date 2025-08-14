import logging
from typing import Dict, List, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from app.agents.scraper_agent import ScraperAgent, ScrapingResult
from app.agents.analyzer_agent import AnalyzerAgent, AnalysisResult
from app.models.schemas import ScrapeRequest, CoordinatorResult
from app.models.database import ScrapingTask, ScrapedData, get_db

logger = logging.getLogger(__name__)

class AgentCoordinator:
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.scraper_agents = [ScraperAgent(f"scraper_{i}") for i in range(max_workers)]
        self.analyzer_agents = [AnalyzerAgent(f"analyzer_{i}") for i in range(max_workers)]
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}

    async def coordinate_scraping_task(self, task_request: Dict[str, Any]) -> CoordinatorResult:
        start_time = datetime.utcnow()
        db: Session = next(get_db())
        scraping_results: List[ScrapingResult] = []
        analysis_results: List[AnalysisResult] = []

        try:
            urls = task_request.get("urls", [])
            task_id = task_request.get("task_id", "unknown")

            # Scraping async séquentiel (ou on peut paralléliser plus tard)
            for i, url in enumerate(urls):
                scraper_agent = self.scraper_agents[i % self.max_workers]
                request = ScrapeRequest(url=url, analysis_type=task_request.get("analysis_type", "standard"))
                result: ScrapingResult = await scraper_agent.scrape(request)
                scraping_results.append(result)

                # Sauvegarde des données scrapées dans la DB
                if result.content:
                    scraped_data = ScrapedData(
                        url=result.url,
                        content=result.content.raw_content,
                        scrape_metadata=result.content.metadata,
                        source_type=result.metadata.get('method', 'unknown'),
                        is_processed=result.success
                    )
                    db.add(scraped_data)

            db.commit()

            # Analyse parallèle avec run_in_executor (car sync)
            loop = asyncio.get_running_loop()
            analysis_tasks = []
            for i, scrape_res in enumerate(scraping_results):
                if scrape_res.success and scrape_res.content:
                    analyzer_agent = self.analyzer_agents[i % self.max_workers]
                    analysis_tasks.append(
                        loop.run_in_executor(
                            self.executor,
                            analyzer_agent.analyze_scraped_data,
                            {
                                "result": scrape_res.content.raw_content,
                                "analysis_type": scrape_res.analysis_type,
                                "query": scrape_res.url
                            }
                        )
                    )
            if analysis_tasks:
                analysis_results = await asyncio.gather(*analysis_tasks)

            total_time = (datetime.utcnow() - start_time).total_seconds()

            # Synthèse simple des résultats
            successful_scrapes = sum(1 for r in scraping_results if r.success)
            failed_scrapes = len(scraping_results) - successful_scrapes
            avg_confidence = (sum(r.confidence_score for r in analysis_results) / len(analysis_results)) if analysis_results else 0.0

            final_insights = {
                "urls_processed": len(urls),
                "successful_scrapes": successful_scrapes,
                "failed_scrapes": failed_scrapes,
                "average_confidence": avg_confidence,
                "analysis_summaries": [r.insights for r in analysis_results]
            }

            # Enregistrer la tâche globale en DB
            task = ScrapingTask(
                task_id=task_id,
                urls=urls,
                status="completed",
                result=final_insights,
                completed_at=datetime.utcnow()
            )
            db.add(task)
            db.commit()

            return CoordinatorResult(
                task_id=task_id,
                scraping_results=scraping_results,
                analysis_results=analysis_results,
                final_insights=final_insights,
                status="completed",
                total_processing_time=total_time,
                timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(f"Erreur coordination tâche {task_request.get('task_id')}: {e}", exc_info=True)
            db.rollback()
            return CoordinatorResult(
                task_id=task_request.get("task_id", "unknown"),
                scraping_results=scraping_results,
                analysis_results=[],
                final_insights={"error": str(e)},
                status="failed",
                total_processing_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow().isoformat()
            )
        finally:
            db.close()

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "running",
            "active_tasks": len(self.active_tasks),
            "scraper_agents": [agent.name for agent in self.scraper_agents],
            "analyzer_agents": [agent.agent_id for agent in self.analyzer_agents],
            "timestamp": datetime.utcnow().isoformat()
        }
