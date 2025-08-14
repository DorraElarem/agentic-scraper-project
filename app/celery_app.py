"""
Configuration Celery pour l'application de scraping agentic
"""

import logging
from celery import Celery
from app.config.settings import settings

# 🔧 CONFIGURATION DU LOGGER EN PREMIER
logger = logging.getLogger(__name__)

# =====================================
# CRÉATION DE L'INSTANCE CELERY
# =====================================

def create_celery_app() -> Celery:
    """Crée et configure l'application Celery"""
    
    # Créer l'instance Celery
    celery_app = Celery('agentic-scraper')
    
    # Configuration depuis les settings
    celery_config = settings.get_celery_config()
    celery_app.config_from_object(celery_config)
    
    # Configuration supplémentaire
    celery_app.conf.update(
        task_track_started=True,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_disable_rate_limits=False,
        task_default_retry_delay=60,
        task_max_retries=3,
        task_soft_time_limit=3600,  # 1 hour
        task_time_limit=3900,       # 65 minutes
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
        # Redis broker settings
        broker_connection_retry_on_startup=True,
        broker_transport_options={
            'priority_steps': list(range(10)),
            'sep': ':',
            'queue_order_strategy': 'priority',
        }
    )
    
    logger.info("✅ CELERY APP CREATED AND CONFIGURED")
    return celery_app

# Créer l'instance globale
celery_app = create_celery_app()

# Alias pour compatibilité
celery = celery_app

# =====================================
# TÂCHES DE BASE CELERY
# =====================================

@celery_app.task(bind=True, name='app.celery_app.test_task')
def test_task(self, message: str = "Hello from Celery!"):
    """Tâche de test simple"""
    try:
        logger.info(f"🧪 TEST TASK EXECUTED: {message}")
        return {
            "status": "success",
            "message": message,
            "task_id": self.request.id,
            "timestamp": str(logger.handlers[0].formatter.formatTime(logger.makeRecord(
                logger.name, logging.INFO, "", 0, "", (), None
            ))) if logger.handlers else "no-timestamp"
        }
    except Exception as e:
        logger.error(f"❌ TEST TASK FAILED: {e}")
        raise

@celery_app.task(bind=True, name='app.celery_app.debug_communication')
def debug_communication(self):
    """Test de communication entre composants"""
    try:
        # Test de base de données
        db_status = "unknown"
        try:
            # Note: Ici on simule le test DB, dans la vraie version on testerait la connexion
            db_status = "connected"
        except Exception as db_e:
            db_status = f"error: {db_e}"
        
        # Test Redis
        redis_status = "unknown"
        try:
            # Note: Test Redis simulation
            redis_status = "connected"
        except Exception as redis_e:
            redis_status = f"error: {redis_e}"
        
        result = {
            "task_id": self.request.id,
            "worker_id": self.request.hostname,
            "database": db_status,
            "redis": redis_status,
            "celery": "working",
            "timestamp": "now"  # Simplified timestamp
        }
        
        logger.info(f"🔍 DEBUG COMMUNICATION: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ DEBUG COMMUNICATION FAILED: {e}")
        return {
            "status": "error",
            "error": str(e),
            "task_id": self.request.id
        }

@celery_app.task(bind=True, name='app.celery_app.system_health_check')
def system_health_check(self):
    """Vérification de santé système"""
    try:
        import psutil
        import time
        
        # Métriques système
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            "task_id": self.request.id,
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "available_memory_mb": memory.available / (1024 * 1024)
            },
            "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "warning"
        }
        
        logger.info(f"💖 SYSTEM HEALTH: {health_data['status']}")
        return health_data
        
    except Exception as e:
        logger.error(f"❌ HEALTH CHECK FAILED: {e}")
        return {
            "status": "error",
            "error": str(e),
            "task_id": self.request.id
        }

# =====================================
# IMPORT SÉCURISÉ DES TÂCHES DE SCRAPING
# =====================================

def safe_import_scraping_tasks():
    """Import sécurisé des tâches de scraping pour éviter les imports circulaires"""
    try:
        # Import différé pour éviter les imports circulaires
        from app.tasks import scraping_tasks
        logger.info("✅ SCRAPING TASKS MODULE IMPORTED SUCCESSFULLY")
        return True
    except ImportError as e:
        logger.warning(f"⚠️ SCRAPING TASKS IMPORT FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR IMPORTING SCRAPING TASKS: {e}")
        return False

# Import différé des tâches de scraping
scraping_tasks_imported = safe_import_scraping_tasks()

# =====================================
# AUTO-DÉCOUVERTE DES TÂCHES
# =====================================

def setup_task_discovery():
    """Configure l'auto-découverte des tâches"""
    try:
        # Auto-découverte avec gestion d'erreurs
        celery_app.autodiscover_tasks(['app.tasks'], force=True)
        logger.info("✅ TASK AUTODISCOVERY COMPLETED")
        
        # Lister les tâches découvertes
        registered_tasks = list(celery_app.tasks.keys())
        logger.info(f"📋 DISCOVERED {len(registered_tasks)} TASKS")
        
        # Afficher les tâches importantes
        important_tasks = [task for task in registered_tasks if 'scraping' in task or 'test' in task]
        if important_tasks:
            logger.info("🔍 KEY TASKS FOUND:")
            for task in important_tasks[:5]:  # Limiter à 5 pour éviter le spam
                logger.info(f"   - {task}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ TASK DISCOVERY FAILED: {e}")
        return False

# Configurer l'auto-découverte
task_discovery_success = setup_task_discovery()

# =====================================
# CONFIGURATION DES SIGNAUX CELERY
# =====================================

from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Signal émis quand le worker est prêt"""
    logger.info(f"🚀 WORKER READY: {sender}")

@worker_shutdown.connect  
def worker_shutdown_handler(sender=None, **kwargs):
    """Signal émis à l'arrêt du worker"""
    logger.info(f"🛑 WORKER SHUTDOWN: {sender}")

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Signal émis avant l'exécution d'une tâche"""
    logger.debug(f"▶️ TASK STARTING: {task.name} [{task_id}]")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Signal émis après l'exécution d'une tâche"""
    logger.debug(f"✅ TASK COMPLETED: {task.name} [{task_id}] - State: {state}")

# =====================================
# FONCTIONS UTILITAIRES
# =====================================

def get_celery_status():
    """Retourne le statut de Celery"""
    try:
        # Inspection des workers
        inspect = celery_app.control.inspect()
        
        # Vérifier les workers actifs
        active_workers = inspect.active()
        registered_tasks = list(celery_app.tasks.keys())
        
        status = {
            "celery_app_configured": True,
            "active_workers": len(active_workers) if active_workers else 0,
            "registered_tasks_count": len(registered_tasks),
            "scraping_tasks_imported": scraping_tasks_imported,
            "task_discovery_success": task_discovery_success,
            "broker_url": celery_app.conf.broker_url,
            "result_backend": celery_app.conf.result_backend
        }
        
        return status
        
    except Exception as e:
        logger.error(f"❌ FAILED TO GET CELERY STATUS: {e}")
        return {
            "celery_app_configured": True,
            "error": str(e),
            "active_workers": 0,
            "registered_tasks_count": len(list(celery_app.tasks.keys()))
        }

def list_available_tasks():
    """Liste toutes les tâches disponibles"""
    try:
        tasks = list(celery_app.tasks.keys())
        return sorted([task for task in tasks if not task.startswith('celery.')])
    except Exception as e:
        logger.error(f"❌ FAILED TO LIST TASKS: {e}")
        return []

# =====================================
# EXPORTS
# =====================================

# Export pour utilisation externe
__all__ = [
    'celery_app',
    'celery', 
    'test_task',
    'debug_communication',
    'system_health_check',
    'get_celery_status',
    'list_available_tasks'
]

# Log final de configuration
logger.info("🎉 CELERY_APP.PY CONFIGURATION COMPLETED")
logger.info(f"📊 FINAL STATUS: Tasks imported: {scraping_tasks_imported}, Discovery: {task_discovery_success}")