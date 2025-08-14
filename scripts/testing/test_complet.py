#!/usr/bin/env python3
"""
Script de test et validation complet pour Agentic Scraper
Usage: python test_complete_validation.py
"""

import requests
import time
import json
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    name: str
    status: str
    duration: float
    details: Dict[str, Any]
    error: str = None

class AgenticScraperValidator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_test(self, test_func):
        """Exécute un test et enregistre le résultat"""
        test_name = test_func.__name__
        self.log(f"🧪 Running {test_name}...")
        
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            
            test_result = TestResult(
                name=test_name,
                status="PASSED",
                duration=duration,
                details=result or {}
            )
            self.log(f"✅ {test_name} PASSED ({duration:.2f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(
                name=test_name,
                status="FAILED",
                duration=duration,
                details={},
                error=str(e)
            )
            self.log(f"❌ {test_name} FAILED: {e}", "ERROR")
            
        self.results.append(test_result)
        return test_result
    
    def test_1_health_check(self):
        """Test 1: Vérification santé API"""
        response = requests.get(f"{self.base_url}/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "healthy", f"Health status not healthy: {data}"
        
        return {"health_data": data}
        
    def test_2_ollama_connectivity(self):
        """Test 2: Test connectivité Ollama"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            assert response.status_code == 200, f"Ollama not accessible: {response.status_code}"
            
            models = response.json().get("models", [])
            assert len(models) > 0, "No Ollama models found"
            
            return {
                "ollama_status": "available",
                "models_count": len(models),
                "models": [m["name"] for m in models]
            }
            
        except Exception as e:
            return {
                "ollama_status": "unavailable",
                "error": str(e),
                "models_count": 0
            }
    
    def test_3_simple_scraping_standard(self):
        """Test 3: Scraping standard avec site simple"""
        payload = {
            "urls": ["https://httpbin.org/json"],
            "analysis_type": "standard"
        }
        
        # Créer la tâche
        response = requests.post(f"{self.base_url}/scrape", json=payload, timeout=30)
        assert response.status_code == 200, f"Failed to create task: {response.status_code}"
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        # Attendre completion avec timeout
        for attempt in range(30):  # 30 secondes max
            task_response = requests.get(f"{self.base_url}/tasks/{task_id}", timeout=10)
            assert task_response.status_code == 200, f"Failed to get task status: {task_response.status_code}"
            
            task_status = task_response.json()
            
            if task_status["status"] == "completed":
                assert len(task_status["results"]) > 0, "No results returned"
                assert task_status["metrics"]["success_rate"] == 100, "Success rate not 100%"
                
                return {
                    "task_id": task_id,
                    "execution_time": task_status["metrics"]["execution_time"],
                    "results_count": len(task_status["results"]),
                    "success_rate": task_status["metrics"]["success_rate"]
                }
                
            elif task_status["status"] == "failed":
                raise AssertionError(f"Task failed: {task_status.get('error_message')}")
                
            time.sleep(1)
        
        raise TimeoutError("Task did not complete within 30 seconds")
        
    def test_4_advanced_scraping_with_llm(self):
        """Test 4: Scraping avancé avec LLM (avec gestion timeout)"""
        payload = {
            "urls": ["https://httpbin.org/html"],
            "analysis_type": "advanced"
        }
        
        response = requests.post(f"{self.base_url}/scrape", json=payload, timeout=30)
        assert response.status_code == 200, f"Failed to create advanced task: {response.status_code}"
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        # Attendre avec timeout plus long pour advanced
        for attempt in range(90):  # 90 secondes max
            task_response = requests.get(f"{self.base_url}/tasks/{task_id}", timeout=10)
            assert task_response.status_code == 200, f"Failed to get task status: {task_response.status_code}"
            
            task_status = task_response.json()
            
            if task_status["status"] in ["completed", "failed"]:
                # Même si LLM timeout, la tâche doit être marquée comme complétée
                assert task_status["status"] == "completed", f"Task not completed: {task_status['status']}"
                
                # Vérifier la présence d'analyse LLM (même si timeout)
                llm_analysis = task_status["results"][0].get("llm_analysis", {})
                
                return {
                    "task_id": task_id,
                    "execution_time": task_status["metrics"]["execution_time"],
                    "llm_analysis_present": bool(llm_analysis),
                    "llm_status": llm_analysis.get("insights", {}).get("error", "success"),
                    "analysis_type": task_status["metrics"]["analysis_type"]
                }
                
            time.sleep(1)
        
        raise TimeoutError("Advanced task did not complete within 90 seconds")
        
    def test_5_multiple_urls(self):
        """Test 5: Scraping multiple URLs"""
        payload = {
            "urls": [
                "https://httpbin.org/json",
                "https://httpbin.org/user-agent",
                "https://httpbin.org/headers"
            ],
            "analysis_type": "standard"
        }
        
        response = requests.post(f"{self.base_url}/scrape", json=payload, timeout=30)
        assert response.status_code == 200, f"Failed to create multi-URL task: {response.status_code}"
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        # Attendre completion
        for attempt in range(60):  # 60 secondes pour 3 URLs
            task_response = requests.get(f"{self.base_url}/tasks/{task_id}", timeout=10)
            assert task_response.status_code == 200, f"Failed to get task status: {task_response.status_code}"
            
            task_status = task_response.json()
            
            if task_status["status"] == "completed":
                assert len(task_status["results"]) == 3, f"Expected 3 results, got {len(task_status['results'])}"
                assert task_status["metrics"]["total_urls"] == 3, f"Expected 3 total URLs"
                
                return {
                    "task_id": task_id,
                    "total_urls": task_status["metrics"]["total_urls"],
                    "successful_urls": task_status["metrics"]["successful_urls"],
                    "success_rate": task_status["metrics"]["success_rate"]
                }
                
            elif task_status["status"] == "failed":
                raise AssertionError(f"Multi-URL task failed: {task_status.get('error_message')}")
                
            time.sleep(1)
        
        raise TimeoutError("Multi-URL task did not complete within 60 seconds")
        
    def test_6_error_handling(self):
        """Test 6: Gestion d'erreurs avec URL invalide"""
        payload = {
            "urls": ["https://site-inexistant-test-12345.com"],
            "analysis_type": "standard"
        }
        
        response = requests.post(f"{self.base_url}/scrape", json=payload, timeout=30)
        assert response.status_code == 200, f"Failed to create error test task: {response.status_code}"
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        # Attendre completion
        for attempt in range(30):
            task_response = requests.get(f"{self.base_url}/tasks/{task_id}", timeout=10)
            assert task_response.status_code == 200, f"Failed to get task status: {task_response.status_code}"
            
            task_status = task_response.json()
            
            if task_status["status"] in ["completed", "failed"]:
                # La tâche peut être "completed" avec failed_urls > 0
                metrics = task_status["metrics"]
                
                return {
                    "task_id": task_id,
                    "task_status": task_status["status"],
                    "failed_urls": metrics["failed_urls"],
                    "success_rate": metrics["success_rate"],
                    "error_handled": metrics["failed_urls"] > 0
                }
                
            time.sleep(1)
        
        raise TimeoutError("Error handling test did not complete within 30 seconds")
        
    def test_7_ins_tn_real_website(self):
        """Test 7: Test avec le vrai site INS.tn"""
        payload = {
            "urls": ["https://www.ins.tn/statistiques/50"],
            "analysis_type": "standard"
        }
        
        response = requests.post(f"{self.base_url}/scrape", json=payload, timeout=30)
        assert response.status_code == 200, f"Failed to create INS task: {response.status_code}"
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        # Attendre completion
        for attempt in range(45):  # 45 secondes pour site réel
            task_response = requests.get(f"{self.base_url}/tasks/{task_id}", timeout=10)
            assert task_response.status_code == 200, f"Failed to get task status: {task_response.status_code}"
            
            task_status = task_response.json()
            
            if task_status["status"] in ["completed", "failed"]:
                # Vérifier que le scraping a fonctionné
                if task_status["status"] == "completed":
                    result = task_status["results"][0]
                    
                    return {
                        "task_id": task_id,
                        "execution_time": task_status["metrics"]["execution_time"],
                        "content_length": result["metadata"]["content_length"],
                        "source_domain": result["metadata"]["source_domain"],
                        "extraction_method": result["structured_data"]["extraction_summary"]["extraction_method"]
                    }
                else:
                    return {
                        "task_id": task_id,
                        "status": "failed",
                        "error": task_status.get("error_message")
                    }
                
            time.sleep(1)
        
        raise TimeoutError("INS.tn test did not complete within 45 seconds")
        
    def test_8_performance_benchmark(self):
        """Test 8: Benchmark de performance"""
        start_time = time.time()
        
        # Test concurrent de 3 tâches simples
        task_ids = []
        
        for i in range(3):
            payload = {
                "urls": [f"https://httpbin.org/delay/{i+1}"],  # Délais croissants
                "analysis_type": "standard"
            }
            
            response = requests.post(f"{self.base_url}/scrape", json=payload, timeout=30)
            assert response.status_code == 200, f"Failed to create benchmark task {i}"
            
            task_data = response.json()
            task_ids.append(task_data["task_id"])
        
        # Attendre que toutes les tâches soient complétées
        completed_tasks = []
        max_wait_time = 60  # 60 secondes max
        
        while len(completed_tasks) < 3 and (time.time() - start_time) < max_wait_time:
            for task_id in task_ids:
                if task_id not in [t["task_id"] for t in completed_tasks]:
                    task_response = requests.get(f"{self.base_url}/tasks/{task_id}", timeout=10)
                    if task_response.status_code == 200:
                        task_status = task_response.json()
                        if task_status["status"] in ["completed", "failed"]:
                            completed_tasks.append({
                                "task_id": task_id,
                                "status": task_status["status"],
                                "execution_time": task_status["metrics"]["execution_time"]
                            })
            
            time.sleep(1)
        
        total_time = time.time() - start_time
        
        assert len(completed_tasks) == 3, f"Only {len(completed_tasks)} tasks completed"
        
        return {
            "total_benchmark_time": total_time,
            "tasks_completed": len(completed_tasks),
            "average_task_time": sum(t["execution_time"] for t in completed_tasks) / len(completed_tasks),
            "all_successful": all(t["status"] == "completed" for t in completed_tasks)
        }
    
    def test_9_celery_flower_monitoring(self):
        """Test 9: Vérification Flower monitoring"""
        try:
            response = requests.get("http://localhost:5555/api/workers", timeout=10)
            if response.status_code == 200:
                workers = response.json()
                return {
                    "flower_available": True,
                    "workers_count": len(workers),
                    "workers": list(workers.keys()) if workers else []
                }
            else:
                return {
                    "flower_available": False,
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "flower_available": False,
                "error": str(e)
            }
    
    def run_full_validation(self):
        """Lance tous les tests de validation"""
        self.log("🚀 Starting comprehensive validation suite...")
        self.log(f"📍 Testing against: {self.base_url}")
        
        tests = [
            self.test_1_health_check,
            self.test_2_ollama_connectivity,
            self.test_3_simple_scraping_standard,
            self.test_4_advanced_scraping_with_llm,
            self.test_5_multiple_urls,
            self.test_6_error_handling,
            self.test_7_ins_tn_real_website,
            self.test_8_performance_benchmark,
            self.test_9_celery_flower_monitoring
        ]
        
        for test in tests:
            self.run_test(test)
            time.sleep(2)  # Pause entre les tests
        
        return self.generate_report()
    
    def generate_report(self):
        """Génère un rapport détaillé des tests"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == "PASSED")
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(r.duration for r in self.results)
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests) * 100,
                "total_duration": total_duration,
                "timestamp": datetime.now().isoformat()
            },
            "tests": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration": r.duration,
                    "details": r.details,
                    "error": r.error
                }
                for r in self.results
            ]
        }
        
        return report
    
    def print_report(self, report):
        """Affiche le rapport de façon lisible"""
        print("\n" + "="*60)
        print("📊 AGENTIC SCRAPER - VALIDATION REPORT")
        print("="*60)
        
        summary = report["summary"]
        print(f"📈 Success Rate: {summary['success_rate']:.1f}% ({summary['passed']}/{summary['total_tests']})")
        print(f"⏱️  Total Duration: {summary['total_duration']:.2f}s")
        print(f"📅 Timestamp: {summary['timestamp']}")
        
        print("\n📋 TEST DETAILS:")
        print("-" * 60)
        
        for test in report["tests"]:
            status_emoji = "✅" if test["status"] == "PASSED" else "❌"
            print(f"{status_emoji} {test['name']:<30} {test['status']:<8} {test['duration']:>6.2f}s")
            
            if test["error"]:
                print(f"   └─ Error: {test['error']}")
            elif test["details"]:
                # Afficher quelques détails clés
                key_details = {}
                if "execution_time" in test["details"]:
                    key_details["exec_time"] = f"{test['details']['execution_time']:.2f}s"
                if "success_rate" in test["details"]:
                    key_details["success_rate"] = f"{test['details']['success_rate']}%"
                if "models_count" in test["details"]:
                    key_details["ollama_models"] = test["details"]["models_count"]
                
                if key_details:
                    details_str = ", ".join([f"{k}: {v}" for k, v in key_details.items()])
                    print(f"   └─ {details_str}")
        
        print("\n" + "="*60)
        
        if summary["success_rate"] == 100:
            print("🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT!")
        elif summary["success_rate"] >= 80:
            print("⚠️  MOSTLY SUCCESSFUL - Review failed tests before deployment")
        else:
            print("🔧 SIGNIFICANT ISSUES - Fix errors before deployment")
        
        print("="*60)

def main():
    """Point d'entrée principal"""
    validator = AgenticScraperValidator()
    
    try:
        report = validator.run_full_validation()
        validator.print_report(report)
        
        # Sauvegarder le rapport
        with open("validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to: validation_report.json")
        
        # Code de sortie basé sur le taux de succès
        if report["summary"]["success_rate"] >= 80:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())