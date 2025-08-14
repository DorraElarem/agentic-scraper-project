#!/usr/bin/env python3
"""
Script de réparation rapide pour l'erreur 'max_content_length' is not defined
"""

import os
import sys
import shutil
from pathlib import Path

def fix_traditional_scraper():
    """Corrige le fichier traditional.py"""
    print("🔧 Correction du fichier traditional.py...")
    
    file_path = Path("app/scrapers/traditional.py")
    
    if not file_path.exists():
        print(f"❌ Fichier {file_path} introuvable")
        return False
    
    # Lire le contenu actuel
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrections nécessaires
    fixes = [
        # 1. Corriger l'import de settings
        ("from app.config.settings import settings", None),
        
        # 2. Corriger l'initialisation de max_content_length
        ("self.max_content_length = max_content_length if max_content_length is not None else float('inf')",
         "self.max_content_length = max_content_length or (getattr(settings, 'MIN_CONTENT_LENGTH', 5000) * 1000)"),
        
        # 3. Corriger l'import de settings s'il n'est pas présent
        ("import re\nfrom typing import Optional, Dict, Any\nimport requests",
         "import re\nfrom typing import Optional, Dict, Any\nimport requests\nfrom app.config.settings import settings"),
    ]
    
    # Vérifier si settings est importé
    if "from app.config.settings import settings" not in content:
        # Ajouter l'import après les autres imports
        content = content.replace(
            "from app.models.schemas import ScrapedContent",
            "from app.models.schemas import ScrapedContent\nfrom app.config.settings import settings"
        )
    
    # Corriger l'initialisation du constructeur
    old_init = '''def __init__(self, delay: float = 2.0, max_content_length: int = None):
        self.delay = delay
        self.max_content_length = max_content_length if max_content_length is not None else float('inf')'''
    
    new_init = '''def __init__(self, delay: float = None, max_content_length: int = None):
        self.delay = delay or getattr(settings, 'DEFAULT_DELAY', 2.0)
        self.max_content_length = max_content_length or (getattr(settings, 'MIN_CONTENT_LENGTH', 5000) * 1000)'''
    
    content = content.replace(old_init, new_init)
    
    # Corriger l'User-Agent
    old_headers = """self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'fr-FR,fr;q=0.9'
        })"""
    
    new_headers = """self.session.headers.update({
            'User-Agent': getattr(settings, 'SCRAPE_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
            'Accept-Language': 'fr-FR,fr;q=0.9'
        })"""
    
    content = content.replace(old_headers, new_headers)
    
    # Sauvegarder le fichier corrigé
    backup_path = file_path.with_suffix('.py.backup')
    shutil.copy2(file_path, backup_path)
    print(f"💾 Sauvegarde créée: {backup_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fichier traditional.py corrigé")
    return True

def fix_settings_file():
    """Corrige le fichier settings.py pour avoir les bonnes variables"""
    print("🔧 Vérification du fichier settings.py...")
    
    file_path = Path("app/config/settings.py")
    
    if not file_path.exists():
        print(f"❌ Fichier {file_path} introuvable")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier que les variables nécessaires sont présentes
    required_vars = [
        'DEFAULT_DELAY',
        'REQUEST_TIMEOUT', 
        'MIN_CONTENT_LENGTH',
        'SCRAPE_USER_AGENT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if f"{var}:" not in content and f"{var} =" not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Variables manquantes dans settings.py: {missing_vars}")
        
        # Ajouter les variables manquantes
        additions = []
        
        if 'DEFAULT_DELAY' in missing_vars:
            additions.append('    DEFAULT_DELAY: float = Field(2.5, env="SCRAPE_DELAY_SEC")')
        
        if 'REQUEST_TIMEOUT' in missing_vars:
            additions.append('    REQUEST_TIMEOUT: int = Field(30, env="SCRAPE_TIMEOUT_SEC")')
        
        if 'MIN_CONTENT_LENGTH' in missing_vars:
            additions.append('    MIN_CONTENT_LENGTH: int = Field(5000, env="MAX_CONTENT_LENGTH_KB")')
        
        if 'SCRAPE_USER_AGENT' in missing_vars:
            additions.append('    SCRAPE_USER_AGENT: str = Field("Mozilla/5.0 (compatible; AgenticScraper/1.0)", env="SCRAPE_USER_AGENT")')
        
        # Insérer les additions après la ligne "# Configuration du scraping"
        insert_point = content.find("# Configuration du scraping")
        if insert_point != -1:
            # Trouver la fin de la section
            next_section = content.find("\n    # Configuration", insert_point + 1)
            if next_section == -1:
                next_section = content.find("\n    class Config:", insert_point + 1)
            
            if next_section != -1:
                # Insérer avant la prochaine section
                new_content = (content[:next_section] + 
                             "\n    " + "\n    ".join(additions) + 
                             content[next_section:])
                
                # Sauvegarder
                backup_path = file_path.with_suffix('.py.backup')
                shutil.copy2(file_path, backup_path)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ Variables ajoutées à settings.py")
    else:
        print("✅ Toutes les variables nécessaires sont présentes")
    
    return True

def fix_intelligent_scraper():
    """Corrige le fichier intelligent.py"""
    print("🔧 Correction du fichier intelligent.py...")
    
    file_path = Path("app/scrapers/intelligent.py")
    
    if not file_path.exists():
        print(f"❌ Fichier {file_path} introuvable")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corriger l'initialisation
    old_init = "def __init__(self, delay: float = settings.DEFAULT_DELAY):"
    new_init = "def __init__(self, delay: float = None):"
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        content = content.replace(
            "super().__init__(delay)",
            "super().__init__(delay or settings.DEFAULT_DELAY)"
        )
        
        # Sauvegarder
        backup_path = file_path.with_suffix('.py.backup')
        shutil.copy2(file_path, backup_path)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fichier intelligent.py corrigé")
    else:
        print("✅ Fichier intelligent.py déjà correct")
    
    return True

def test_import():
    """Test l'import des modules corrigés"""
    print("🧪 Test des imports...")
    
    try:
        sys.path.insert(0, str(Path.cwd()))
        
        # Test import settings
        from app.config.settings import settings
        print("✅ Import settings réussi")
        
        # Test des variables
        vars_to_check = ['DEFAULT_DELAY', 'REQUEST_TIMEOUT', 'MIN_CONTENT_LENGTH', 'SCRAPE_USER_AGENT']
        for var in vars_to_check:
            if hasattr(settings, var):
                value = getattr(settings, var)
                print(f"  ✅ {var} = {value}")
            else:
                print(f"  ❌ {var} manquant")
        
        # Test import scrapers
        from app.scrapers.traditional import TunisianWebScraper
        print("✅ Import TunisianWebScraper réussi")
        
        from app.scrapers.intelligent import IntelligentScraper
        print("✅ Import IntelligentScraper réussi")
        
        # Test création d'instances
        traditional_scraper = TunisianWebScraper()
        print(f"✅ TunisianWebScraper créé (delay={traditional_scraper.delay}, max_length={traditional_scraper.max_content_length})")
        
        intelligent_scraper = IntelligentScraper()
        print(f"✅ IntelligentScraper créé (delay={intelligent_scraper.delay})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_test_script():
    """Crée un script de test simple"""
    print("📝 Création d'un script de test...")
    
    test_script_content = '''#!/usr/bin/env python3
"""
Script de test simple pour vérifier le scraping
"""

import requests
import json
import time

def test_scraping_api():
    """Test l'API de scraping"""
    base_url = "http://localhost:8000"
    
    print("🧪 Test de l'API de scraping...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API accessible")
        else:
            print(f"❌ API inaccessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion API: {e}")
        return False
    
    # Test 2: Scraping simple
    try:
        payload = {
            "urls": ["https://httpbin.org/html"],
            "analysis_type": "standard"
        }
        
        response = requests.post(f"{base_url}/scrape", json=payload, timeout=15)
        
        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get("task_id")
            print(f"✅ Tâche créée: {task_id}")
            
            # Attendre la completion
            for i in range(10):
                time.sleep(3)
                status_response = requests.get(f"{base_url}/tasks/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")
                    print(f"📊 Status: {status}")
                    
                    if status == "completed":
                        print("✅ Scraping réussi!")
                        print(f"📋 Résultats: {len(status_data.get('results', []))} éléments")
                        return True
                    elif status == "failed":
                        print(f"❌ Scraping échoué: {status_data.get('error')}")
                        return False
            
            print("⏰ Timeout - tâche non terminée")
            return False
            
        else:
            print(f"❌ Erreur création tâche: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 Détails: {error_data}")
            except:
                print(f"📋 Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test scraping: {e}")
        return False

if __name__ == "__main__":
    test_scraping_api()
'''
    
    with open("test_scraping_simple.py", "w", encoding="utf-8") as f:
        f.write(test_script_content)
    
    print("✅ Script de test créé: test_scraping_simple.py")

def main():
    """Fonction principale"""
    print("🚀 RÉPARATION RAPIDE - Erreur 'max_content_length' not defined")
    print("=" * 60)
    
    success = True
    
    # Étape 1: Corriger settings.py
    if not fix_settings_file():
        success = False
    
    # Étape 2: Corriger traditional.py
    if not fix_traditional_scraper():
        success = False
    
    # Étape 3: Corriger intelligent.py
    if not fix_intelligent_scraper():
        success = False
    
    # Étape 4: Tester les imports
    if not test_import():
        success = False
    
    # Étape 5: Créer un script de test
    create_test_script()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ RÉPARATION TERMINÉE AVEC SUCCÈS!")
        print("\n📋 Prochaines étapes:")
        print("1. Redémarrez votre application: docker-compose restart")
        print("2. Testez avec: python test_scraping_simple.py")
        print("3. Ou utilisez l'API directement: POST /scrape")
        print("\n💡 Les fichiers originaux ont été sauvegardés avec l'extension .backup")
    else:
        print("❌ RÉPARATION INCOMPLÈTE - Vérifiez les erreurs ci-dessus")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())