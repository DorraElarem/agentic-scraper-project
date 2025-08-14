#!/usr/bin/env python3
"""
🧪 TEST COMPLET POUR IDENTIFIER L'ERREUR INT('0/1')
==================================================
Ce script teste tous les composants individuellement pour identifier précisément
où l'erreur se produit dans votre chaîne d'exécution.
"""

import sys
import os
import traceback
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Teste les imports un par un pour identifier les erreurs"""
    print("🧪 TEST DES IMPORTS")
    print("=" * 50)
    
    tests = [
        ("os", lambda: __import__('os')),
        ("sys", lambda: __import__('sys')),
        ("uuid", lambda: __import__('uuid')),
        ("datetime", lambda: __import__('datetime')),
        ("logging", lambda: __import__('logging')),
        ("fastapi", lambda: __import__('fastapi')),
        ("sqlalchemy.orm", lambda: __import__('sqlalchemy.orm')),
        ("app.utils.helpers", lambda: __import__('app.utils.helpers')),
        ("app.models.database", lambda: __import__('app.models.database')),
        ("app.models.schemas", lambda: __import__('app.models.schemas')),
        ("app.tasks.scraping_tasks", lambda: __import__('app.tasks.scraping_tasks')),
    ]
    
    for name, import_func in tests:
        try:
            import_func()
            print(f"✅ {name}: OK")
        except Exception as e:
            print(f"❌ {name}: ERREUR - {str(e)}")
            traceback.print_exc()

def test_helper_functions():
    """Teste les fonctions helper individuellement"""
    print("\n🧪 TEST DES FONCTIONS HELPER")
    print("=" * 50)
    
    try:
        from app.utils.helpers import safe_parse_progress, validate_progress_pair, normalize_progress_string
        
        # Test 1: safe_parse_progress
        test_cases = [
            ("0", 0),
            ("5", 5), 
            ("0/1", 0),
            ("3/5", 3),
            ("10.5", 10),
            ("invalid", 0),
            (None, 0),
            (42, 42),
            ("  7.8  ", 7)
        ]
        
        print("🔍 Test safe_parse_progress:")
        for value, expected in test_cases:
            try:
                result = safe_parse_progress(value)
                status = "✅" if result == expected else "⚠️"
                print(f"   {status} safe_parse_progress({repr(value)}) = {result} (attendu: {expected})")
            except Exception as e:
                print(f"   ❌ safe_parse_progress({repr(value)}) = ERREUR: {e}")
        
        # Test 2: validate_progress_pair
        print("\n🔍 Test validate_progress_pair:")
        pair_tests = [
            ((0, 1), (0, 1)),
            (("0", "5"), (0, 5)),
            (("3/5", "10"), (3, 10)),
            ((None, None), (0, 1)),
        ]
        
        for (current, total), (exp_current, exp_total) in pair_tests:
            try:
                result_current, result_total = validate_progress_pair(current, total)
                status = "✅" if (result_current == exp_current and result_total == exp_total) else "⚠️"
                print(f"   {status} validate_progress_pair({repr(current)}, {repr(total)}) = ({result_current}, {result_total})")
            except Exception as e:
                print(f"   ❌ validate_progress_pair({repr(current)}, {repr(total)}) = ERREUR: {e}")
        
        # Test 3: normalize_progress_string
        print("\n🔍 Test normalize_progress_string:")
        norm_tests = ["0", "5", "3/5", 10, None, "invalid"]
        for value in norm_tests:
            try:
                result = normalize_progress_string(value)
                print(f"   ✅ normalize_progress_string({repr(value)}) = '{result}'")
            except Exception as e:
                print(f"   ❌ normalize_progress_string({repr(value)}) = ERREUR: {e}")
                
    except Exception as e:
        print(f"❌ Impossible d'importer les helpers: {e}")
        traceback.print_exc()

def test_database_models():
    """Teste les modèles de base de données"""
    print("\n🧪 TEST DES MODÈLES DATABASE")
    print("=" * 50)
    
    try:
        from app.models.database import ScrapingTask, get_db
        
        # Test creation d'un objet ScrapingTask
        print("🔍 Test création ScrapingTask:")
        task = ScrapingTask(
            task_id="test-123",
            urls=["https://example.com"],
            status="pending",
            progress_current="0",
            progress_total="1"
        )
        
        print(f"✅ Création task OK")
        print(f"   task_id: {task.task_id}")
        print(f"   progress_current: {task.progress_current} ({type(task.progress_current)})")
        print(f"   progress_total: {task.progress_total} ({type(task.progress_total)})")
        
        # Test des méthodes
        print("\n🔍 Test méthodes ScrapingTask:")
        
        try:
            display = task.progress_display
            print(f"✅ progress_display: '{display}'")
        except Exception as e:
            print(f"❌ progress_display: ERREUR - {e}")
            traceback.print_exc()
            
        try:
            progress_dict = task.get_progress_dict()
            print(f"✅ get_progress_dict: {progress_dict}")
        except Exception as e:
            print(f"❌ get_progress_dict: ERREUR - {e}")
            traceback.print_exc()
            
        try:
            success = task.set_progress("2", "5")
            print(f"✅ set_progress('2', '5'): {success}")
            print(f"   Nouveau current: {task.progress_current}")
            print(f"   Nouveau total: {task.progress_total}")
        except Exception as e:
            print(f"❌ set_progress: ERREUR - {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Erreur test modèles: {e}")
        traceback.print_exc()

def test_schemas():
    """Teste les schémas Pydantic"""
    print("\n🧪 TEST DES SCHÉMAS PYDANTIC")
    print("=" * 50)
    
    try:
        from app.models.schemas import ProgressDetail, ScrapingTaskRequest, AnalysisType
        
        # Test ProgressDetail
        print("🔍 Test ProgressDetail:")
        test_cases = [
            {"current": 0, "total": 1},
            {"current": "3", "total": "5"},
            {"current": "3/10", "total": "20"},
        ]
        
        for i, case in enumerate(test_cases):
            try:
                progress = ProgressDetail(**case)
                print(f"✅ Test {i+1}: current={progress.current}, total={progress.total}, display='{progress.display}'")
            except Exception as e:
                print(f"❌ Test {i+1}: ERREUR - {e}")
                traceback.print_exc()
        
        # Test ScrapingTaskRequest
        print("\n🔍 Test ScrapingTaskRequest:")
        try:
            request = ScrapingTaskRequest(
                urls=["https://example.com"],
                analysis_type=AnalysisType.STANDARD
            )
            print(f"✅ ScrapingTaskRequest créé: {request.urls}, {request.analysis_type}")
        except Exception as e:
            print(f"❌ ScrapingTaskRequest: ERREUR - {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Erreur test schémas: {e}")
        traceback.print_exc()

def test_celery_import():
    """Teste l'import de la tâche Celery"""
    print("\n🧪 TEST IMPORT CELERY TASK")
    print("=" * 50)
    
    try:
        from app.tasks.scraping_tasks import enqueue_scraping_task
        print(f"✅ Import enqueue_scraping_task: OK")
        
        # Affichage des infos de la tâche
        print(f"   Nom: {enqueue_scraping_task.name}")
        print(f"   Bind: {getattr(enqueue_scraping_task, 'bind', 'N/A')}")
        
        # Vérifier si apply_async est disponible
        if hasattr(enqueue_scraping_task, 'apply_async'):
            print(f"✅ apply_async disponible")
        else:
            print(f"❌ apply_async indisponible")
            
        # Vérifier si apply est disponible  
        if hasattr(enqueue_scraping_task, 'apply'):
            print(f"✅ apply disponible")
        else:
            print(f"❌ apply indisponible")
            
    except Exception as e:
        print(f"❌ Erreur import Celery task: {e}")
        traceback.print_exc()

def test_worker_connection():
    """Teste la connexion au worker Celery"""
    print("\n🧪 TEST CONNEXION WORKER")
    print("=" * 50)
    
    try:
        from app.worker import celery
        print("✅ Celery app trouvée")
        
        # Vérifier la configuration
        print(f"   Backend: {celery.conf.result_backend}")
        print(f"   Broker: {celery.conf.broker_url}")
        print(f"   Always Eager: {celery.conf.task_always_eager}")
        
        # Test basic du worker avec gestion d'erreur Redis
        try:
            inspect_result = celery.control.inspect()
            stats = inspect_result.stats()
            if stats:
                print(f"✅ Worker connecté: {list(stats.keys())}")
            else:
                print("❌ Aucun worker actif détecté")
        except Exception as redis_error:
            print(f"❌ Erreur connexion Redis/Worker: {str(redis_error)[:200]}...")
            if "getaddrinfo failed" in str(redis_error):
                print("💡 Solution: Configurez CELERY_ALWAYS_EAGER=True dans .env pour le développement")
                
    except Exception as e:
        print(f"❌ Erreur test worker: {e}")
        traceback.print_exc()

def test_celery_task_creation():
    """Teste la création de tâche Celery en mode simulation"""
    print("\n🧪 TEST SIMULATION CELERY TASK")
    print("=" * 50)
    
    try:
        # Simuler les étapes de création sans Celery réel
        from app.models.database import ScrapingTask
        from app.utils.helpers import validate_progress_pair, normalize_progress_string
        import uuid
        
        print("🔍 Simulation création tâche:")
        
        # Étape 1: Génération ID
        task_id = str(uuid.uuid4())
        print(f"✅ ID généré: {task_id}")
        
        # Étape 2: Validation URLs
        urls = ["https://www.ins.tn/statistiques"]
        total_urls = len(urls)
        print(f"✅ URLs validées: {total_urls} URLs")
        
        # Étape 3: Normalisation progression - ICI PEUT ÊTRE L'ERREUR
        try:
            safe_current, safe_total = validate_progress_pair(0, total_urls)
            print(f"✅ Progression normalisée: current={safe_current}, total={safe_total}")
            
            normalized_current = normalize_progress_string(safe_current)
            normalized_total = normalize_progress_string(safe_total)
            print(f"✅ Strings normalisées: current='{normalized_current}', total='{normalized_total}'")
            
        except Exception as e:
            print(f"❌ ERREUR lors de la normalisation: {e}")
            if "invalid literal for int()" in str(e) and "0/1" in str(e):
                print("🎯 ERREUR INT('0/1') TROUVÉE ICI!")
            traceback.print_exc()
            return
        
        # Étape 4: Création objet (sans DB)
        try:
            db_task = ScrapingTask(
                task_id=task_id,
                urls=urls,
                status="pending",
                progress_current=normalized_current,
                progress_total=normalized_total,
                analysis_type="standard",
                parameters={},
                priority=1,
                created_at=datetime.utcnow()
            )
            print(f"✅ Objet ScrapingTask créé")
            print(f"   progress_current: '{db_task.progress_current}' ({type(db_task.progress_current)})")
            print(f"   progress_total: '{db_task.progress_total}' ({type(db_task.progress_total)})")
            
            # Test des méthodes sur l'objet créé
            display = db_task.progress_display
            print(f"✅ progress_display: '{display}'")
            
            progress_dict = db_task.get_progress_dict()
            print(f"✅ get_progress_dict: {progress_dict}")
            
        except Exception as e:
            print(f"❌ ERREUR création objet ScrapingTask: {e}")
            if "invalid literal for int()" in str(e):
                print("🎯 ERREUR INT() TROUVÉE DANS LA CRÉATION D'OBJET!")
            traceback.print_exc()
            return
            
        print("\n🎯 SIMULATION RÉUSSIE - L'erreur ne vient PAS de la logique de création")
        
    except Exception as e:
        print(f"❌ Erreur test simulation: {e}")
        traceback.print_exc()

def test_edge_cases():
    """Teste les cas limites qui peuvent causer int('0/1')"""
    print("\n🧪 TEST CAS LIMITES INT('0/1')")
    print("=" * 50)
    
    # Test direct des conversions dangereuses
    dangerous_values = ["0/1", "3/5", "10/20", "abc/def", "0.5/1", ""]
    
    print("🔍 Test conversions directes (pour reproduire l'erreur):")
    for value in dangerous_values:
        try:
            result = int(value)
            print(f"   ⚠️  int('{value}') = {result} (inattendu!)")
        except ValueError as e:
            if "0/1" in value:
                print(f"   🎯 int('{value}') = ERREUR REPRODUITE: {e}")
            else:
                print(f"   ✅ int('{value}') = erreur attendue: {e}")
    
    # Test avec safe_parse_progress
    print("\n🔍 Test avec safe_parse_progress (devrait fonctionner):")
    try:
        from app.utils.helpers import safe_parse_progress
        for value in dangerous_values:
            try:
                result = safe_parse_progress(value)
                print(f"   ✅ safe_parse_progress('{value}') = {result}")
            except Exception as e:
                print(f"   ❌ safe_parse_progress('{value}') = ERREUR: {e}")
    except ImportError:
        print("   ❌ Impossible d'importer safe_parse_progress")

def test_reproduce_int_error():
    """Test spécifique pour reproduire et localiser l'erreur int('0/1')"""
    print("\n🧪 TEST REPRODUCTION ERREUR INT('0/1')")
    print("=" * 50)
    
    # Test direct de l'erreur
    try:
        result = int("0/1")
        print(f"⚠️  int('0/1') = {result} (ne devrait pas arriver!)")
    except ValueError as e:
        print(f"✅ int('0/1') reproduit l'erreur: {e}")
    
    # Test avec nos fonctions sécurisées
    try:
        from app.utils.helpers import safe_parse_progress, normalize_progress_string
        
        safe_result = safe_parse_progress("0/1", 0)
        normalized = normalize_progress_string("0/1")
        
        print(f"✅ safe_parse_progress('0/1') = {safe_result}")
        print(f"✅ normalize_progress_string('0/1') = '{normalized}'")
        
        print("\n💡 CONCLUSION:")
        print("   Si votre code utilise int('0/1') quelque part,")
        print("   remplacez par safe_parse_progress('0/1')")
        
    except ImportError as e:
        print(f"❌ Impossible d'importer helpers: {e}")

def test_manual_task_execution():
    """Teste l'exécution manuelle de la tâche avec la BONNE signature"""
    print("\n🧪 TEST EXÉCUTION MANUELLE CELERY")
    print("=" * 50)
    
    try:
        from app.tasks.scraping_tasks import enqueue_scraping_task
        from app.models.schemas import AnalysisType
        
        # Paramètres pour le test
        test_params = {
            'task_id': 'test-manual-123',
            'urls': ['https://www.ins.tn/statistiques'],
            'analysis_type': AnalysisType.STANDARD,
            'callback_url': None,
            'parameters': {},
            'priority': 1
        }
        
        print(f"🔍 Test avec paramètres: {test_params}")
        
        # ✅ MÉTHODE 1: Test avec .apply() (mode synchrone)
        print("\n🔍 Méthode 1: Celery .apply() synchrone")
        try:
            result = enqueue_scraping_task.apply(
                args=[
                    test_params['task_id'],       # task_id
                    test_params['urls'],          # urls
                    test_params['analysis_type'], # analysis_type
                    test_params['callback_url'],  # callback_url
                    test_params['parameters'],    # parameters
                    test_params['priority']       # priority
                ]
            )
            print(f"✅ .apply() réussi!")
            print(f"   État: {result.state}")
            print(f"   Résultat: {str(result.result)[:200]}...")
            
        except Exception as apply_error:
            print(f"❌ .apply() échoué: {apply_error}")
            
            # Détecter l'erreur int('0/1')
            error_str = str(apply_error)
            if "invalid literal for int()" in error_str:
                print("🚨 ERREUR INT() TROUVÉE AVEC .apply()!")
                if "0/1" in error_str:
                    print("🎯 BINGO! ERREUR INT('0/1') TROUVÉE!")
                    print("📍 Stack trace complète:")
                    traceback.print_exc()
                    return
                    
        # ✅ MÉTHODE 2: Test avec signature minimale si erreur de paramètres
        print("\n🔍 Méthode 2: Signature minimale (task_id, urls, analysis_type)")
        try:
            result = enqueue_scraping_task.apply(
                args=[
                    test_params['task_id'],
                    test_params['urls'],
                    test_params['analysis_type']
                ]
            )
            print(f"✅ Signature minimale réussie!")
            print(f"   État: {result.state}")
            
        except Exception as min_error:
            print(f"❌ Signature minimale échouée: {min_error}")
            
            # Détecter l'erreur int('0/1')
            error_str = str(min_error)
            if "invalid literal for int()" in error_str:
                print("🚨 ERREUR INT() TROUVÉE AVEC SIGNATURE MINIMALE!")
                if "0/1" in error_str:
                    print("🎯 BINGO! ERREUR INT('0/1') TROUVÉE!")
                    print("📍 Stack trace complète:")
                    traceback.print_exc()
                    return
        
        # ✅ MÉTHODE 3: Test avec appel direct (bypass Celery)
        print("\n🔍 Méthode 3: Appel direct de fonction (bypass Celery)")
        try:
            # Créer un mock self simple
            class MockCeleryTask:
                def __init__(self):
                    self.request = type('MockRequest', (), {
                        'id': 'test-request-id', 
                        'retries': 0
                    })()
                    self.max_retries = 3
                    
                def update_state(self, state, meta=None):
                    print(f"   📊 Mock Celery state: {state}")
                    
                def retry(self, exc=None, countdown=None):
                    print(f"   🔄 Mock retry: countdown={countdown}")
                    raise exc
            
            mock_self = MockCeleryTask()
            
            # Appel direct avec mock self
            result = enqueue_scraping_task(
                mock_self,
                test_params['task_id'],
                test_params['urls'],
                test_params['analysis_type'],
                test_params['callback_url'],
                test_params['parameters'],
                test_params['priority']
            )
            
            print(f"✅ Appel direct réussi!")
            print(f"   Type résultat: {type(result)}")
            print(f"   Contenu: {str(result)[:200]}...")
            
        except Exception as direct_error:
            print(f"❌ Appel direct échoué: {direct_error}")
            print(f"   Type d'erreur: {type(direct_error).__name__}")
            
            # Détecter l'erreur int('0/1')
            error_str = str(direct_error)
            if "invalid literal for int()" in error_str:
                print("🚨 ERREUR INT() TROUVÉE AVEC APPEL DIRECT!")
                
                if "0/1" in error_str:
                    print("🎯 BINGO! ERREUR INT('0/1') TROUVÉE DANS LA FONCTION!")
                elif "/" in error_str:
                    print(f"🎯 ERREUR INT() avec slash: {error_str}")
                
                print("📍 Stack trace complète:")
                traceback.print_exc()
                
                # Analyser la stack trace pour localiser l'erreur
                print("\n🔍 ANALYSE DE LA STACK TRACE:")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_traceback:
                    for frame_info in traceback.extract_tb(exc_traceback):
                        if "int(" in frame_info.line or "0/1" in frame_info.line:
                            print(f"🎯 LIGNE PROBLÉMATIQUE TROUVÉE:")
                            print(f"   Fichier: {frame_info.filename}")
                            print(f"   Ligne {frame_info.lineno}: {frame_info.line}")
                            
            elif "getaddrinfo failed" in error_str:
                print("ℹ️  Erreur de connexion Redis (normal)")
                print("💡 Configurez CELERY_ALWAYS_EAGER=True dans .env")
            elif "database" in error_str.lower() or "connection" in error_str.lower():
                print("ℹ️  Erreur de base de données (normal sans DB)")
            else:
                print(f"ℹ️  Autre erreur: {error_str[:300]}...")
                
    except ImportError as import_error:
        print(f"❌ Erreur import: {import_error}")
    except Exception as e:
        print(f"❌ Erreur générale test manuel: {e}")
        traceback.print_exc()

def test_check_helpers_usage():
    """Vérifie que les helpers sont bien utilisés partout"""
    print("\n🧪 TEST VÉRIFICATION USAGE HELPERS")
    print("=" * 50)
    
    try:
        import inspect
        from app.tasks import scraping_tasks
        
        # Récupérer le code source du module
        source_code = inspect.getsource(scraping_tasks)
        
        # Chercher les usages dangereux de int()
        lines = source_code.split('\n')
        dangerous_patterns = ['int(', 'int (']
        
        print("🔍 Recherche d'usages dangereux de int():")
        found_dangerous = False
        
        for i, line in enumerate(lines, 1):
            for pattern in dangerous_patterns:
                if pattern in line and 'safe_parse_progress' not in line:
                    print(f"⚠️  Ligne {i}: {line.strip()}")
                    found_dangerous = True
        
        if not found_dangerous:
            print("✅ Aucun usage dangereux de int() détecté")
        else:
            print("❌ Usages dangereux de int() trouvés - remplacez par safe_parse_progress()")
            
        # Vérifier les usages de safe_parse_progress
        safe_usage_count = source_code.count('safe_parse_progress')
        print(f"✅ Usages de safe_parse_progress: {safe_usage_count}")
        
    except Exception as e:
        print(f"❌ Erreur vérification helpers: {e}")

def main():
    print("🚀 TEST COMPLET POUR IDENTIFIER L'ERREUR INT('0/1')")
    print("=" * 80)
    print("Ce test va identifier précisément où l'erreur se produit")
    print("=" * 80)
    
    # Tests en séquence logique
    test_imports()
    test_helper_functions()
    test_database_models()
    test_schemas()
    test_celery_import()
    test_worker_connection()
    test_celery_task_creation()
    test_edge_cases()
    test_reproduce_int_error()
    test_check_helpers_usage()  # ✅ NOUVEAU: Vérifier l'usage des helpers
    test_manual_task_execution() # Test final avec toutes les méthodes
    
    print("\n🎯 ANALYSE TERMINÉE")
    print("=" * 80)
    print("Regardez les résultats ci-dessus pour identifier où l'erreur se produit.")
    print("Si 'BINGO! ERREUR INT('0/1') TROUVÉE!' apparaît, nous avons trouvé la source!")
    
    print("\n💡 INSTRUCTIONS DE RÉSOLUTION:")
    print("1. Si erreur Redis: Ajoutez CELERY_ALWAYS_EAGER=True dans .env")
    print("2. Si erreur int('0/1'): Remplacez int() par safe_parse_progress()")
    print("3. Si erreur signature: Utilisez .apply() avec 6 arguments")
    print("4. Si erreur DB: Normal sans base de données connectée")

if __name__ == "__main__":
    main()