#!/usr/bin/env python3
"""
Worker Celery intelligent avec diagnostics automatiques
Version simplifiée sans paramètres complexes
"""
import os
import sys
import time
import logging
import argparse
from typing import Dict, Any, List, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_services(max_retries: int = 30) -> bool:
    """Attendre que les services soient prêts"""
    logger.info("⏳ Attente des services...")
    
    services_ready = False
    for attempt in range(max_retries):
        try:
            # Test Redis
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            
            # Test base de données
            from app.models.database import test_db_connection
            if test_db_connection():
                services_ready = True
                break
                
        except Exception as e:
            logger.debug(f"Tentative {attempt + 1}/{max_retries}: {e}")
            time.sleep(2)
    
    if services_ready:
        logger.info("✅ Services prêts")
        return True
    else:
        logger.error("❌ Services non disponibles après attente")
        return False

def run_basic_diagnostics() -> Dict[str, Any]:
    """Diagnostics de base du système"""
    logger.info("🧪 Diagnostics de base...")
    
    diagnostics = {
        'timestamp': time.time(),
        'status': 'unknown',
        'checks': {}
    }
    
    try:
        # 1. Test configuration
        try:
            from app.config.settings import get_settings
            settings = get_settings()
            diagnostics['checks']['configuration'] = {
                'status': 'ok',
                'database_url': bool(settings.database_url),
                'redis_url': bool(settings.redis_url)
            }
        except Exception as e:
            diagnostics['checks']['configuration'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # 2. Test base de données
        try:
            from app.models.database import test_db_connection
            db_ok = test_db_connection()
            diagnostics['checks']['database'] = {
                'status': 'ok' if db_ok else 'error',
                'connected': db_ok
            }
        except Exception as e:
            diagnostics['checks']['database'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # 3. Test Redis
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            diagnostics['checks']['redis'] = {
                'status': 'ok',
                'connected': True
            }
        except Exception as e:
            diagnostics['checks']['redis'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # 4. Test imports principaux
        try:
            from app.agents.smart_coordinator import SmartScrapingCoordinator
            from app.tasks.scraping_tasks import smart_scrape_task
            diagnostics['checks']['imports'] = {
                'status': 'ok',
                'coordinator': True,
                'tasks': True
            }
        except Exception as e:
            diagnostics['checks']['imports'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Déterminer statut global
        all_ok = all(
            check.get('status') == 'ok' 
            for check in diagnostics['checks'].values()
        )
        
        diagnostics['status'] = 'ok' if all_ok else 'error'
        
        logger.info(f"📊 Diagnostics: {diagnostics['status']}")
        return diagnostics
        
    except Exception as e:
        logger.error(f"❌ Erreur diagnostics: {e}")
        diagnostics['status'] = 'error'
        diagnostics['error'] = str(e)
        return diagnostics

def start_celery_worker(concurrency: int = 1, loglevel: str = 'info') -> None:
    """Démarrer le worker Celery"""
    logger.info("🔧 Démarrage du worker Celery...")
    
    try:
        # Import de l'app Celery
        from app.celery_app import celery_app
        
        # Configuration du worker
        worker_args = [
            'worker',
            f'--concurrency={concurrency}',
            f'--loglevel={loglevel}',
            '--queues=scraping,monitoring,testing',
            '--pool=solo' if os.name == 'nt' else '--pool=prefork',  # Windows compatibility
        ]
        
        logger.info(f"🚀 Lancement worker avec args: {' '.join(worker_args)}")
        
        # Démarrer le worker
        celery_app.worker_main(worker_args)
        
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt du worker demandé")
    except Exception as e:
        logger.error(f"❌ Erreur worker: {e}")
        sys.exit(1)

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Worker Celery intelligent')
    parser.add_argument('--concurrency', type=int, default=1, help='Nombre de processus worker')
    parser.add_argument('--loglevel', default='info', choices=['debug', 'info', 'warning', 'error'])
    parser.add_argument('--skip-diagnostics', action='store_true', help='Ignorer les diagnostics')
    parser.add_argument('--skip-wait', action='store_true', help='Ignorer l\'attente des services')
    
    args = parser.parse_args()
    
    try:
        # 1. Attendre les services (sauf si skip)
        if not args.skip_wait:
            if not wait_for_services():
                logger.error("❌ Services non disponibles")
                sys.exit(1)
        
        # 2. Diagnostics de base (sauf si skip)
        if not args.skip_diagnostics:
            diagnostics = run_basic_diagnostics()
            if diagnostics['status'] != 'ok':
                logger.warning("⚠️ Diagnostics avec erreurs, mais démarrage quand même")
        
        # 3. Démarrer le worker
        start_celery_worker(
            concurrency=args.concurrency,
            loglevel=args.loglevel
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()