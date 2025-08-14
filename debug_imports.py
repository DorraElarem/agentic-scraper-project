#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les problèmes d'imports dans le projet
"""
import sys
import traceback
from pathlib import Path

def test_import(module_name, item_name=None):
    """Teste l'import d'un module ou d'un item spécifique"""
    try:
        if item_name:
            exec(f"from {module_name} import {item_name}")
            print(f"✅ {module_name}.{item_name} - OK")
            return True
        else:
            exec(f"import {module_name}")
            print(f"✅ {module_name} - OK")
            return True
    except Exception as e:
        print(f"❌ {module_name}{f'.{item_name}' if item_name else ''} - ERROR: {e}")
        return False

def test_settings_module():
    """Test spécifique du module settings"""
    print("\n🔍 DIAGNOSTIC DU MODULE SETTINGS:")
    
    try:
        # Test 1: Import du module
        print("1. Test import du module...")
        import app.config.settings as settings_module
        print("✅ Module importé avec succès")
        
        # Test 2: Vérifier les attributs disponibles
        print("2. Attributs disponibles dans le module:")
        attrs = [attr for attr in dir(settings_module) if not attr.startswith('_')]
        for attr in attrs[:10]:  # Premiers 10 attributs
            print(f"   - {attr}")
        
        # Test 3: Vérifier la classe Settings
        if hasattr(settings_module, 'Settings'):
            print("✅ Classe Settings trouvée")
        else:
            print("❌ Classe Settings manquante")
        
        # Test 4: Vérifier l'instance settings
        if hasattr(settings_module, 'settings'):
            print("✅ Instance settings trouvée")
            settings_instance = settings_module.settings
            print(f"   Type: {type(settings_instance)}")
        else:
            print("❌ Instance settings manquante")
            print("💡 Il faut créer l'instance à la fin du fichier settings.py")
        
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {e}")
        traceback.print_exc()

def test_all_imports():
    """Teste tous les imports critiques"""
    print("🔍 TEST DE TOUS LES IMPORTS CRITIQUES\n")
    
    imports_to_test = [
        # Modules de base
        ("app.config.settings", None),
        ("app.config.settings", "settings"),
        ("app.config.settings", "Settings"),
        
        # Modèles
        ("app.models.schemas", None),
        ("app.models.schemas", "TaskResponse"),
        ("app.models.schemas", "ProgressInfo"),
        ("app.models.schemas", "AnalysisType"),
        
        # Base de données
        ("app.models.database", None),
        ("app.models.database", "ScrapingTask"),
        ("app.models.database", "init_db"),
        
        # Scrapers
        ("app.scrapers.traditional", None),
        ("app.scrapers.traditional", "TunisianWebScraper"),
        ("app.scrapers.intelligent", None),
        ("app.scrapers.intelligent", "IntelligentScraper"),
        
        # Agents
        ("app.agents.scraper_agent", None),
        ("app.agents.scraper_agent", "ScraperAgent"),
        
        # Celery
        ("app.celery_app", None),
        ("app.celery_app", "celery_app"),
        
        # LLM Config
        ("app.config.llm_config", None),
        ("app.config.llm_config", "LLMConfig"),
    ]
    
    success_count = 0
    total_count = len(imports_to_test)
    
    for module_name, item_name in imports_to_test:
        if test_import(module_name, item_name):
            success_count += 1
    
    print(f"\n📊 RÉSULTATS: {success_count}/{total_count} imports réussis")
    
    if success_count < total_count:
        print("\n🔧 ACTIONS RECOMMANDÉES:")
        print("1. Vérifier que tous les fichiers __init__.py existent")
        print("2. Vérifier la syntaxe de chaque module")
        print("3. Corriger les imports circulaires")
        print("4. S'assurer que settings.py exporte bien l'instance 'settings'")

def check_file_structure():
    """Vérifie la structure des fichiers"""
    print("\n📁 VÉRIFICATION DE LA STRUCTURE DES FICHIERS:")
    
    required_files = [
        "app/__init__.py",
        "app/config/__init__.py", 
        "app/config/settings.py",
        "app/models/__init__.py",
        "app/models/schemas.py",
        "app/models/database.py",
        "app/scrapers/__init__.py",
        "app/scrapers/traditional.py", 
        "app/scrapers/intelligent.py",
        "app/agents/__init__.py",
        "app/agents/scraper_agent.py",
        "app/celery_app.py",
        "app/main.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MANQUANT")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ {len(missing_files)} fichiers manquants détectés")
        return False
    else:
        print("\n✅ Tous les fichiers requis sont présents")
        return True

def create_missing_init_files():
    """Crée les fichiers __init__.py manquants"""
    print("\n🔧 CRÉATION DES FICHIERS __init__.py MANQUANTS:")
    
    init_files = [
        ("app/__init__.py", ""),
        ("app/config/__init__.py", ""),
        ("app/models/__init__.py", ""),
        ("app/scrapers/__init__.py", ""),
        ("app/agents/__init__.py", ""),
        ("app/tasks/__init__.py", ""),
        ("app/utils/__init__.py", "")
    ]
    
    for file_path, content in init_files:
        path = Path(file_path)
        if not path.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding='utf-8')
                print(f"✅ Créé: {file_path}")
            except Exception as e:
                print(f"❌ Erreur création {file_path}: {e}")
        else:
            print(f"✓ Existe déjà: {file_path}")

def fix_settings_export():
    """Propose une correction pour le fichier settings.py"""
    print("\n🔧 CORRECTION SUGGÉRÉE POUR SETTINGS.PY:")
    
    settings_fix = '''
# À la fin du fichier app/config/settings.py, ajouter :

# Instance singleton des paramètres
settings = Settings()

# Export explicite pour éviter les erreurs d'import
__all__ = ['Settings', 'settings', 'AnalysisCategory']
'''
    
    print(settings_fix)
    
    # Vérifier si le fichier settings.py existe et contient l'instance
    settings_path = Path("app/config/settings.py")
    if settings_path.exists():
        content = settings_path.read_text(encoding='utf-8')
        if "settings = Settings()" in content:
            print("✅ L'instance settings est déjà définie")
        else:
            print("❌ L'instance settings n'est pas définie dans le fichier")
            print("💡 Ajoutez 'settings = Settings()' à la fin du fichier")
    else:
        print("❌ Le fichier settings.py n'existe pas")

def main():
    """Fonction principale de diagnostic"""
    print("🔍 DIAGNOSTIC COMPLET DES IMPORTS\n")
    print("=" * 60)
    
    # Étape 1: Vérifier la structure des fichiers
    structure_ok = check_file_structure()
    
    # Étape 2: Créer les fichiers __init__.py manquants
    create_missing_init_files()
    
    # Étape 3: Diagnostic spécifique du module settings
    test_settings_module()
    
    # Étape 4: Suggestion de correction
    fix_settings_export()
    
    # Étape 5: Test de tous les imports
    test_all_imports()
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC TERMINÉ")
    
    if not structure_ok:
        print("\n⚠️ Corrigez d'abord la structure des fichiers avant de continuer")
    else:
        print("\n✅ Vous pouvez maintenant tester vos imports")

if __name__ == "__main__":
    main()