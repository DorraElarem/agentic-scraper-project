"""
Configuration Celery intelligente avec intelligence automatique
"""
import os
import logging
from typing import List, Dict, Any, Optional
from celery import Celery
from celery.signals import worker_ready, task_prerun, task_postrun, task_failure

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_celery_app() -> Celery:
    """Créer l'application Celery avec configuration intelligente"""
    
    # Configuration Redis avec fallbacks
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    
    # Configuration Celery optimisée
    celery_config = {
        'broker_url': redis_url,
        'result_backend': redis_url,
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'timezone': 'Africa/Tunis',
        'enable_utc': True,
        
        # Queues intelligentes
        'task_routes': {
            'app.tasks.scraping_tasks.smart_scrape_task': {'queue': 'scraping'},
            'app.tasks.scraping_tasks.smart_health_check': {'queue': 'monitoring'},
            'app.celery_app.smart_test_task': {'queue': 'testing'},
        },
        
        # Performance optimisée
        'worker_prefetch_multiplier': 1,
        'task_acks_late': True,
        'worker_max_tasks_per_child': 1000,
        'task_time_limit': 300,  # 5 minutes
        'task_soft_time_limit': 240,  # 4 minutes
        
        # Retry intelligent
        'task_default_retry_delay': 60,
        'task_max_retries': 3,
        
        # Monitoring
        'worker_send_task_events': True,
        'task_send_sent_event': True,
    }
    
    # Créer l'app Celery
    celery_app = Celery('smart_scraper')
    celery_app.config_from_object(celery_config)
    
    # Auto-découverte des tâches
    celery_app.autodiscover_tasks([
        'app.tasks.scraping_tasks'
    ])
    
    return celery_app

# Créer l'instance globale
celery_app = create_celery_app()

@celery_app.task(bind=True, name='app.celery_app.smart_test_task')
def smart_test_task(self) -> Dict[str, Any]:
    """Tâche de test pour validation du système intelligent"""
    try:
        import time
        start_time = time.time()
        
        # Test simple
        result = {
            'status': 'success',
            'message': 'Système intelligent opérationnel',
            'worker_id': self.request.id,
            'execution_time': time.time() - start_time,
            'intelligence_level': 'auto',
            'system_health': 'ok'
        }
        
        logger.info(f"✅ Test intelligent réussi: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur test intelligent: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'worker_id': getattr(self.request, 'id', 'unknown')
        }

# Signaux pour monitoring intelligent
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Signal quand worker est prêt"""
    logger.info("🚀 Worker Celery intelligent prêt")
    
    # Test de santé automatique au démarrage
    try:
        result = smart_test_task.delay()
        logger.info(f"✅ Test de santé lancé: {result.id}")
    except Exception as e:
        logger.error(f"❌ Erreur test de santé: {e}")

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Avant exécution de tâche"""
    logger.debug(f"🔄 Démarrage tâche: {task.name} [{task_id}]")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Après exécution de tâche"""
    logger.debug(f"✅ Tâche terminée: {task.name} [{task_id}] - État: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, einfo=None, **kwds):
    """En cas d'échec de tâche"""
    logger.error(f"❌ Échec tâche: {sender.name} [{task_id}] - Erreur: {exception}")

def test_celery_connection() -> Dict[str, Any]:
    """Test de connexion Celery intelligent"""
    try:
        # Test de base
        inspect = celery_app.control.inspect()
        
        # Vérifier workers actifs
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        
        if not active_workers:
            return {
                'status': 'warning',
                'message': 'Aucun worker actif détecté',
                'workers_count': 0,
                'registered_tasks': len(registered_tasks) if registered_tasks else 0
            }
        
        # Test avec tâche simple
        test_result = smart_test_task.delay()
        
        return {
            'status': 'success',
            'message': 'Connexion Celery opérationnelle',
            'workers_count': len(active_workers),
            'test_task_id': test_result.id,
            'registered_tasks': len(registered_tasks) if registered_tasks else 0,
            'intelligence_mode': 'auto'
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur test Celery: {e}")
        return {
            'status': 'error',
            'message': f'Erreur connexion Celery: {str(e)}',
            'workers_count': 0
        }

# Export pour imports
__all__ = ['celery_app', 'test_celery_connection', 'smart_test_task']