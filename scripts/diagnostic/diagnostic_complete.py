#!/usr/bin/env python3
"""
Script de diagnostic complet pour l'agentic scraper
Identifie et résout les problèmes courants
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any, List

class AgenticScraperDiagnostic:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.issues_found = []
        self.fixes_applied = []

    def run_complete_diagnostic(self) -> Dict[str, Any]:
        """Lance un diagnostic complet du système"""
        print("🔍 DIAGNOSTIC COMPLET DU SYSTÈME AGENTIC SCRAPER")
        print("=" * 60)
        
        results = {
            "api_health": self.check_api_health(),
            "celery_status": self.check_celery_status(),
            "redis_connectivity": self.check_redis_connectivity(),
            "database_status": self.check_database_status(),
            "ollama_status": self.check_ollama_status(),
            "scraping_functionality": self.test_scraping_modes(),
            "performance_metrics": self.measure_performance(),
            "recommendations": self.generate_recommendations()
        }
        
        self.print_summary(results)
        return results

    def check_api_health(self) -> Dict[str, Any]:
        """Vérifie la santé de l'API FastAPI"""
        print("\n🏥 Vérification de la santé de l'API...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ API FastAPI opérationnelle")
                return {"status": "healthy", "data": data}
            else:
                print(f"❌ API répond avec le code {response.status_code}")
                self.issues_found.append("API health check failed")
                return {"status": "unhealthy", "status_code": response.status_code}
                
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de se connecter à l'API")
            self.issues_found.append("API connection failed")
            return {"status": "unreachable", "error": "Connection failed"}
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {str(e)}")
            self.issues_found.append(f"API health error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def check_celery_status(self) -> Dict[str, Any]:
        """Vérifie le statut de Celery"""
        print("\n🔄 Vérification de Celery...")
        
        try:
            response = self.session.get(f"{self.base_url}/debug/celery", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Vérifications spécifiques
                if data.get("scraping_task_available"):
                    print("✅ Tâche de scraping disponible dans Celery")
                else:
                    print("❌ Tâche de scraping non disponible")
                    self.issues_found.append("Scraping task not registered in Celery")
                
                if data.get("redis_status") == "connected":
                    print("✅ Redis connecté à Celery")
                else:
                    print(f"❌ Problème Redis: {data.get('redis_status')}")
                    self.issues_found.append("Redis connection issue")
                
                print(f"📋 Tâches enregistrées: {len(data.get('registered_tasks', []))}")
                
                return {"status": "operational", "data": data}
            else:
                print(f"❌ Erreur debug Celery: {response.status_code}")
                self.issues_found.append("Celery debug endpoint failed")
                return {"status": "error", "status_code": response.status_code}
                
        except Exception as e:
            print(f"❌ Erreur Celery: {str(e)}")
            self.issues_found.append(f"Celery check error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def check_redis_connectivity(self) -> Dict[str, Any]:
        """Teste la connectivité Redis directement"""
        print("\n📡 Test de connectivité Redis...")
        
        try:
            # Test via l'endpoint de test Celery
            response = self.session.post(f"{self.base_url}/debug/test-celery", timeout=15)
            if response.status_code == 200:
                data = response.json()
                print("✅ Communication Celery-Redis fonctionnelle")
                return {"status": "connected", "test_data": data}
            else:
                print(f"❌ Test Celery échoué: {response.status_code}")
                self.issues_found.append("Celery-Redis communication failed")
                return {"status": "failed", "status_code": response.status_code}
                
        except Exception as e:
            print(f"❌ Erreur test Redis: {str(e)}")
            self.issues_found.append(f"Redis test error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def check_database_status(self) -> Dict[str, Any]:
        """Vérifie l'état de la base de données"""
        print("\n💾 Vérification de la base de données...")
        
        try:
            # Test en listant les tâches
            response = self.session.get(f"{self.base_url}/tasks?limit=1", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ Base de données accessible")
                print(f"📊 Nombre de tâches: {data.get('total', 0)}")
                return {"status": "connected", "task_count": data.get('total', 0)}
            else:
                print(f"❌ Erreur base de données: {response.status_code}")
                self.issues_found.append("Database connection failed")
                return {"status": "error", "status_code": response.status_code}
                
        except Exception as e:
            print(f"❌ Erreur DB: {str(e)}")
            self.issues_found.append(f"Database error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def check_ollama_status(self) -> Dict[str, Any]:
        """Vérifie le statut d'Ollama"""
        print("\n🤖 Vérification d'Ollama...")
        
        try:
            # Test direct sur Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                print(f"✅ Ollama opérationnel avec {len(models)} modèles")
                
                # Vérifier si le modèle requis est présent
                mistral_present = any("mistral" in model.get("name", "") for model in models)
                if mistral_present:
                    print("✅ Modèle Mistral disponible")
                else:
                    print("⚠️ Modèle Mistral non trouvé")
                    self.issues_found.append("Mistral model not found")
                
                return {
                    "status": "operational", 
                    "models": models,
                    "mistral_available": mistral_present
                }
            else:
                print(f"❌ Ollama non accessible: {response.status_code}")
                self.issues_found.append("Ollama not accessible")
                return {"status": "unreachable", "status_code": response.status_code}
                
        except requests.exceptions.ConnectionError:
            print("❌ Ollama non démarré")
            self.issues_found.append("Ollama not running")
            return {"status": "not_running"}
        except Exception as e:
            print(f"❌ Erreur Ollama: {str(e)}")
            self.issues_found.append(f"Ollama error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def test_scraping_modes(self) -> Dict[str, Any]:
        """Teste les différents modes de scraping"""
        print("\n🕷️ Test des modes de scraping...")
        
        test_url = "https://httpbin.org/html"
        modes = ["standard", "advanced", "custom"]
        results = {}
        
        for mode in modes:
            print(f"\n  🧪 Test mode {mode.upper()}...")
            
            try:
                # Créer une tâche de scraping
                payload = {
                    "urls": [test_url],
                    "analysis_type": mode,
                    "parameters": {"test_mode": True} if mode == "custom" else {}
                }
                
                response = self.session.post(f"{self.base_url}/scrape", json=payload, timeout=15)
                
                if response.status_code == 200:
                    task_data = response.json()
                    task_id = task_data.get("task_id")
                    print(f"    ✅ Tâche créée: {task_id}")
                    
                    # Attendre l'exécution
                    result = self.wait_for_task_completion(task_id, timeout=30)
                    
                    if result["status"] == "completed":
                        print(f"    ✅ Scraping {mode} réussi")
                        results[mode] = {"status": "success", "task_id": task_id, "result": result}
                    else:
                        print(f"    ❌ Scraping {mode} échoué: {result.get('error', 'Unknown error')}")
                        results[mode] = {"status": "failed", "error": result.get('error')}
                        self.issues_found.append(f"{mode} scraping failed")
                else:
                    print(f"    ❌ Erreur création tâche {mode}: {response.status_code}")
                    results[mode] = {"status": "creation_failed", "status_code": response.status_code}
                    self.issues_found.append(f"{mode} task creation failed")
                    
            except Exception as e:
                print(f"    ❌ Erreur test {mode}: {str(e)}")
                results[mode] = {"status": "error", "error": str(e)}
                self.issues_found.append(f"{mode} test error: {str(e)}")
        
        return results

    def wait_for_task_completion(self, task_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Attend qu'une tâche soit terminée"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.base_url}/tasks/{task_id}", timeout=5)
                if response.status_code == 200:
                    task_data = response.json()
                    status = task_data.get("status")
                    
                    if status in ["completed", "failed", "cancelled"]:
                        return task_data
                    
                    print(f"    ⏳ Status: {status}, Progress: {task_data.get('progress', {}).get('display', 'N/A')}")
                    time.sleep(2)
                else:
                    return {"status": "error", "error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        return {"status": "timeout", "error": "Task did not complete within timeout"}

    def measure_performance(self) -> Dict[str, Any]:
        """Mesure les performances du système"""
        print("\n⚡ Mesure des performances...")
        
        metrics = {
            "api_response_time": self.measure_api_response_time(),
            "scraping_speed": self.measure_scraping_speed(),
            "memory_usage": self.estimate_memory_usage()
        }
        
        return metrics

    def measure_api_response_time(self) -> float:
        """Mesure le temps de réponse de l'API"""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000  # en ms
                print(f"  📊 Temps de réponse API: {response_time:.2f}ms")
                return response_time
            else:
                print("  ❌ Impossible de mesurer le temps de réponse")
                return -1
                
        except Exception as e:
            print(f"  ❌ Erreur mesure temps de réponse: {str(e)}")
            return -1

    def measure_scraping_speed(self) -> Dict[str, Any]:
        """Mesure la vitesse de scraping"""
        print("  🚀 Test de vitesse de scraping...")
        
        try:
            start_time = time.time()
            
            # Test avec une URL simple
            payload = {
                "urls": ["https://httpbin.org/json"],
                "analysis_type": "standard"
            }
            
            response = self.session.post(f"{self.base_url}/scrape", json=payload, timeout=15)
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("task_id")
                
                # Attendre la completion
                result = self.wait_for_task_completion(task_id, timeout=20)
                end_time = time.time()
                
                total_time = end_time - start_time
                
                if result["status"] == "completed":
                    print(f"    ⚡ Scraping terminé en {total_time:.2f}s")
                    return {"duration": total_time, "status": "success"}
                else:
                    print(f"    ❌ Scraping échoué: {result.get('error')}")
                    return {"duration": total_time, "status": "failed", "error": result.get('error')}
            else:
                print(f"    ❌ Erreur création tâche: {response.status_code}")
                return {"status": "creation_failed"}
                
        except Exception as e:
            print(f"    ❌ Erreur test vitesse: {str(e)}")
            return {"status": "error", "error": str(e)}

    def estimate_memory_usage(self) -> str:
        """Estime l'utilisation mémoire (approximative)"""
        # Cette fonction pourrait être étendue avec des métriques plus précises
        print("  💾 Estimation mémoire: Fonctionnalité à implémenter")
        return "estimation_not_implemented"

    def generate_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur les problèmes trouvés"""
        recommendations = []
        
        if any("API" in issue for issue in self.issues_found):
            recommendations.append("Vérifiez que le service web est démarré avec 'docker-compose up web'")
        
        if any("Celery" in issue for issue in self.issues_found):
            recommendations.append("Redémarrez le worker Celery: 'docker-compose restart worker'")
        
        if any("Redis" in issue for issue in self.issues_found):
            recommendations.append("Vérifiez le service Redis: 'docker-compose logs redis'")
        
        if any("Database" in issue for issue in self.issues_found):
            recommendations.append("Vérifiez la base de données: 'docker-compose logs db'")
        
        if any("Ollama" in issue for issue in self.issues_found):
            recommendations.append("Démarrez Ollama et installez le modèle: 'ollama pull mistral:7b-instruct-v0.2-q4_0'")
        
        if any("scraping" in issue.lower() for issue in self.issues_found):
            recommendations.append("Vérifiez les logs du worker pour les erreurs de scraping")
        
        if not recommendations:
            recommendations.append("🎉 Aucun problème majeur détecté! Le système fonctionne correctement.")
        
        return recommendations

    def print_summary(self, results: Dict[str, Any]):
        """Affiche un résumé du diagnostic"""
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DU DIAGNOSTIC")
        print("=" * 60)
        
        # Statut global
        total_issues = len(self.issues_found)
        if total_issues == 0:
            print("✅ SYSTÈME OPÉRATIONNEL - Aucun problème détecté")
        else:
            print(f"⚠️ {total_issues} PROBLÈME(S) DÉTECTÉ(S)")
        
        # Détail des composants
        components = {
            "API FastAPI": results["api_health"]["status"],
            "Celery": results["celery_status"]["status"],
            "Redis": results["redis_connectivity"]["status"],
            "Base de données": results["database_status"]["status"],
            "Ollama": results["ollama_status"]["status"]
        }
        
        print("\n📊 État des composants:")
        for component, status in components.items():
            icon = "✅" if status in ["healthy", "operational", "connected"] else "❌"
            print(f"  {icon} {component}: {status}")
        
        # Recommandations
        if results["recommendations"]:
            print("\n💡 RECOMMANDATIONS:")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print("\n🔗 Liens utiles:")
        print("  • API: http://localhost:8000/docs")
        print("  • Santé: http://localhost:8000/health") 
        print("  • Debug Celery: http://localhost:8000/debug/celery")

def main():
    """Fonction principale"""
    diagnostic = AgenticScraperDiagnostic()
    
    try:
        results = diagnostic.run_complete_diagnostic()
        
        # Sauvegarder le rapport
        with open("diagnostic_report.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Rapport complet sauvegardé dans 'diagnostic_report.json'")
        
        # Code de sortie basé sur les problèmes trouvés
        return 0 if len(diagnostic.issues_found) == 0 else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Diagnostic interrompu par l'utilisateur")
        return 130
    except Exception as e:
        print(f"\n💥 Erreur fatale du diagnostic: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())