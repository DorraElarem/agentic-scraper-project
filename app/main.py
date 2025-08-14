# Import des dépendances système
import os
import sys
import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional, Any
from uuid import UUID

# Import FastAPI
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, text

# Import des modules de l'application
from app.models.database import init_db, get_db, ScrapingTask
from app.models.schemas import (
    ScrapeRequest, TaskResponse, AnalysisType, ProgressInfo
)

# Import Celery - avec gestion d'erreur
try:
    from app.celery_app import celery_app
    CELERY_AVAILABLE = True
    logging.info("✅ Celery app imported successfully")
except ImportError as e:
    logging.error(f"❌ Failed to import Celery app: {e}")
    CELERY_AVAILABLE = False
    celery_app = None

# Import des tâches de scraping - avec gestion d'erreur
try:
    import app.tasks.scraping_tasks
    SCRAPING_TASKS_AVAILABLE = True
    logging.info("✅ Scraping tasks imported successfully")
except ImportError as e:
    logging.error(f"❌ Failed to import scraping tasks: {e}")
    SCRAPING_TASKS_AVAILABLE = False

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f"🚀 FASTAPI STARTING AT {datetime.utcnow()}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    logger.info("🔧 INITIALIZING APPLICATION...")
    
    # Initialisation de la base de données
    try:
        init_db()
        logger.info("✅ DATABASE INITIALIZED")
    except Exception as e:
        logger.error(f"❌ DATABASE INITIALIZATION FAILED: {e}")
        raise
    
    # Test de communication Celery au démarrage
    if CELERY_AVAILABLE and celery_app:
        logger.info("🔧 TESTING CELERY COMMUNICATION...")
        try:
            # Test avec la tâche de debug
            result = celery_app.send_task('app.celery_app.debug_communication')
            logger.info(f"✅ CELERY TEST TASK SENT: {result.id}")
            
            # Vérification des tâches enregistrées
            registered_tasks = list(celery_app.tasks.keys())
            logger.info(f"✅ REGISTERED TASKS COUNT: {len(registered_tasks)}")
            
            if 'app.tasks.scraping_tasks.enqueue_scraping_task' in registered_tasks:
                logger.info("✅ SCRAPING TASK IS AVAILABLE IN MAIN!")
            else:
                logger.warning("❌ SCRAPING TASK NOT AVAILABLE IN MAIN!")
                
        except Exception as e:
            logger.error(f"❌ CELERY COMMUNICATION FAILED: {e}")
    else:
        logger.warning("⚠️ CELERY NOT AVAILABLE - Running in synchronous mode")
    
    yield
    
    logger.info("🔧 SHUTTING DOWN APPLICATION...")

# Initialisation FastAPI
app = FastAPI(
    title="Agentic Scraper API",
    description="API de scraping intelligent avec agents IA",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================
# ENDPOINT HEALTH UNIQUE
# =====================================

@app.get("/health")
async def health_check():
    """Endpoint de santé global - version simplifiée"""
    try:
        status_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "components": {
                "fastapi": "running",
                "celery": "available" if CELERY_AVAILABLE else "unavailable",
                "scraping_tasks": "available" if SCRAPING_TASKS_AVAILABLE else "unavailable",
                "database": "unknown",
                "redis": "unknown"
            }
        }
        
        # Test base de données
        try:
            db = next(get_db())
            db.execute(text("SELECT 1"))
            db.close()
            status_info["components"]["database"] = "available"
        except Exception:
            status_info["components"]["database"] = "unavailable"
            status_info["status"] = "unhealthy"
        
        # Test Redis
        if CELERY_AVAILABLE:
            try:
                import redis
                r = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'))
                r.ping()
                status_info["components"]["redis"] = "available"
            except Exception:
                status_info["components"]["redis"] = "unavailable"
        
        return status_info
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# =====================================
# ENDPOINTS DE SCRAPING
# =====================================

@app.post("/scrape", response_model=TaskResponse)
async def create_scraping_task(
    request: ScrapeRequest,
    db: Session = Depends(get_db)
):
    """Créer une nouvelle tâche de scraping"""
    if not CELERY_AVAILABLE or not celery_app:
        raise HTTPException(
            status_code=503,
            detail="Scraping service unavailable - Celery worker not running"
        )
    
    if not SCRAPING_TASKS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Scraping tasks not available - check worker configuration"
        )
    
    try:
        logger.info(f"🎯 NEW SCRAPING REQUEST: {len(request.urls)} URLs, type: {request.analysis_type}")
        
        # Génération d'un ID unique
        task_id = str(uuid.uuid4())
        
        # Validation des URLs
        valid_urls = [url for url in request.urls if url and url.strip()]
        if not valid_urls:
            raise HTTPException(status_code=400, detail="No valid URLs provided")
        
        # 🔧 CORRECTION: Enrichir les paramètres avec les flags LLM et Intelligence
        enriched_parameters = request.parameters or {}
        
        # Ajouter enable_llm_analysis et enable_intelligent_analysis aux paramètres
        enriched_parameters['enable_llm_analysis'] = getattr(request, 'enable_llm_analysis', False)
        enriched_parameters['enable_intelligent_analysis'] = getattr(request, 'enable_intelligent_analysis', False)
        enriched_parameters['quality_threshold'] = getattr(request, 'quality_threshold', 0.6)
        enriched_parameters['timeout'] = getattr(request, 'timeout', 30)
        
        logger.info(f"🤖 LLM Analysis: {'Enabled' if enriched_parameters['enable_llm_analysis'] else 'Disabled'}")
        logger.info(f"🧠 Intelligent Analysis: {'Enabled' if enriched_parameters['enable_intelligent_analysis'] else 'Disabled'}")
        
        # Création du progress
        initial_progress = ProgressInfo()
        initial_progress.update_from_values(0, len(valid_urls))
        
        # Création de l'entrée en base
        db_task = ScrapingTask(
            task_id=task_id,
            status="pending",
            progress=initial_progress.dict(),
            analysis_type=request.analysis_type.value,
            urls=valid_urls,
            parameters=enriched_parameters,  # 🔧 CORRECTION: Utiliser enriched_parameters
            callback_url=request.callback_url,
            priority=request.priority,
            created_at=datetime.utcnow(),
            results=[],
            max_retries=None,
            current_retries=None
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        logger.info(f"✅ TASK CREATED IN DB: {task_id}")
        
        # Envoi de la tâche à Celery
        try:
            celery_result = celery_app.send_task(
                'app.tasks.scraping_tasks.enqueue_scraping_task',
                args=[
                    task_id,
                    valid_urls,
                    request.analysis_type.value,
                    enriched_parameters,  # 🔧 CORRECTION: Utiliser enriched_parameters
                    request.callback_url or "",
                    request.priority
                ],
                retry=True,
                retry_policy={
                    'max_retries': 3,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )
            logger.info(f"✅ TASK SENT TO CELERY: {celery_result.id}")
            
            return TaskResponse(
                task_id=task_id,
                status="pending",
                analysis_type=request.analysis_type,
                progress=initial_progress,
                results=[],
                created_at=db_task.created_at,
                started_at=None,
                completed_at=None,
                error=None,
                metrics={},
                urls=valid_urls,
                parameters=enriched_parameters  # 🔧 CORRECTION: Retourner enriched_parameters
            )
            
        except Exception as celery_error:
            error_msg = str(celery_error)
            logger.error(f"❌ FAILED TO SEND TASK TO CELERY: {error_msg}")
            
            # Mettre à jour le statut en base
            db_task.status = "failed"
            db_task.error = f"Failed to queue task: {error_msg}"
            db_task.completed_at = datetime.utcnow()
            db.commit()
            
            raise HTTPException(
                status_code=500, 
                detail="Failed to queue scraping task"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ SCRAPING REQUEST FAILED: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Failed to create scraping task"
        )
        
@app.get("/tasks/{task_id}")
async def get_task_by_id(task_id: UUID, db: Session = Depends(get_db)):
    """Récupérer une tâche par son ID"""
    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.task_id == str(task_id)).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task.to_task_response()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve task"
        )

@app.get("/tasks")
async def get_tasks(
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lister les tâches avec filtres optionnels"""
    try:
        # Validation de la limite
        limit = min(max(limit, 1), 100)
        
        query = db.query(ScrapingTask)
        
        # Filtre par statut
        if status:
            valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
            if status in valid_statuses:
                query = query.filter(ScrapingTask.status == status)
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status. Valid statuses: {', '.join(valid_statuses)}"
                )
        
        tasks = query.order_by(desc(ScrapingTask.created_at)).limit(limit).all()
        
        # Conversion en réponses
        task_responses = []
        for task in tasks:
            try:
                task_responses.append(task.to_task_response())
            except Exception as e:
                logger.warning(f"Error converting task {task.task_id}: {e}")
                # Créer une réponse minimale en cas d'erreur
                task_responses.append(TaskResponse(
                    task_id=task.task_id,
                    status=task.status,
                    analysis_type=task.analysis_type or "standard",
                    progress=ProgressInfo(),
                    created_at=task.created_at or datetime.utcnow(),
                    error=f"Conversion error: {str(e)}",
                    urls=task.urls or [],
                    parameters=task.parameters or {}
                ))
        
        return {
            "tasks": task_responses,
            "total": len(task_responses),
            "limit": limit,
            "status_filter": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ GET TASKS FAILED: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Annuler/Supprimer une tâche"""
    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Si la tâche est déjà terminée, on ne peut que la supprimer de la base
        if task.status in ["completed", "failed", "cancelled"]:
            db.delete(task)
            db.commit()
            return {
                "message": f"Task {task_id} deleted from database",
                "task_id": task_id,
                "action": "deleted"
            }
        
        # Tentative d'annulation de la tâche Celery si elle est en cours
        if CELERY_AVAILABLE and celery_app and task.status in ["pending", "running"]:
            try:
                celery_app.control.revoke(task_id, terminate=True)
                logger.info(f"✅ CELERY TASK REVOKED: {task_id}")
            except Exception as e:
                logger.warning(f"⚠️ FAILED TO REVOKE CELERY TASK: {e}")
        
        # Mise à jour du statut en base
        task.status = "cancelled"
        task.error = "Task cancelled by user"
        task.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": f"Task {task_id} cancelled successfully",
            "task_id": task_id,
            "action": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ DELETE TASK FAILED: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete/cancel task")

# =====================================
# ENDPOINT DE DEBUG CELERY (optionnel)
# =====================================

@app.post("/debug/test-celery")
async def test_celery():
    """Test rapide de Celery"""
    if not CELERY_AVAILABLE or not celery_app:
        raise HTTPException(
            status_code=503,
            detail="Celery not available"
        )
    
    try:
        # Test simple
        result = celery_app.send_task('app.celery_app.test_task', args=['api_test'])
        
        return {
            "status": "success",
            "task_id": result.id,
            "message": "Test task sent to Celery"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Celery test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)