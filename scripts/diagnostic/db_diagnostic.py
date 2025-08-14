#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les problèmes de connexion à la base de données.
À exécuter avant la migration pour vérifier la configuration.
"""

import os
import sys
from urllib.parse import quote_plus

def test_environment_variables():
    """Tester les variables d'environnement"""
    print("🔍 DIAGNOSTIC DES VARIABLES D'ENVIRONNEMENT")
    print("=" * 50)
    
    vars_to_check = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD", 
        "POSTGRES_DB",
        "DB_HOST"
    ]
    
    for var in vars_to_check:
        value = os.getenv(var)
        if var == "POSTGRES_PASSWORD":
            display_value = "***" if value else "NON_DÉFINI"
        else:
            display_value = value or "NON_DÉFINI"
        
        status = "✅" if value else "❌"
        print(f"{status} {var}: {display_value}")
    
    return all(os.getenv(var) for var in vars_to_check)

def test_connection_urls():
    """Tester différentes URLs de connexion"""
    print("\n🔗 TEST DES URLs DE CONNEXION")
    print("=" * 50)
    
    # Configuration par défaut
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_pass = os.getenv("POSTGRES_PASSWORD", "dorra123")
    db_name = os.getenv("POSTGRES_DB", "scraper_db")
    
    # Différentes configurations à tester
    hosts_to_test = [
        ("Docker (db)", "db"),
        ("Local (localhost)", "localhost"),
        ("Local (127.0.0.1)", "127.0.0.1")
    ]
    
    urls = []
    for desc, host in hosts_to_test:
        try:
            # Encodage sûr du mot de passe
            db_pass_encoded = quote_plus(db_pass)
            url = f"postgresql://{db_user}:{db_pass_encoded}@{host}:5432/{db_name}"
            urls.append((desc, url, host))
            print(f"📝 {desc}: postgresql://{db_user}:***@{host}:5432/{db_name}")
        except Exception as e:
            print(f"❌ Erreur création URL {desc}: {e}")
    
    return urls

def test_sqlalchemy_connection(url_info):
    """Tester une connexion SQLAlchemy spécifique"""
    desc, url, host = url_info
    
    try:
        from sqlalchemy import create_engine, text
        
        # Engine avec options d'encodage robustes
        engine = create_engine(
            url,
            echo=False,
            connect_args={
                "client_encoding": "utf8",
                "connect_timeout": 5,
                "options": "-c client_encoding=utf8"
            },
            pool_pre_ping=True
        )
        
        # Test de connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ {desc}: Connexion OK")
            print(f"   Version PostgreSQL: {version[:50]}...")
            return True
            
    except UnicodeDecodeError as e:
        print(f"❌ {desc}: Erreur encodage - {e}")
        return False
    except Exception as e:
        print(f"❌ {desc}: Erreur connexion - {e}")
        return False

def test_direct_import():
    """Tester l'import direct des modules app"""
    print("\n📦 TEST DES IMPORTS")
    print("=" * 50)
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Test imports un par un
        imports_to_test = [
            ("app.models.database", "ScrapingTask, SessionLocal"),
            ("app.utils.helpers", "safe_parse_progress"),
            ("sqlalchemy", "text, inspect")
        ]
        
        for module_name, items in imports_to_test:
            try:
                __import__(module_name)
                print(f"✅ Import {module_name}: OK")
            except Exception as e:
                print(f"❌ Import {module_name}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur imports généraux: {e}")
        return False

def suggest_fixes():
    """Suggérer des solutions basées sur les tests"""
    print("\n🛠️ SOLUTIONS SUGGÉRÉES")
    print("=" * 50)
    
    print("1. 🐳 Si vous utilisez Docker:")
    print("   docker-compose up -d db")
    print("   docker exec -it votre-conteneur python migration_cleanup.py --dry-run")
    
    print("\n2. 🖥️ Si vous exécutez localement:")
    print("   export DB_HOST=localhost")
    print("   # ou modifiez dans .env: DB_HOST=localhost")
    
    print("\n3. 🔑 Si problème de mot de passe:")
    print("   # Vérifiez les caractères spéciaux dans POSTGRES_PASSWORD")
    print("   # Essayez de simplifier temporairement le mot de passe")
    
    print("\n4. 🔧 Test direct PostgreSQL:")
    print("   psql -h localhost -U postgres -d scraper_db")
    
    print("\n5. 📁 Vérification de structure:")
    print("   ls -la app/models/")
    print("   ls -la app/utils/")

def main():
    print("🚀 DIAGNOSTIC DE CONNEXION BASE DE DONNÉES")
    print("=" * 60)
    
    # Test 1: Variables d'environnement
    env_ok = test_environment_variables()
    
    # Test 2: Imports Python
    imports_ok = test_direct_import()
    
    if not imports_ok:
        print("\n❌ Problème d'imports - Vérifiez la structure du projet")
        suggest_fixes()
        return False
    
    # Test 3: URLs de connexion
    urls = test_connection_urls()
    
    # Test 4: Connexions effectives
    print("\n🔌 TEST DES CONNEXIONS")
    print("=" * 50)
    
    connection_success = False
    for url_info in urls:
        if test_sqlalchemy_connection(url_info):
            connection_success = True
            break
    
    # Résumé et recommandations
    print("\n📊 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 50)
    print(f"Variables d'env: {'✅ OK' if env_ok else '❌ Manquantes'}")
    print(f"Imports Python:  {'✅ OK' if imports_ok else '❌ Échec'}")
    print(f"Connexion DB:    {'✅ OK' if connection_success else '❌ Échec'}")
    
    if connection_success:
        print("\n🎉 Diagnostic réussi ! Vous pouvez exécuter la migration.")
        print("   Commande: python migration_cleanup.py --dry-run --verbose")
    else:
        print("\n⚠️ Problèmes détectés. Suivez les suggestions ci-dessous:")
        suggest_fixes()
    
    return connection_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur fatale du diagnostic: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)