#!/usr/bin/env python3
"""
Script de test pour vérifier les corrections apportées
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"  # Ajustez selon votre configuration
TEST_URLS = [
    "https://httpbin.org/json",
    "https://httpbin.org/html", 
    "https://httpbin.org/xml"
]

def test_system_status():
    """Test du statut système"""
    print("\n=== Test du statut système ===")
    try:
        response = requests.get(f"{API_BASE_URL}/system/status")
        if response.status_code == 200:
            print("✅ Statut système : OK")
            data = response.json()
            print(f"   Version: {data.get('version')}")
            print(f"   Statut: {data.get('status')}")
        else:
            print(f"❌ Erreur statut système: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")

def test_task_creation():
    """Test de création de tâche"""
    print("\n=== Test de création de tâche ===")
    try:
        payload = {
            "urls": TEST_URLS,
            "analysis_type": "standard"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tasks",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            task_data = response.json()
            task_id = task_data.get('task_id')
            print(f"✅ Tâche créée avec succès: {task_id}")
            print(f"   Status: {task_data.get('status')}")
            print(f"   Progress: {task_data.get('progress')}")
            print(f"   Type d'analyse: {task_data.get('analysis_type')}")
            return task_id
        else:
            print(f"❌ Erreur création tâche: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur création tâche: {e}")
        return None

def test_task_monitoring(task_id, max_wait=60):
    """Test de monitoring de tâche"""
    if not task_id:
        print("❌ Pas de task_id pour le monitoring")
        return
        
    print(f"\n=== Monitoring de la tâche {task_id} ===")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', {})
                
                current = progress.get('current', 0)
                total = progress.get('total', 1)
                percentage = progress.get('percentage', 0)
                
                print(f"📊 Status: {status} | Progress: {current}/{total} ({percentage}%)")
                
                if status in ['completed', 'failed']:
                    print(f"🏁 Tâche terminée avec le statut: {status}")
                    
                    if status == 'completed':
                        result = data.get('result', {})
                        if result:
                            print("✅ Résultats disponibles:")
                            summary = result.get('summary', {})
                            if summary:
                                print(f"   Total URLs: {summary.get('total_urls', 0)}")
                                print(f"   Succès: {summary.get('successful', 0)}")
                                print(f"   Échecs: {summary.get('failed', 0)}")
                                print(f"   Taux de succès: {summary.get('success_rate', 0):.1%}")
                    
                    elif status == 'failed':
                        error = data.get('error')
                        if error:
                            print(f"❌ Erreur: {error}")
                    
                    break
                    
                time.sleep(2)  # Attendre 2 secondes avant le prochain check
                
            else:
                print(f"❌ Erreur récupération statut: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Erreur monitoring: {e}")
            break
    else:
        print(f"⏰ Timeout atteint ({max_wait}s)")

def test_edge_cases():
    """Test des cas limites"""
    print("\n=== Test des cas limites ===")
    
    # Test avec URL invalide
    print("🧪 Test URL invalide...")
    try:
        payload = {
            "urls": ["not-a-url", "https://httpbin.org/status/404"],
            "analysis_type": "standard"
        }
        
        response = requests.post(f"{API_BASE_URL}/tasks", json=payload)
        if response.status_code == 201:
            print("✅ Tâche créée malgré URL invalide (gestion d'erreur OK)")
        else:
            print(f"⚠️  Création refusée: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur test URL invalide: {e}")
    
    # Test avec task_id inexistant
    print("🧪 Test task_id inexistant...")
    try:
        fake_task_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{API_BASE_URL}/tasks/{fake_task_id}")
        if response.status_code == 404:
            print("✅ Erreur 404 correctement retournée")
        else:
            print(f"⚠️  Réponse inattendue: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur test task_id inexistant: {e}")

def test_progress_calculation():
    """Test spécifique du calcul de progression"""
    print("\n=== Test calcul de progression ===")
    
    # Test avec une seule URL pour vérifier la progression
    payload = {
        "urls": ["https://httpbin.org/delay/1"],  # URL avec délai
        "analysis_type": "standard"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/tasks", json=payload)
        if response.status_code == 201:
            task_id = response.json().get('task_id')
            print(f"✅ Tâche de test progression créée: {task_id}")
            
            # Vérifier plusieurs fois pour voir l'évolution
            for i in range(5):
                time.sleep(1)
                status_response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
                if status_response.status_code == 200:
                    data = status_response.json()
                    progress = data.get('progress', {})
                    print(f"   Check {i+1}: {progress.get('current', 0)}/{progress.get('total', 1)} ({progress.get('percentage', 0)}%)")
                    
                    if data.get('status') in ['completed', 'failed']:
                        break
        else:
            print(f"❌ Erreur création tâche test: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur test progression: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 Début des tests de l'API Agentic Scraper")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL de base: {API_BASE_URL}")
    
    # Tests séquentiels
    test_system_status()
    task_id = test_task_creation()
    test_task_monitoring(task_id)
    test_edge_cases()
    test_progress_calculation()
    
    print("\n✨ Tests terminés")

if __name__ == "__main__":
    main()