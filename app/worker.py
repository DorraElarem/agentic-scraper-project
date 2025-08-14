#!/usr/bin/env python3
"""
Worker Celery pour l'agentic scraper
Point d'entrée principal pour le worker avec gestion d'erreurs et diagnostics
"""

import sys
import os
import logging
from datetime import datetime
from app.config.settings import settings

# Configuration des logs pour le worker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Fonction principale du worker avec diagnostics intégrés"""
    logger.info(f"🚀 WORKER STARTING AT {datetime.utcnow()}")
    
    try:
        # Test des imports critiques avant de démarrer Celery
        logger.info("🔧 Testing critical imports...")
        
        # Test 1: Configuration
        try:
            from app.config.settings import settings
            logger.info(f"✅ Settings imported - DEFAULT_DELAY: {settings.DEFAULT_DELAY}")
        except Exception as e:
            logger.error(f"❌ Settings import failed: {e}")
            return 1
        
        # Test 2: Scrapers avec gestion des attributs optionnels
        try:
            from app.scrapers.traditional import TunisianWebScraper
            from app.scrapers.intelligent import IntelligentScraper
            
            # Test de création d'instances
            traditional = TunisianWebScraper()
            intelligent = IntelligentScraper()
            
            # 🔥 CORRECTION: Utiliser get_scraper_info() pour éviter les AttributeError
            traditional_info = traditional.get_scraper_info()
            logger.info(f"✅ Traditional scraper: delay={traditional_info.get('delay', 'unknown')}, max_length={traditional_info.get('max_content_length', 'unknown')}")
            
            # Pour intelligent scraper, utiliser getattr avec fallback
            intelligent_delay = getattr(intelligent, 'delay', 'unknown')
            logger.info(f"✅ Intelligent scraper: delay={intelligent_delay}")
            
        except Exception as e:
            logger.error(f"❌ Scrapers creation failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Test 3: Agent scraper
        try:
            from app.agents.scraper_agent import ScraperAgent
            agent = ScraperAgent("test_worker_agent")
            logger.info("✅ ScraperAgent created successfully")
        except Exception as e:
            logger.error(f"❌ ScraperAgent creation failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Test 4: Tâches de scraping avec nouvelle structure
        try:
            # Import du module sans importer la fonction directement
            import app.tasks.scraping_tasks
            
            # Utiliser l'enregistrement des tâches
            from app.tasks.scraping_tasks import register_tasks
            tasks = register_tasks()
            
            logger.info("✅ Scraping tasks imported successfully")
        except Exception as e:
            logger.error(f"❌ Scraping tasks import failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Test 5: Import de l'app Celery
        try:
            from app.celery_app import celery_app
            logger.info("✅ Celery app imported successfully")
        except Exception as e:
            logger.error(f"❌ Celery app import failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Vérification des tâches enregistrées
        registered_tasks = list(celery_app.tasks.keys())
        logger.info(f"📋 Registered tasks: {len(registered_tasks)}")
        
        important_tasks = [
            'app.tasks.scraping_tasks.enqueue_scraping_task',
            'app.celery_app.test_task',
            'app.celery_app.debug_communication'
        ]
        
        missing_tasks = []
        for task in important_tasks:
            if task in registered_tasks:
                logger.info(f"✅ Task available: {task}")
            else:
                logger.warning(f"❌ Task missing: {task}")
                missing_tasks.append(task)
        
        if missing_tasks:
            logger.error(f"❌ Critical tasks missing: {missing_tasks}")
            logger.info("📋 Available tasks:")
            for task in sorted(registered_tasks):
                logger.info(f"   - {task}")
            return 1
        
        # Test de connectivité Redis
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            logger.info(f"✅ Redis connection OK: {redis_url}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return 1
        
        logger.info("✅ ALL DIAGNOSTICS PASSED - Starting Celery worker...")
        
        # Démarrer le worker Celery
        celery_app.start()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("ℹ️ Worker stopped by user")
        return 0
    except Exception as e:
        logger.error(f"💥 Worker startup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

def run_diagnostics_only():
    """Lance seulement les diagnostics sans démarrer le worker"""
    logger.info("🔍 RUNNING DIAGNOSTICS ONLY...")
    
    try:
        # Import et test de tous les composants
        from app.config.settings import settings
        from app.scrapers.traditional import TunisianWebScraper
        from app.scrapers.intelligent import IntelligentScraper
        from app.agents.scraper_agent import ScraperAgent
        from app.models.schemas import ScrapeRequest, AnalysisType
        import app.tasks.scraping_tasks
        from app.celery_app import celery_app
        
        # Test de création d'instances avec gestion d'erreurs
        traditional = TunisianWebScraper()
        intelligent = IntelligentScraper()
        agent = ScraperAgent("diagnostic_agent")
        
        # Test d'une requête de scraping
        request = ScrapeRequest(
            urls=["https://httpbin.org/json"], 
            analysis_type=AnalysisType.STANDARD
        )
        
        logger.info("✅ ALL COMPONENTS LOADED SUCCESSFULLY")
        
        # 🔥 CORRECTION: Utiliser les méthodes sécurisées pour obtenir les infos
        try:
            traditional_info = traditional.get_scraper_info()
            logger.info(f"✅ Traditional scraper: delay={traditional_info.get('delay', 'unknown')}, max_length={traditional_info.get('max_content_length', 'unknown')}")
        except Exception as e:
            # Fallback si get_scraper_info n'existe pas
            delay = getattr(traditional, 'delay', 'unknown')
            max_length = getattr(traditional, 'max_content_length', 'unknown')
            logger.info(f"✅ Traditional scraper: delay={delay}, max_length={max_length}")
        
        intelligent_delay = getattr(intelligent, 'delay', 'unknown')
        logger.info(f"✅ Intelligent scraper: delay={intelligent_delay}")
        
        agent_name = getattr(agent, 'name', 'unknown')
        logger.info(f"✅ Agent: {agent_name}")
        
        logger.info(f"✅ Test request: {len(request.urls)} URLs, type={request.analysis_type}")
        
        # Vérifier les tâches Celery
        registered_tasks = list(celery_app.tasks.keys())
        logger.info(f"✅ Celery tasks: {len(registered_tasks)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DIAGNOSTIC FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_extended_diagnostics():
    """Diagnostics étendus avec tests approfondis"""
    logger.info("🔬 RUNNING EXTENDED DIAGNOSTICS...")
    
    try:
        # Test des imports avec informations détaillées
        logger.info("📦 Testing module imports...")
        
        # Configuration
        from app.config.settings import settings
        logger.info(f"   ✅ Settings: DEFAULT_DELAY={settings.DEFAULT_DELAY}, TIMEOUT={settings.REQUEST_TIMEOUT}")
        
        # Scrapers
        from app.scrapers.traditional import TunisianWebScraper
        from app.scrapers.intelligent import IntelligentScraper
        
        traditional = TunisianWebScraper()
        intelligent = IntelligentScraper()
        
        # Test des méthodes clés
        traditional_methods = [method for method in dir(traditional) if not method.startswith('_')]
        intelligent_methods = [method for method in dir(intelligent) if not method.startswith('_')]
        
        logger.info(f"   ✅ Traditional scraper: {len(traditional_methods)} public methods")
        logger.info(f"   ✅ Intelligent scraper: {len(intelligent_methods)} public methods")
        
        # Agent
        from app.agents.scraper_agent import ScraperAgent
        agent = ScraperAgent("extended_diagnostic_agent")
        agent_status = agent.get_scraper_status()
        logger.info(f"   ✅ Agent status: {agent_status.get('agent_name', 'unknown')}")
        
        # Base de données
        from app.models.database import get_db
        with next(get_db()) as db:
            # Test simple de connexion
            result = db.execute("SELECT 1").fetchone()
            logger.info(f"   ✅ Database connection: result={result}")
        
        # Celery
        from app.celery_app import celery_app
        registered_tasks = list(celery_app.tasks.keys())
        important_tasks = [t for t in registered_tasks if 'app.' in t]
        logger.info(f"   ✅ Celery: {len(registered_tasks)} total tasks, {len(important_tasks)} app tasks")
        
        # Redis
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url)
        redis_info = r.info()
        logger.info(f"   ✅ Redis: version={redis_info.get('redis_version', 'unknown')}")
        
        logger.info("🎉 EXTENDED DIAGNOSTICS COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        logger.error(f"❌ EXTENDED DIAGNOSTICS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        if sys.argv[1] == '--diagnose-only':
            # Mode diagnostic seulement
            success = run_diagnostics_only()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == '--extended-diagnostics':
            # Mode diagnostic étendu
            success = run_extended_diagnostics()
            sys.exit(0 if success else 1)
        else:
            logger.warning(f"Unknown argument: {sys.argv[1]}")
            logger.info("Available options: --diagnose-only, --extended-diagnostics")
    
    # Mode normal - démarrer le worker
    sys.exit(main())