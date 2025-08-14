# 🔥 CORRECTION CRITIQUE: Réorganiser les imports pour éviter l'import circulaire

from typing import List, Dict, Any, Optional
import logging
import traceback
from datetime import datetime, timedelta
from sqlalchemy import update

# Import des modèles et schémas en premier
from app.models.schemas import ScrapeRequest, AnalysisType
from app.models.database import ScrapingTask, get_db

# Import de l'app Celery APRÈS les dépendances de base
from app.agents.scraper_agent import ScraperAgent

# 🔥 Import de celery_app à la fin pour éviter les cycles
def get_celery_app():
    """Fonction helper pour obtenir l'app Celery de manière différée"""
    from app.celery_app import celery_app
    return celery_app

logger = logging.getLogger(__name__)

# 🚀 Décoration des tâches avec une référence différée
def register_tasks():
    """Enregistre les tâches Celery après initialisation"""
    celery_app = get_celery_app()
    
    @celery_app.task(bind=True, name='app.tasks.scraping_tasks.enqueue_scraping_task')
    def enqueue_scraping_task(self, task_id: str, urls: List[str], analysis_type: str, 
                             parameters: Dict[str, Any], callback_url: Optional[str] = None, priority: int = 1):
        """
        Tâche Celery pour le scraping asynchrone - SIGNATURE CORRIGÉE ET UNIFIÉE
        """
        start_time = datetime.utcnow()
        logger.info(f"SCRAPING TASK STARTED: {task_id}")
        logger.info(f"URLs to scrape: {len(urls)} URLs")
        logger.info(f"Analysis type: {analysis_type}")
        logger.info(f"Parameters: {list(parameters.keys()) if parameters else 'None'}")
        logger.info(f"Priority: {priority}")
        
        try:
            # CORRECTION: Mise à jour sécurisée du statut avec format progress unifié
            with next(get_db()) as db:
                # Utiliser le format JSON unifié pour progress
                progress_data = {
                    "current": 0, 
                    "total": len(urls), 
                    "percentage": 0.0, 
                    "display": f"0/{len(urls)}"
                }
                
                db.execute(
                    update(ScrapingTask)
                    .where(ScrapingTask.task_id == task_id)
                    .values(
                        status="running",
                        started_at=start_time,
                        progress=progress_data
                    )
                )
                db.commit()
                logger.info(f"Task {task_id} status updated to 'running'")

            # Initialisation de l'agent scraper
            scraper_agent = ScraperAgent()
            results = []
            successful_urls = 0
            
            for i, url in enumerate(urls):
                try:
                    logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
                    
                    # CORRECTION: Création de la requête avec signature unifiée
                    scrape_request = ScrapeRequest(
                        urls=[url],
                        analysis_type=AnalysisType(analysis_type),
                        parameters=parameters or {},
                        callback_url=callback_url,
                        priority=priority
                    )

                    # 🔧 NOUVEAU: Ajouter les paramètres LLM et Intelligence à la requête
                    if parameters:
                        scrape_request.enable_llm_analysis = parameters.get('enable_llm_analysis', False)
                        scrape_request.enable_intelligent_analysis = parameters.get('enable_intelligent_analysis', False)
                        scrape_request.quality_threshold = parameters.get('quality_threshold', 0.6)
                        scrape_request.timeout = parameters.get('timeout', 30)

                    # Log pour debug
                    logger.info(f"🤖 Request LLM Analysis: {'Enabled' if getattr(scrape_request, 'enable_llm_analysis', False) else 'Disabled'}")
                    logger.info(f"🧠 Request Intelligent Analysis: {'Enabled' if getattr(scrape_request, 'enable_intelligent_analysis', False) else 'Disabled'}")
                    
                    # Exécution du scraping
                    scraping_result = scraper_agent.scrape(scrape_request)
                    
                    # CORRECTION: Vérification robuste de la sérialisation
                    if hasattr(scraping_result, 'model_dump'):
                        # Pydantic v2
                        result_dict = scraping_result.model_dump()
                    elif hasattr(scraping_result, 'dict'):
                        # Pydantic v1
                        result_dict = scraping_result.dict()
                    else:
                        # Fallback manuel
                        result_dict = {
                            "url": getattr(scraping_result, 'url', url),
                            "content": getattr(scraping_result, 'content', {}),
                            "status_code": getattr(scraping_result, 'status_code', 0),
                            "metadata": getattr(scraping_result, 'metadata', {}),
                            "success": getattr(scraping_result, 'success', False),
                            "error": getattr(scraping_result, 'error', None),
                            "analysis_type": analysis_type,
                            "llm_analysis": getattr(scraping_result, 'llm_analysis', {}),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    
                    results.append(result_dict)
                    if result_dict.get('success', False):
                        successful_urls += 1
                        logger.info(f"URL {url} scraped successfully")
                    else:
                        logger.warning(f"URL {url} scraping failed: {result_dict.get('error', 'Unknown error')}")
                    
                    # CORRECTION: Mise à jour du progrès avec format unifié
                    current_progress = i + 1
                    percentage = round((current_progress / len(urls)) * 100, 2)
                    
                    progress_data = {
                        "current": current_progress,
                        "total": len(urls),
                        "percentage": percentage,
                        "display": f"{current_progress}/{len(urls)}"
                    }
                    
                    with next(get_db()) as db:
                        db.execute(
                            update(ScrapingTask)
                            .where(ScrapingTask.task_id == task_id)
                            .values(progress=progress_data)
                        )
                        db.commit()
                        
                except Exception as url_error:
                    logger.error(f"Error processing URL {url}: {str(url_error)}")
                    # CORRECTION: Format de résultat d'erreur unifié
                    error_result = {
                        "url": url,
                        "content": {},
                        "status_code": 0,
                        "metadata": {"error": str(url_error), "error_type": type(url_error).__name__},
                        "timestamp": datetime.utcnow().isoformat(),
                        "success": False,
                        "error": str(url_error),
                        "analysis_type": analysis_type,
                        "llm_analysis": {}
                    }
                    results.append(error_result)
                    continue

            # Calcul du temps d'exécution
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # CORRECTION: Calcul des métriques enrichies
            metrics = {
                "total_urls": len(urls),
                "successful_urls": successful_urls,
                "failed_urls": len(urls) - successful_urls,
                "success_rate": round((successful_urls / len(urls)) * 100, 2) if urls else 0,
                "execution_time": round(execution_time, 2),
                "average_time_per_url": round(execution_time / len(urls), 2) if urls else 0,
                "analysis_type": analysis_type,
                "parameters_used": bool(parameters),
                "has_callback": bool(callback_url),
                "priority": priority
            }

            # CORRECTION: Finalisation avec format progress unifié
            final_progress = {
                "current": len(urls),
                "total": len(urls),
                "percentage": 100.0,
                "display": f"{len(urls)}/{len(urls)}"
            }

            with next(get_db()) as db:
                db.execute(
                    update(ScrapingTask)
                    .where(ScrapingTask.task_id == task_id)
                    .values(
                        status="completed",
                        completed_at=datetime.utcnow(),
                        results=results,  # Utiliser results (pas result)
                        progress=final_progress,
                        metrics=metrics
                    )
                )
                db.commit()
                
            logger.info(f"SCRAPING TASK COMPLETED: {task_id}")
            logger.info(f"Results: {successful_urls} successful, {len(urls)-successful_urls} failed")
            logger.info(f"Execution time: {execution_time:.2f} seconds")
            logger.info(f"Success rate: {metrics['success_rate']}%")
            
            # CORRECTION: Retour cohérent avec toutes les informations
            return {
                "task_id": task_id,
                "status": "completed",
                "metrics": metrics,
                "successful_urls": successful_urls,
                "total_urls": len(urls),
                "execution_time": execution_time,
                "results_count": len(results),
                "analysis_type": analysis_type
            }
            
        except Exception as e:
            error_msg = f"Erreur lors du scraping: {str(e)}"
            logger.error(f"SCRAPING TASK FAILED: {task_id} - {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # CORRECTION: Mise à jour du statut d'erreur avec format unifié
            try:
                error_progress = {
                    "current": 0,
                    "total": len(urls),
                    "percentage": 0.0,
                    "display": f"0/{len(urls)} (error)"
                }
                
                with next(get_db()) as db:
                    db.execute(
                        update(ScrapingTask)
                        .where(ScrapingTask.task_id == task_id)
                        .values(
                            status="failed",
                            completed_at=datetime.utcnow(),
                            error=error_msg,
                            progress=error_progress,
                            metrics={
                                "total_urls": len(urls),
                                "successful_urls": 0,
                                "failed_urls": len(urls),
                                "success_rate": 0.0,
                                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                                "error": error_msg,
                                "analysis_type": analysis_type
                            }
                        )
                    )
                    db.commit()
                    logger.info(f"Task {task_id} status updated to 'failed' in DB")
            except Exception as db_error:
                logger.error(f"Failed to update task status in DB: {db_error}")
            
            # CORRECTION: Retry avec paramètres appropriés
            raise self.retry(exc=e, countdown=60, max_retries=3)

    # =====================================
    # TÂCHES UTILITAIRES SUPPLÉMENTAIRES
    # =====================================

    @celery_app.task(bind=True, name='app.tasks.scraping_tasks.cleanup_old_tasks')
    def cleanup_old_tasks(self, days_old: int = 30):
        """
        Tâche de nettoyage des anciennes tâches
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            with next(get_db()) as db:
                deleted_count = db.query(ScrapingTask).filter(
                    ScrapingTask.created_at < cutoff_date,
                    ScrapingTask.status.in_(['completed', 'failed', 'cancelled'])
                ).delete()
                db.commit()
                
            logger.info(f"Cleaned up {deleted_count} old tasks (older than {days_old} days)")
            return {"deleted_count": deleted_count, "cutoff_date": cutoff_date.isoformat()}
            
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
            raise

    @celery_app.task(bind=True, name='app.tasks.scraping_tasks.get_task_statistics')
    def get_task_statistics(self):
        """
        Tâche pour obtenir des statistiques sur les tâches
        """
        try:
            with next(get_db()) as db:
                total_tasks = db.query(ScrapingTask).count()
                
                stats_by_status = {}
                for status in ['pending', 'running', 'completed', 'failed', 'cancelled']:
                    count = db.query(ScrapingTask).filter(ScrapingTask.status == status).count()
                    stats_by_status[status] = count
                
                stats_by_analysis_type = {}
                for analysis_type in ['standard', 'advanced', 'custom']:
                    count = db.query(ScrapingTask).filter(ScrapingTask.analysis_type == analysis_type).count()
                    stats_by_analysis_type[analysis_type] = count
                
                # Statistiques des 24 dernières heures
                last_24h = datetime.utcnow() - timedelta(hours=24)
                recent_tasks = db.query(ScrapingTask).filter(ScrapingTask.created_at >= last_24h).count()
                
            return {
                "total_tasks": total_tasks,
                "stats_by_status": stats_by_status,
                "stats_by_analysis_type": stats_by_analysis_type,
                "recent_tasks_24h": recent_tasks,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Statistics task failed: {e}")
            raise

    @celery_app.task(bind=True, name='app.tasks.scraping_tasks.health_check_task')
    def health_check_task(self):
        """
        Tâche de vérification de santé pour Celery
        """
        try:
            logger.info("Health check task started")
            
            # Test de connectivité DB
            with next(get_db()) as db:
                task_count = db.query(ScrapingTask).count()
            
            # Test simple sans dépendance externe
            result = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database_connection": "ok",
                "total_tasks_in_db": task_count,
                "worker_id": f"worker_{self.request.id}",
                "check_duration": "< 1s"
            }
            
            logger.info("Health check task completed successfully")
            return result
            
        except Exception as e:
            error_result = {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
                "worker_id": f"worker_{self.request.id}"
            }
            logger.error(f"Health check task failed: {e}")
            return error_result

    # Retourner les fonctions pour export
    return enqueue_scraping_task, cleanup_old_tasks, get_task_statistics, health_check_task

# 🚀 Enregistrement des tâches (appelé depuis celery_app.py)
if __name__ != '__main__':
    try:
        enqueue_scraping_task, cleanup_old_tasks, get_task_statistics, health_check_task = register_tasks()
        logger.info("✅ Scraping tasks registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register scraping tasks: {e}")

# Export des fonctions pour utilisation externe
__all__ = ['register_tasks', 'enqueue_scraping_task', 'cleanup_old_tasks', 'get_task_statistics', 'health_check_task']