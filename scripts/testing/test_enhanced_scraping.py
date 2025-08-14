#!/usr/bin/env python3
"""
Script de test pour valider l'extraction de valeurs améliorée
"""

import requests
import json
import time
from datetime import datetime
import sys

def test_enhanced_scraping():
    """Teste le scraping amélioré avec différents types d'analyse"""
    
    base_url = "http://localhost:8000"
    
    # URLs de test avec des données économiques
    test_urls = [
        "https://www.ins.tn/statistiques",  # Page principale avec indicateurs
        "https://www.ins.tn/statistiques/90",  # IPC spécifique
        "https://www.bct.gov.tn/bct/siteprod/stat_index.jsp",  # BCT (si accessible)
    ]
    
    print("🚀 Test du Scraping Amélioré pour l'Extraction de Valeurs")
    print("=" * 60)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🎯 Test {i}/3: {url}")
        print("-" * 50)
        
        # Test mode STANDARD
        print("📊 Test mode STANDARD...")
        task_id_standard = create_scraping_task(base_url, url, "standard")
        if task_id_standard:
            results_standard = wait_for_completion(base_url, task_id_standard)
            analyze_results(results_standard, "STANDARD")
        
        time.sleep(2)
        
        # Test mode ADVANCED (avec LLM)
        print("\n🧠 Test mode ADVANCED...")
        task_id_advanced = create_scraping_task(base_url, url, "advanced")
        if task_id_advanced:
            results_advanced = wait_for_completion(base_url, task_id_advanced)
            analyze_results(results_advanced, "ADVANCED")
        
        print("\n" + "="*60)

def create_scraping_task(base_url: str, url: str, analysis_type: str) -> str:
    """Crée une tâche de scraping"""
    try:
        payload = {
            "urls": [url],
            "analysis_type": analysis_type,
            "parameters": {
                "extract_values": True,
                "detailed_analysis": True
            },
            "timeout": 60,
            "priority": 1
        }
        
        response = requests.post(f"{base_url}/scrape", json=payload)
        response.raise_for_status()
        
        data = response.json()
        task_id = data.get('task_id')
        print(f"✅ Tâche créée: {task_id}")
        return task_id
        
    except Exception as e:
        print(f"❌ Erreur création tâche: {e}")
        return None

def wait_for_completion(base_url: str, task_id: str, max_wait: int = 120) -> dict:
    """Attend la completion d'une tâche"""
    print(f"⏳ Attente de completion (max {max_wait}s)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/tasks/{task_id}")
            response.raise_for_status()
            
            data = response.json()
            status = data.get('status')
            progress = data.get('progress', {})
            
            print(f"   Status: {status} - {progress.get('display', 'N/A')}", end='\r')
            
            if status == 'completed':
                print(f"\n✅ Tâche terminée en {time.time() - start_time:.1f}s")
                return data
            elif status == 'failed':
                print(f"\n❌ Tâche échouée: {data.get('error', 'Unknown error')}")
                return data
            
            time.sleep(2)
            
        except Exception as e:
            print(f"\n❌ Erreur vérification status: {e}")
            break
    
    print(f"\n⏰ Timeout après {max_wait}s")
    return {}

def analyze_results(results: dict, mode: str):
    """Analyse les résultats et compte les valeurs extraites"""
    if not results or results.get('status') != 'completed':
        print(f"❌ {mode}: Pas de résultats valides")
        return
    
    task_results = results.get('results', [])
    if not task_results:
        print(f"❌ {mode}: Aucun résultat de scraping")
        return
    
    first_result = task_results[0]
    content = first_result.get('content', {})
    structured_data = content.get('structured_data', {})
    metadata = content.get('metadata', {})
    
    print(f"📊 {mode} - Analyse des résultats:")
    
    # Compter les valeurs par source
    value_counts = {}
    
    # 1. Chiffres clés
    key_figures = structured_data.get('key_figures', {})
    value_counts['key_figures'] = count_values_in_dict(key_figures)
    
    # 2. Données de tableaux
    tables_data = structured_data.get('tables_data', [])
    value_counts['tables'] = count_values_in_tables(tables_data)
    
    # 3. Indicateurs économiques
    indicators = structured_data.get('indicators_with_values', {})
    value_counts['economic_indicators'] = count_values_in_dict(indicators)
    
    # 4. Valeurs extraites (nouveau)
    extracted_values = structured_data.get('extracted_values', {})
    value_counts['extracted_values'] = count_values_in_dict(extracted_values)
    
    # 5. Analyse intelligente
    intelligent_analysis = structured_data.get('intelligent_analysis', {})
    value_counts['intelligent'] = count_intelligent_values(intelligent_analysis)
    
    # Affichage des résultats
    total_values = sum(value_counts.values())
    print(f"   🎯 Total valeurs extraites: {total_values}")
    
    for source, count in value_counts.items():
        if count > 0:
            print(f"   • {source.replace('_', ' ').title()}: {count} valeurs")
    
    # Informations sur les métadonnées
    data_found = metadata.get('data_found', 0)
    method = metadata.get('method', 'unknown')
    print(f"   📋 Méthode: {method}")
    print(f"   📊 Données détectées: {data_found}")
    
    # Exemples de valeurs si disponibles
    print_sample_values(structured_data, mode)

def count_values_in_dict(data_dict: dict) -> int:
    """Compte les valeurs numériques dans un dictionnaire"""
    count = 0
    for key, value in data_dict.items():
        if isinstance(value, dict) and 'value' in value:
            count += 1
        elif isinstance(value, (int, float)):
            count += 1
    return count

def count_values_in_tables(tables: list) -> int:
    """Compte les valeurs dans les données de tableaux"""
    count = 0
    for table in tables:
        if isinstance(table, dict):
            rows = table.get('rows', [])
            for row in rows:
                if isinstance(row, dict):
                    for key, cell_data in row.items():
                        if isinstance(cell_data, dict) and 'value' in cell_data:
                            count += 1
    return count

def count_intelligent_values(analysis: dict) -> int:
    """Compte les valeurs de l'analyse intelligente"""
    count = 0
    if isinstance(analysis, dict):
        insights = analysis.get('insights', {})
        if isinstance(insights, dict):
            numeric_insights = insights.get('numeric_insights', {})
            if isinstance(numeric_insights, dict):
                for key, values in numeric_insights.items():
                    if isinstance(values, list):
                        count += len(values)
    return count

def print_sample_values(structured_data: dict, mode: str):
    """Affiche quelques exemples de valeurs extraites"""
    print(f"   📝 Exemples de valeurs {mode}:")
    
    examples = []
    
    # Exemples des chiffres clés
    key_figures = structured_data.get('key_figures', {})
    for name, info in list(key_figures.items())[:2]:
        if isinstance(info, dict) and 'value' in info:
            examples.append(f"     • {name}: {info['value']} {info.get('unit', '')}")
    
    # Exemples des indicateurs économiques
    indicators = structured_data.get('indicators_with_values', {})
    for name, info in list(indicators.items())[:2]:
        if isinstance(info, dict) and 'value' in info:
            category = info.get('category', 'unknown')
            examples.append(f"     • {category}: {info['value']} {info.get('unit', '')}")
    
    # Exemples des valeurs extraites
    extracted = structured_data.get('extracted_values', {})
    for name, info in list(extracted.items())[:2]:
        if isinstance(info, dict) and 'value' in info:
            examples.append(f"     • {name}: {info['value']} {info.get('unit', '')}")
    
    # Afficher les exemples (max 5)
    for example in examples[:5]:
        print(example)
    
    if len(examples) > 5:
        print(f"     ... et {len(examples) - 5} autres")
    elif not examples:
        print("     Aucun exemple trouvé")

def test_system_health():
    """Teste la santé du système avant les tests"""
    base_url = "http://localhost:8000"
    
    print("🔍 Vérification de la santé du système...")
    
    try:
        # Test health
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        health = response.json()
        
        print(f"   ✅ API: {health.get('status', 'unknown')}")
        
        components = health.get('components', {})
        for component, status in components.items():
            icon = "✅" if status == "available" else "❌"
            print(f"   {icon} {component}: {status}")
        
        # Test Celery debug
        response = requests.get(f"{base_url}/debug/celery")
        response.raise_for_status()
        celery_info = response.json()
        
        print(f"   🔧 Celery: {celery_info.get('celery_status', 'unknown')}")
        print(f"   📋 Tasks: {celery_info.get('task_statistics', {}).get('total_tasks', 0)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur santé système: {e}")
        return False

def save_test_results(all_results: dict):
    """Sauvegarde les résultats de test"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 Résultats sauvegardés: {filename}")
    return filename

def compare_modes(standard_results: dict, advanced_results: dict):
    """Compare les résultats entre les modes STANDARD et ADVANCED"""
    print("\n🔄 Comparaison STANDARD vs ADVANCED:")
    print("-" * 40)
    
    def get_total_values(results):
        if not results or results.get('status') != 'completed':
            return 0
        
        task_results = results.get('results', [])
        if not task_results:
            return 0
        
        structured_data = task_results[0].get('content', {}).get('structured_data', {})
        
        total = 0
        total += count_values_in_dict(structured_data.get('key_figures', {}))
        total += count_values_in_tables(structured_data.get('tables_data', []))
        total += count_values_in_dict(structured_data.get('indicators_with_values', {}))
        total += count_values_in_dict(structured_data.get('extracted_values', {}))
        total += count_intelligent_values(structured_data.get('intelligent_analysis', {}))
        
        return total
    
    standard_values = get_total_values(standard_results)
    advanced_values = get_total_values(advanced_results)
    
    print(f"   📊 STANDARD: {standard_values} valeurs")
    print(f"   🧠 ADVANCED: {advanced_values} valeurs")
    
    if advanced_values > standard_values:
        improvement = advanced_values - standard_values
        percentage = ((improvement / max(standard_values, 1)) * 100)
        print(f"   🚀 Amélioration: +{improvement} valeurs (+{percentage:.1f}%)")
    elif advanced_values == standard_values:
        print(f"   ➡️ Résultats identiques")
    else:
        print(f"   ⚠️ Mode ADVANCED moins performant")

def main():
    """Fonction principale du test"""
    print("🧪 SCRIPT DE TEST - EXTRACTION DE VALEURS AMÉLIORÉE")
    print("=" * 60)
    
    # Vérifier la santé du système
    if not test_system_health():
        print("❌ Système non prêt, arrêt des tests")
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # URLs de test simplifiées pour commencer
    test_urls = [
        "https://www.ins.tn/statistiques",
    ]
    
    all_results = {}
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🎯 Test {i}/{len(test_urls)}: {url}")
        print("-" * 50)
        
        url_results = {}
        
        # Test STANDARD
        print("📊 Mode STANDARD...")
        task_id = create_scraping_task("http://localhost:8000", url, "standard")
        if task_id:
            standard_results = wait_for_completion("http://localhost:8000", task_id)
            url_results['standard'] = standard_results
            analyze_results(standard_results, "STANDARD")
        
        time.sleep(3)
        
        # Test ADVANCED
        print("\n🧠 Mode ADVANCED...")
        task_id = create_scraping_task("http://localhost:8000", url, "advanced")
        if task_id:
            advanced_results = wait_for_completion("http://localhost:8000", task_id)
            url_results['advanced'] = advanced_results
            analyze_results(advanced_results, "ADVANCED")
        
        # Comparaison
        if 'standard' in url_results and 'advanced' in url_results:
            compare_modes(url_results['standard'], url_results['advanced'])
        
        all_results[url] = url_results
        print("\n" + "="*60)
    
    # Sauvegarde des résultats
    save_test_results(all_results)
    
    print("\n🎉 Tests terminés!")
    print("📋 Résumé:")
    print("   • Vérifiez que les valeurs numériques sont bien extraites")
    print("   • Comparez les performances entre STANDARD et ADVANCED")
    print("   • Analysez les fichiers de résultats pour plus de détails")

if __name__ == "__main__":
    main()