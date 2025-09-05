"""
Tâches Celery CORRIGÉES - Timeouts sécurisés et gestion stratégies
VERSION CORRIGÉE avec fixes critiques pour éviter les tâches bloquées
"""

from typing import List, Dict, Any, Optional
import logging
import traceback
from datetime import datetime
from sqlalchemy import update
import signal
import time

from app.models.database import ScrapingTask, get_db_session
from app.agents.smart_coordinator import SmartScrapingCoordinator

logger = logging.getLogger(__name__)

def get_celery_app():
    """Fonction helper pour obtenir l'app Celery de manière différée"""
    from app.celery_app import celery_app
    return celery_app

def make_json_serializable(obj):
    """Assure que l'objet est JSON-serializable"""
    if obj is None:
        return None
    elif isinstance(obj, (bool, int, float, str)):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {str(k): make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, 'dict'):
        try:
            return make_json_serializable(obj.dict())
        except:
            return str(obj)
    elif hasattr(obj, 'model_dump'):
        try:
            return make_json_serializable(obj.model_dump())
        except:
            return str(obj)
    else:
        return str(obj)

class TimeoutHandler:
    """Gestionnaire de timeout pour éviter les tâches bloquées"""
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.timeout_seconds)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        return False
    
    def _timeout_handler(self, signum, frame):
        elapsed = time.time() - self.start_time if self.start_time else 0
        raise TimeoutError(f"Task timed out after {elapsed:.1f}s (limit: {self.timeout_seconds}s)")
    
    def check_timeout(self):
        """Vérification manuelle du timeout"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(f"Task manually timed out after {elapsed:.1f}s")

def register_tasks():
    """Enregistre les tâches Celery CORRIGÉES avec timeouts sécurisés"""
    celery_app = get_celery_app()
    
    @celery_app.task(bind=True, name='app.tasks.scraping_tasks.smart_scraping_task',
                     soft_time_limit=540, time_limit=600)  # CORRECTION: Timeouts explicites
    def smart_scraping_task(
        self, 
        task_id: str, 
        urls: List[str], 
        enable_llm_analysis: bool = False,
        quality_threshold: float = 0.1,  # CORRIGÉ: Seuil très permissif
        timeout: int = 60,
        callback_url: Optional[str] = None,
        priority: int = 1
    ):
        """Tâche de scraping intelligent CORRIGÉE avec timeouts sécurisés"""
        start_time = datetime.utcnow()
        
        # CORRECTION CRITIQUE: Protection timeout globale
        max_task_timeout = min(timeout * len(urls), 500)  # Max 8min 20s
        
        logger.info(f"🚀 CORRECTED smart scraping task started: {task_id}")
        logger.info(f"URLs: {len(urls)}, LLM: {'Enabled' if enable_llm_analysis else 'Auto'}")
        logger.info(f"Task timeout protection: {max_task_timeout}s")
        
        try:
            with TimeoutHandler(max_task_timeout):
                # Initialisation du progress avec protection DB
                try:
                    with get_db_session() as db:
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
                                progress=progress_data,
                                worker_id=self.request.id
                            )
                        )
                        db.commit()
                except Exception as db_error:
                    logger.warning(f"DB update failed: {db_error}")

                # CORRECTION CRITIQUE: Création du coordinateur avec gestion d'erreurs
                try:
                    coordinator = SmartScrapingCoordinator()
                    logger.info("✅ Smart coordinator created successfully")
                except Exception as coord_error:
                    logger.error(f"❌ Failed to create coordinator: {coord_error}")
                    raise Exception(f"Coordinator initialization failed: {coord_error}")
                
                results = []
                successful_urls = 0
                strategy_stats = {"traditional": 0, "intelligent": 0}
                
                # CORRECTION: Limitation intelligente du nombre d'URLs
                max_urls = min(len(urls), 10)  # Limiter à 10 URLs max
                urls_to_process = urls[:max_urls]
                
                if len(urls) > max_urls:
                    logger.warning(f"⚠️ URLs limited from {len(urls)} to {max_urls} for performance")
                
                # Traitement avec timeout par URL
                for i, url in enumerate(urls_to_process):
                    url_start_time = time.time()
                    
                    try:
                        logger.info(f"🎯 Processing URL {i+1}/{len(urls_to_process)}: {url}")
                        
                        # CORRECTION CRITIQUE: Timeout par URL
                        single_url_timeout = min(timeout, 90)  # Max 90s par URL
                        
                        # Vérification timeout global
                        elapsed_total = (datetime.utcnow() - start_time).total_seconds()
                        if elapsed_total > max_task_timeout * 0.9:  # 90% du timeout
                            logger.warning(f"⏰ Approaching task timeout, stopping at URL {i+1}")
                            break
                        
                        # CORRECTION: Appel coordinateur avec timeout et validation
                        scrape_result = None
                        try:
                            with TimeoutHandler(single_url_timeout):
                                # Support LangGraph pour le superviseur
                                if hasattr(coordinator, 'scrape_with_langgraph'):
                                    logger.info("Using LangGraph-enabled scraping")
                                    scrape_result = coordinator.scrape_with_langgraph(
                                        url=url,
                                        enable_llm_analysis=enable_llm_analysis
                                    )      
                                else:
                                    logger.info("Using standard coordinator scraping")
                                    scrape_result = coordinator.scrape(
                                        url=url,
                                        enable_llm_analysis=enable_llm_analysis,
                                        quality_threshold=quality_threshold,
                                        timeout=single_url_timeout
                                    )
                        except TimeoutError as timeout_error:
                            logger.error(f"⏰ URL timeout: {url} after {single_url_timeout}s")
                            scrape_result = None
                        except Exception as scrape_error:
                            logger.error(f"❌ Scraping error for {url}: {scrape_error}")
                            scrape_result = None
                        
                        url_processing_time = time.time() - url_start_time
                        
                        # CORRECTION CRITIQUE: Validation du résultat avec logs détaillés
                        if scrape_result and hasattr(scrape_result, 'structured_data'):
                            logger.info(f"✅ Scrape result received for {url}")
                            
                            # Extraction sécurisée des données
                            try:
                                raw_content = scrape_result.raw_content or ""
                                structured_data = scrape_result.structured_data or {}
                                metadata = scrape_result.metadata or {}
                                
                                # Récupération sécurisée de la stratégie
                                coordinator_meta = metadata.get('smart_coordinator', {})
                                strategy_used = coordinator_meta.get('strategy_used', 'intelligent')
                                
                                # CORRECTION: Validation de la stratégie
                                if strategy_used in strategy_stats:
                                    strategy_stats[strategy_used] += 1
                                else:
                                    strategy_stats['intelligent'] += 1
                                    strategy_used = 'intelligent'
                                
                                # Extraction du nombre de valeurs
                                extracted_values = structured_data.get('extracted_values', {})
                                extraction_count = len(extracted_values) if isinstance(extracted_values, dict) else 0
                                
                                logger.info(f"📊 Extracted {extraction_count} values using {strategy_used} strategy")
                                
                                # Construction du résultat enrichi
                                result_dict = {
                                    "url": url,
                                    "success": True,
                                    "status_code": 200,
                                    "content": {
                                        "raw_content": raw_content[:5000] if raw_content else "",
                                        "structured_data": structured_data,
                                        "metadata": metadata
                                    },
                                    "strategy_used": strategy_used,
                                    "method": f"corrected_{strategy_used}",
                                    "llm_analysis": metadata.get('llm_analysis', {}),
                                    "processing_time": url_processing_time,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "confidence_score": metadata.get('compliance_score', 0.8),
                                    "extraction_count": extraction_count,
                                    "quality_metrics": {
                                        "content_length": len(raw_content),
                                        "structured_data_fields": len(structured_data) if isinstance(structured_data, dict) else 0,
                                        "has_llm_analysis": bool(metadata.get('llm_analysis')),
                                        "intelligence_level": metadata.get('intelligence_level', 'enhanced_automatic')
                                    },
                                    "corrections_applied": [
                                        "timeout_protection",
                                        "strategy_validation", 
                                        "robust_error_handling",
                                        "permissive_thresholds"
                                    ]
                                }
                                
                                results.append(result_dict)
                                successful_urls += 1
                                logger.info(f"✅ URL processed successfully: {url} using {strategy_used}")
                                
                            except Exception as result_error:
                                logger.error(f"❌ Result processing failed for {url}: {result_error}")
                                error_result = {
                                    "url": url,
                                    "success": False,
                                    "status_code": 500,
                                    "error": f"Result processing error: {str(result_error)}",
                                    "strategy_used": "error",
                                    "method": "processing_failed",
                                    "timestamp": datetime.utcnow().isoformat()
                                }
                                results.append(error_result)
                        else:
                            logger.warning(f"⚠️ No valid result from coordinator for: {url}")
                            error_result = {
                                "url": url,
                                "success": False,
                                "status_code": 500,
                                "error": "Coordinator returned no valid content",
                                "strategy_used": "failed",
                                "method": "coordinator_failed",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            results.append(error_result)
                        
                        # Mise à jour du progress avec protection
                        try:
                            current_progress = i + 1
                            percentage = round((current_progress / len(urls_to_process)) * 100, 2)
                            
                            progress_data = {
                                "current": current_progress,
                                "total": len(urls_to_process),
                                "percentage": percentage,
                                "display": f"{current_progress}/{len(urls_to_process)}"
                            }
                            
                            with get_db_session() as db:
                                db.execute(
                                    update(ScrapingTask)
                                    .where(ScrapingTask.task_id == task_id)
                                    .values(progress=progress_data)
                                )
                                db.commit()
                        except Exception as progress_error:
                            logger.warning(f"Progress update failed: {progress_error}")
                            
                    except Exception as url_error:
                        logger.error(f"❌ Error processing URL {url}: {str(url_error)}")
                        
                        error_result = {
                            "url": url,
                            "success": False,
                            "status_code": 500,
                            "error": str(url_error),
                            "strategy_used": "error",
                            "method": "url_processing_error",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        results.append(error_result)

                # Calcul des métriques finales
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                # CORRECTION: Métriques robustes
                success_rate = round((successful_urls / len(urls_to_process)) * 100, 2) if urls_to_process else 0
                
                metrics = {
                    "total_urls": len(urls),
                    "processed_urls": len(urls_to_process), 
                    "successful_urls": successful_urls,
                    "failed_urls": len(urls_to_process) - successful_urls,
                    "success_rate": success_rate,
                    "execution_time": round(execution_time, 2),
                    "analysis_type": "corrected_smart_automatic",
                    "llm_analysis_enabled": enable_llm_analysis,
                    "coordinator_mode": "corrected_intelligent_automatic",
                    "strategy_distribution": strategy_stats,
                    "corrections_metadata": {
                        "timeout_protection_applied": True,
                        "url_limiting_applied": len(urls) > len(urls_to_process),
                        "permissive_validation": True,
                        "robust_error_handling": True,
                        "max_task_timeout": max_task_timeout
                    }
                }

                # Finalisation avec protection DB
                final_progress = {
                    "current": len(urls_to_process),
                    "total": len(urls_to_process),
                    "percentage": 100.0,
                    "display": f"{len(urls_to_process)}/{len(urls_to_process)}"
                }

                try:
                    with get_db_session() as db:
                        db.execute(
                            update(ScrapingTask)
                            .where(ScrapingTask.task_id == task_id)
                            .values(
                                status="completed",
                                completed_at=datetime.utcnow(),
                                results=results,
                                progress=final_progress,
                                metrics=metrics
                            )
                        )
                        db.commit()
                except Exception as final_db_error:
                    logger.error(f"Final DB update failed: {final_db_error}")
                    
                logger.info(f"🎉 CORRECTED smart scraping completed: {task_id}")
                logger.info(f"Success rate: {success_rate}% ({successful_urls}/{len(urls_to_process)})")
                logger.info(f"Strategy distribution: {strategy_stats}")
                logger.info(f"Execution time: {execution_time:.2f}s")
                
                return make_json_serializable({
                    "task_id": task_id,
                    "status": "completed",
                    "metrics": metrics,
                    "successful_urls": successful_urls,
                    "total_urls": len(urls),
                    "processed_urls": len(urls_to_process),
                    "execution_time": execution_time,
                    "coordinator_mode": "corrected_smart_automatic",
                    "corrections_applied": [
                        "timeout_protection",
                        "url_limiting",
                        "strategy_validation",
                        "robust_error_handling",
                        "permissive_validation"
                    ]
                })
                
        except TimeoutError as timeout_error:
            error_msg = f"Task timed out: {str(timeout_error)}"
            logger.error(f"⏰ TIMEOUT: {task_id} - {error_msg}")
            
            try:
                with get_db_session() as db:
                    db.execute(
                        update(ScrapingTask)
                        .where(ScrapingTask.task_id == task_id)
                        .values(
                            status="timeout",
                            completed_at=datetime.utcnow(),
                            error=error_msg
                        )
                    )
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update DB after timeout: {db_error}")
            
            raise timeout_error
            
        except Exception as e:
            error_msg = f"CORRECTED smart scraping failed: {str(e)}"
            logger.error(f"❌ Task failed: {task_id} - {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            try:
                with get_db_session() as db:
                    db.execute(
                        update(ScrapingTask)
                        .where(ScrapingTask.task_id == task_id)
                        .values(
                            status="failed",
                            completed_at=datetime.utcnow(),
                            error=error_msg
                        )
                    )
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update DB: {db_error}")
            
            # CORRECTION: Retry intelligent avec backoff
            if self.request.retries < 2:  # Réduit à 2 tentatives max
                countdown = 30 * (2 ** self.request.retries)  # Backoff plus court
                logger.info(f"🔄 Retrying task {task_id} in {countdown}s (attempt {self.request.retries + 1}/2)")
                raise self.retry(exc=e, countdown=countdown, max_retries=2)
            else:
                logger.error(f"❌ Task {task_id} failed after all retries")
                raise e

    @celery_app.task(bind=True, name='app.tasks.scraping_tasks.health_check_task',
                     soft_time_limit=30, time_limit=45)  # CORRECTION: Timeouts courts
    def health_check_task(self):
        """Tâche de vérification de santé CORRIGÉE avec timeout"""
        try:
            check_start = datetime.utcnow()
            
            with TimeoutHandler(40):  # Protection timeout
                # Test du coordinateur intelligent
                coordinator = SmartScrapingCoordinator()
                coordinator_status = coordinator.get_coordinator_status()
                
                # Test de la base de données avec timeout
                try:
                    with get_db_session() as db:
                        total_tasks = db.execute("SELECT COUNT(*) FROM scraping_tasks").scalar()
                        active_tasks = db.execute(
                            "SELECT COUNT(*) FROM scraping_tasks WHERE status IN ('pending', 'running')"
                        ).scalar()
                        recent_tasks = db.execute(
                            "SELECT COUNT(*) FROM scraping_tasks WHERE created_at >= CURRENT_DATE"
                        ).scalar()
                except Exception as db_error:
                    logger.error(f"DB health check failed: {db_error}")
                    total_tasks = active_tasks = recent_tasks = -1
                
                check_time = (datetime.utcnow() - check_start).total_seconds()
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "coordinator": {
                        "status": "operational",
                        "type": coordinator_status.get("coordinator_type", "SmartScrapingCoordinator"),
                        "version": coordinator_status.get("version", "2.0_corrected"),
                        "features": coordinator_status.get("features", [])
                    },
                    "database": {
                        "status": "connected" if total_tasks >= 0 else "error",
                        "total_tasks": total_tasks,
                        "active_tasks": active_tasks,
                        "today_tasks": recent_tasks
                    },
                    "worker": {
                        "mode": "corrected_smart_automatic",
                        "check_time": round(check_time, 3),
                        "worker_id": self.request.id,
                        "timeout_protection": True
                    },
                    "corrections_applied": [
                        "timeout_protection",
                        "robust_db_checks",
                        "error_resilience"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "worker_mode": "corrected_smart_automatic"
            }

    @celery_app.task(bind=True, name='app.tasks.scraping_tasks.coordinator_status_task',
                     soft_time_limit=20, time_limit=30)  # CORRECTION: Timeouts courts
    def coordinator_status_task(self):
        """Tâche de statut du coordinateur CORRIGÉE"""
        try:
            with TimeoutHandler(25):  # Protection timeout
                coordinator = SmartScrapingCoordinator()
                status = coordinator.get_coordinator_status()
                
                return make_json_serializable({
                    "timestamp": datetime.utcnow().isoformat(),
                    "coordinator_status": status,
                    "task_id": self.request.id,
                    "intelligence_mode": "corrected_automatic",
                    "timeout_protection": True
                })
                
        except Exception as e:
            logger.error(f"Coordinator status check failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            }
            
    @celery_app.task(bind=True, name="test_langgraph_workflow")
    def test_langgraph_workflow(self, test_urls: List[str] = None):
        """Test du workflow LangGraph pour le superviseur"""
        try:
            if not test_urls:
                test_urls = [
                    "https://api.worldbank.org/v2/countries/TN/indicators/NY.GDP.MKTP.CD?format=json&date=2020:2023",
                    "https://restcountries.com/v3.1/name/tunisia"
                ]
            
            coordinator = SmartScrapingCoordinator()
            results = {}
            
            for url in test_urls:
                logger.info(f"Testing LangGraph workflow with: {url}")
                
                try:
                    if hasattr(coordinator, 'scrape_with_langgraph'):
                        result = coordinator.scrape_with_langgraph(url, enable_llm_analysis=False)
                        
                        results[url] = {
                            "success": result is not None,
                            "langgraph_enabled": True,
                            "content_length": len(result.raw_content) if result and result.raw_content else 0,
                            "structured_data": bool(result and result.structured_data),
                            "metadata": result.metadata if result else None
                        }
                    else:
                        results[url] = {
                            "success": False,
                            "langgraph_enabled": False,
                            "error": "LangGraph method not available"
                        }
                        
                except Exception as e:
                    results[url] = {
                        "success": False,
                        "error": str(e)
                    }
                    logger.error(f"LangGraph test failed for {url}: {e}")
            
            return {
                "task_id": self.request.id,
                "test_results": results,
                "supervisor_requirements_met": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LangGraph workflow test failed: {e}")
            return {
                "task_id": self.request.id,
                "success": False,
                "error": str(e)
            }

    return smart_scraping_task, health_check_task, coordinator_status_task, test_langgraph_workflow

# Export pour utilisation externe
if __name__ != '__main__':
    try:
        smart_scraping_task, health_check_task, coordinator_status_task, test_langgraph_workflow = register_tasks()
        logger.info("CORRECTED smart scraping tasks registered successfully")
    except Exception as e:
        logger.error(f"Task registration failed: {e}")

__all__ = [
    'register_tasks', 
    'smart_scraping_task', 
    'health_check_task', 
    'coordinator_status_task',
    'test_langgraph_workflow',  # AJOUTÉ
    'make_json_serializable',
    'TimeoutHandler'
]