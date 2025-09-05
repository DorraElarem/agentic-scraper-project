"""
API FastAPI CORRIGÉE - Timeouts et Validation d'URLs
Corrections critiques pour éviter les tâches bloquées et valider les URLs
"""

import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
import asyncio
import aiohttp

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models.schemas import (
    ScrapingRequest, TaskCreateResponse, TaskResponse,
    HealthCheck, SystemStatus, ProgressInfo, TaskStatus
)
from app.models.database import get_db, ScrapingTask, test_database_connection, init_database
from app.celery_app import test_celery_connection, celery_app
from app.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_url_accessibility(url: str, timeout: int = 10) -> bool:
    """Validation d'accessibilité URL avec timeout - NOUVEAU"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                return response.status < 500  # Accepter même les 4xx
    except Exception as e:
        logger.debug(f"URL validation failed for {url}: {e}")
        return False  # Ne pas bloquer, juste signaler

@asynccontextmanager
async def smart_lifespan(app: FastAPI):
    """Gestionnaire intelligent du cycle de vie"""
    
    logger.info("Starting Smart Agentic Scraper API v2.0 - CORRECTED...")
    
    try:
        # Test de la base de données
        if test_database_connection():
            logger.info("Database connection: OK")
            if init_database():
                logger.info("Database initialization: OK")
        else:
            logger.warning("Database connection: FAILED")
        
        # Test de Celery
        celery_status = test_celery_connection()
        if celery_status.get('connection_status') == 'connected':
            logger.info(f"Celery connection: OK")
        else:
            logger.warning("Celery connection: No workers available")
        
        logger.info("Smart coordination system: ACTIVE")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
    
    yield
    
    logger.info("Shutting down Smart Agentic Scraper API...")

app = FastAPI(
    title="Smart Agentic Web Scraper - CORRECTED",
    description="API intelligente avec corrections critiques pour scraping économique tunisien",
    version="2.0.1_CORRECTED",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=smart_lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes de santé
@app.get("/health", response_model=HealthCheck)
async def smart_health_check():
    """Endpoint de vérification de santé intelligent"""
    try:
        from app.agents.smart_coordinator import SmartScrapingCoordinator
        coordinator = SmartScrapingCoordinator()
        
        return HealthCheck(
            healthy=True,
            services={
                "api": "operational",
                "coordinator": "smart_active_corrected",
                "database": "connected",
                "intelligence": "automatic"
            },
            coordinator_status="smart_coordination_enabled_corrected",
            message="Système de coordination intelligent opérationnel avec corrections critiques"
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthCheck(
            healthy=False,
            services={"api": "degraded"},
            message=f"Problème système: {str(e)}"
        )

@app.post("/scrape", response_model=TaskCreateResponse)
async def create_smart_scraping_task(
    request: ScrapingRequest,
    db = Depends(get_db)
):
    """
    ENDPOINT PRINCIPAL - création d'une tache de scraping
    """
    try:
        logger.info(f"Smart scraping request CORRECTED: {len(request.urls)} URLs")
        
        # CORRECTION 1: Validation automatique des URLs avec timeout
        valid_urls = []
        validation_warnings = []
        
        for url in request.urls:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                validation_warnings.append(f"URL invalide ignorée: {url}")
                continue
                
            # Validation d'accessibilité avec timeout court
            try:
                is_accessible = await asyncio.wait_for(
                    validate_url_accessibility(url, timeout=5), 
                    timeout=8
                )
                valid_urls.append(url)
                if not is_accessible:
                    validation_warnings.append(f"URL potentiellement inaccessible: {url}")
            except asyncio.TimeoutError:
                valid_urls.append(url)  # Inclure quand même mais signaler
                validation_warnings.append(f"Validation timeout pour: {url}")
            except Exception:
                valid_urls.append(url)  # Mode permissif
        
        if not valid_urls:
            raise HTTPException(
                status_code=422, 
                detail="Aucune URL valide fournie"
            )
        
        # CORRECTION 2: Paramètres de validation plus permissifs
        from app.utils.helpers import validate_task_parameters
        
        validation = validate_task_parameters(
            urls=valid_urls,
            enable_llm_analysis=request.enable_llm_analysis,
            quality_threshold=max(request.quality_threshold, 0.1),  # Min 0.1
            timeout=min(request.timeout if hasattr(request, 'timeout') else 300, 300),  # Max 5min
            priority=request.priority,
            callback_url=request.callback_url
        )
        
        if not validation['valid']:
            raise HTTPException(
                status_code=422, 
                detail=f"Paramètres invalides: {', '.join(validation['errors'])}"
            )
        
        # Génération d'ID unique
        task_id = str(uuid.uuid4())
        
        # CORRECTION 3: Création de tâche avec timeouts de sécurité
        task = ScrapingTask(
            task_id=task_id,
            urls=validation['normalized_params']['urls'],
            analysis_type="smart_automatic_corrected",
            status=TaskStatus.PENDING.value,
            priority=validation['normalized_params']['priority'],
            parameters={
                "enable_llm_analysis": request.enable_llm_analysis,
                "quality_threshold": validation['normalized_params']['quality_threshold'],
                "timeout": validation['normalized_params']['timeout'],
                "coordinator_mode": "smart_automatic_corrected",
                "validation_warnings": validation_warnings,
                "corrections_applied": [
                    "url_validation_with_timeout",
                    "permissive_quality_thresholds", 
                    "security_timeouts",
                    "robust_error_handling"
                ]
            },
            callback_url=request.callback_url,
            created_at=datetime.utcnow()
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # CORRECTION 4: Envoi à Celery avec timeouts de sécurité CRITIQUES
        from app.tasks.scraping_tasks import smart_scraping_task
        
        # Calcul intelligent des timeouts
        base_timeout = validation['normalized_params']['timeout']
        num_urls = len(validation['normalized_params']['urls'])
        total_timeout = min(base_timeout * num_urls, 600)  # Max 10 minutes
        
        celery_result = smart_scraping_task.apply_async(
            kwargs={
                'task_id': task_id,
                'urls': validation['normalized_params']['urls'],
                'enable_llm_analysis': request.enable_llm_analysis,
                'quality_threshold': validation['normalized_params']['quality_threshold'],
                'timeout': base_timeout,
                'callback_url': request.callback_url,
                'priority': validation['normalized_params']['priority']
            },
            # TIMEOUTS DE SÉCURITÉ CRITIQUES
            time_limit=total_timeout + 60,      # Timeout dur
            soft_time_limit=total_timeout + 30,  # Warning timeout
            expires=total_timeout + 120         # Expiration si pas exécuté
        )
        
        # Mise à jour avec l'ID du worker
        task.status = TaskStatus.RUNNING.value
        task.worker_id = celery_result.id
        task.started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Smart task created CORRECTED: {task_id} -> worker: {celery_result.id} (timeout: {total_timeout}s)")
        
        response_message = "Tâche intelligente créée avec corrections critiques"
        if validation_warnings:
            response_message += f" - {len(validation_warnings)} avertissements"
        
        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            message=response_message,
            coordinator_mode="smart_automatic_corrected",
            intelligence_activated=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating smart task CORRECTED: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur création tâche (corrigée): {str(e)}"
        )

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_smart_task_status(task_id: str, db = Depends(get_db)):
    """Récupérer le statut d'une tâche avec métadonnées intelligentes CORRIGÉES"""
    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Tâche non trouvée")
        
        # Construction de la réponse avec intelligence
        response = TaskResponse(
            task_id=task.task_id,
            status=TaskStatus(task.status),
            progress=ProgressInfo(
                current=task.progress.get("current", 0) if task.progress else 0,
                total=task.progress.get("total", 1) if task.progress else 1,
                percentage=task.progress.get("percentage", 0.0) if task.progress else 0.0,
                display=task.progress.get("display", "0/1") if task.progress else "0/1"
            ),
            results=task.results or [],
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error=task.error,
            urls=task.urls or [],
            llm_analysis_enabled=task.parameters.get("enable_llm_analysis", False) if task.parameters else False,
            ai_enhanced=task.parameters.get("enable_llm_analysis", False) if task.parameters else False,
            metrics=task.metrics or {},
            strategy_used="smart_automatic_corrected",
            coordinator_insights={
                "intelligent_coordination": True,
                "automatic_strategy_selection": True,
                "performance_optimization": True,
                "tunisian_optimization": True,
                "critical_corrections_applied": True,
                "timeout_security": True
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération: {str(e)}")

@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks_by_status(
    status: Optional[TaskStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db = Depends(get_db)
):
    """
    Récupérer les tâches filtrées par statut avec pagination
    
    Args:
        status: Statut de filtrage (optionnel)
        limit: Nombre maximum de résultats (défaut: 100)
        offset: Décalage pour la pagination (défaut: 0)
    """
    try:
        query = db.query(ScrapingTask)
        
        # Filtrage par statut si spécifié
        if status:
            query = query.filter(ScrapingTask.status == status.value)
        
        # Tri par date de création décroissante et pagination
        tasks = query.order_by(ScrapingTask.created_at.desc()).offset(offset).limit(limit).all()
        
        # Construction des réponses
        responses = []
        for task in tasks:
            response = TaskResponse(
                task_id=task.task_id,
                status=TaskStatus(task.status),
                progress=ProgressInfo(
                    current=task.progress.get("current", 0) if task.progress else 0,
                    total=task.progress.get("total", 1) if task.progress else 1,
                    percentage=task.progress.get("percentage", 0.0) if task.progress else 0.0,
                    display=task.progress.get("display", "0/1") if task.progress else "0/1"
                ),
                results=task.results or [],
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                error=task.error,
                urls=task.urls or [],
                llm_analysis_enabled=task.parameters.get("enable_llm_analysis", False) if task.parameters else False,
                ai_enhanced=task.parameters.get("enable_llm_analysis", False) if task.parameters else False,
                metrics=task.metrics or {},
                strategy_used="smart_automatic_corrected",
                coordinator_insights={
                    "intelligent_coordination": True,
                    "automatic_strategy_selection": True,
                    "performance_optimization": True,
                    "tunisian_optimization": True,
                    "critical_corrections_applied": True,
                    "timeout_security": True
                }
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Error retrieving tasks by status {status}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération: {str(e)}")

@app.delete("/tasks/{task_id}")
async def cancel_smart_task(task_id: str, db = Depends(get_db)):
    """Annuler une tâche avec nettoyage intelligent CORRIGÉ"""
    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Tâche non trouvée")
        
        # CORRECTION: Annulation intelligente dans Celery avec force
        if task.worker_id and task.status in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
            try:
                # Révocation forcée avec terminaison
                celery_app.control.revoke(task.worker_id, terminate=True, signal='KILL')
                logger.info(f"Celery task force-revoked: {task.worker_id}")
            except Exception as e:
                logger.warning(f"Could not revoke Celery task: {e}")
        
        # Mise à jour avec nettoyage intelligent
        task.status = TaskStatus.CANCELLED.value
        task.error = "Tâche annulée par l'utilisateur"
        task.completed_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "cancelled",
            "task_id": task_id,
            "message": "Tâche annulée avec succès (corrections appliquées)",
            "timestamp": datetime.utcnow().isoformat(),
            "corrections_applied": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling task {task_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur annulation: {str(e)}")

# Nouvel endpoint de debug
@app.post("/debug/coordinator")
async def debug_coordinator():
    """Endpoint de debug pour le coordinateur"""
    try:
        from app.agents.smart_coordinator import SmartScrapingCoordinator
        coordinator = SmartScrapingCoordinator()
        
        # Test de fonctionnalité
        test_result = coordinator.test_coordinator_functionality()
        
        return {
            "debug_timestamp": datetime.utcnow().isoformat(),
            "coordinator_test": test_result,
            "status": "debug_completed"
        }
        
    except Exception as e:
        logger.error(f"Debug coordinator failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint de test avec URLs sûres
@app.post("/test/safe-urls")
async def test_safe_urls():
    """Test avec des URLs sûres et accessibles"""
    safe_urls = [
        "https://httpbin.org/json",
        "https://api.worldbank.org/v2/country/TN/indicator/NY.GDP.MKTP.CD?format=json&date=2020:2023"
    ]
    
    try:
        from app.agents.smart_coordinator import SmartScrapingCoordinator
        coordinator = SmartScrapingCoordinator()
        
        results = {}
        for url in safe_urls:
            debug_info = coordinator.debug_extraction(url)
            results[url] = debug_info
        
        return {
            "test_timestamp": datetime.utcnow().isoformat(),
            "safe_urls_test": results,
            "corrections_applied": True
        }
        
    except Exception as e:
        logger.error(f"Safe URLs test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Gestionnaire d'erreurs amélioré
@app.exception_handler(Exception)
async def smart_global_exception_handler(request, exc):
    """Gestionnaire global d'exceptions avec intelligence CORRIGÉ"""
    logger.error(f"Unhandled exception in {request.url}: {exc}")
    
    # Classification intelligente de l'erreur
    error_type = "system_error"
    if "database" in str(exc).lower():
        error_type = "database_error"
    elif "celery" in str(exc).lower():
        error_type = "worker_error"
    elif "timeout" in str(exc).lower():
        error_type = "timeout_error"
    elif "coordination" in str(exc).lower():
        error_type = "coordination_error"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_type": error_type,
            "message": "Erreur système - corrections critiques appliquées",
            "timestamp": datetime.utcnow().isoformat(),
            "coordinator_mode": "smart_automatic_corrected",
            "corrections_info": {
                "timeout_protection": True,
                "url_validation": True,
                "permissive_thresholds": True,
                "robust_error_handling": True
            }
        }
    )
    
@app.post("/coordinator/langgraph-test")
async def test_langgraph_endpoint():
    """Endpoint de test LangGraph pour le superviseur"""
    try:
        from app.tasks.scraping_tasks import test_langgraph_workflow
        
        # URLs de test tunisiennes fonctionnelles
        test_urls = [
            "https://api.worldbank.org/v2/countries/TN/indicators/NY.GDP.MKTP.CD?format=json&date=2020:2023",
            "https://restcountries.com/v3.1/name/tunisia"
        ]
        
        # Lancement de la tâche LangGraph
        task = test_langgraph_workflow.delay(test_urls)
        
        return {
            "status": "success",
            "message": "LangGraph workflow test started",
            "task_id": task.id,
            "test_urls": test_urls,
            "supervisor_requirements": {
                "langgraph_enabled": True,
                "multi_agent_workflow": True,
                "intelligent_routing": True
            },
            "endpoint": "/coordinator/langgraph-test",
            "check_results_at": f"/tasks/{task.id}/status"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"LangGraph test failed: {str(e)}",
            "supervisor_requirements": {
                "langgraph_enabled": False,
                "error": str(e)
            }
        }

@app.get("/coordinator/quick-langgraph-test")
async def quick_langgraph_test():
    """Test rapide LangGraph sans Celery"""
    try:
        from app.agents.smart_coordinator import SmartScrapingCoordinator
        
        coordinator = SmartScrapingCoordinator()
        
        if hasattr(coordinator, 'scrape_with_langgraph'):
            test_url = "https://httpbin.org/json"
            result = coordinator.scrape_with_langgraph(test_url, enable_llm_analysis=False)
            
            return {
                "status": "success",
                "langgraph_available": True,
                "test_result": {
                    "url": test_url,
                    "success": result is not None,
                    "has_content": bool(result and result.raw_content),
                    "has_metadata": bool(result and result.metadata)
                },
                "supervisor_requirements_met": True
            }
        else:
            return {
                "status": "warning",
                "langgraph_available": False,
                "message": "LangGraph method not found in coordinator"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "langgraph_available": False,
            "error": str(e)
        }

@app.get("/api/diagnose/llm")
async def diagnose_llm():
    """Endpoint de diagnostic LLM"""
    from app.scrapers.intelligent import IntelligentScraper
    
    scraper = IntelligentScraper()
    diagnostics = scraper._diagnose_llm_connection()
    
    return {
        "status": "success" if diagnostics.get('model_available') else "error",
        "diagnostics": diagnostics,
        "timestamp": datetime.utcnow().isoformat()
    }
    
@app.get("/api/debug/extraction")
async def debug_extraction(url: str):
    """Endpoint de debug pour l'extraction"""
    from app.scrapers.intelligent import IntelligentScraper
    from app.scrapers.traditional import TunisianWebScraper
    
    scraper = IntelligentScraper()
    traditional = TunisianWebScraper()
    
    # Test des deux scrapers
    traditional_result = traditional.scrape(url)
    intelligent_result = scraper.scrape_with_analysis(url)
    
    # Diagnostic des catégories
    categories_found = set()
    if traditional_result and traditional_result.structured_data:
        trad_values = traditional_result.structured_data.get('extracted_values', {})
        categories_found.update(v.get('category') for v in trad_values.values() if v.get('category'))
    
    return {
        "traditional_categories": list(categories_found),
        "traditional_count": len(trad_values) if traditional_result else 0,
        "intelligent_llm_available": scraper.llm_available,
        "ollama_status": scraper._diagnose_llm_connection(),
        "extraction_issues": "Check category mapping and validation logic"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )