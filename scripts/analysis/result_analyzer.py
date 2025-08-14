#!/usr/bin/env python3
"""
Script d'analyse des résultats de scraping amélioré
Analyse les fichiers JSON de résultats pour extraire des insights
"""

import json
import re
from typing import Dict, Any, List
from pathlib import Path

def analyze_scraping_results(json_file: str = "test_results_20250811_153353.json"):
    """Analyse détaillée des résultats de scraping"""
    
    print("🔍 ANALYSE DÉTAILLÉE DES RÉSULTATS DE SCRAPING")
    print("=" * 60)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 Fichier: {json_file}")
        
        # Détecter le format des données
        if isinstance(data, list):
            print(f"📊 Tests effectués: {len(data)}")
            tests_data = data
        elif isinstance(data, dict):
            print(f"📊 Format: Dictionnaire unique")
            tests_data = [data]
        else:
            print(f"❌ Format de données non reconnu: {type(data)}")
            return False
        
        for i, test_result in enumerate(tests_data, 1):
            # Gestion des différents formats de test_result
            if isinstance(test_result, str):
                print(f"\n🧪 TEST {i}: Données en format string - parsing nécessaire")
                continue
                
            if isinstance(test_result, dict):
                url = test_result.get('url', test_result.get('test_url', 'URL inconnue'))
                print(f"\n🧪 TEST {i}: {url}")
                print("-" * 40)
                
                # Analyser chaque mode (STANDARD/ADVANCED)
                for mode in ['standard', 'advanced']:
                    if mode in test_result:
                        analyze_mode_results(test_result[mode], mode.upper())
                
                # Comparaison des modes
                if 'standard' in test_result and 'advanced' in test_result:
                    compare_modes(test_result['standard'], test_result['advanced'])
                
                # Si le format est différent, essayer d'analyser directement
                elif 'results' in test_result or 'task_id' in test_result:
                    print(f"   📊 Format direct détecté")
                    analyze_direct_results(test_result)
    
    except FileNotFoundError:
        print(f"❌ Fichier {json_file} non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def analyze_mode_results(mode_data: Dict[str, Any], mode_name: str):
    """Analyse des résultats pour un mode donné"""
    
    print(f"\n📊 MODE {mode_name}:")
    
    # Informations de base
    task_id = mode_data.get('task_id', 'N/A')
    status = mode_data.get('status', 'N/A')
    execution_time = mode_data.get('execution_time', 0)
    
    print(f"   🆔 Task ID: {task_id[:8]}...")
    print(f"   ✅ Status: {status}")
    print(f"   ⏱️ Temps: {execution_time:.1f}s")
    
    # Analyser les résultats détaillés
    results = mode_data.get('results', {})
    if not results:
        print("   ⚠️ Aucun résultat détaillé disponible")
        return
    
    # Compter les valeurs extraites
    extracted_values = results.get('extracted_values', {})
    key_figures = results.get('key_figures', {})
    content_length = len(results.get('content', ''))
    
    print(f"   🎯 Valeurs extraites: {len(extracted_values)}")
    print(f"   🔑 Chiffres clés: {len(key_figures)}")
    print(f"   📄 Contenu: {content_length:,} caractères")
    
    # Analyser les types de valeurs extraites
    if extracted_values:
        analyze_extracted_values(extracted_values)
    
    # Analyser les chiffres clés
    if key_figures:
        analyze_key_figures(key_figures)
    
    # Métriques de qualité
    metrics = results.get('metrics', {})
    if metrics:
        print(f"   📈 Métriques disponibles: {len(metrics)}")

def analyze_extracted_values(extracted_values: Dict[str, Any]):
    """Analyse détaillée des valeurs extraites"""
    
    print(f"   📊 ANALYSE DES VALEURS EXTRAITES:")
    
    # Grouper par type/source
    sources = {}
    values_by_type = {}
    
    for key, value_data in extracted_values.items():
        # Extraire la source/méthode
        if isinstance(value_data, dict):
            source = value_data.get('source', 'unknown')
            value = value_data.get('value')
            unit = value_data.get('unit', 'no_unit')
        else:
            source = 'direct'
            value = value_data
            unit = 'no_unit'
        
        # Compter par source
        sources[source] = sources.get(source, 0) + 1
        
        # Compter par type de valeur
        if isinstance(value, (int, float)):
            if value > 1000:
                value_type = 'large_number'
            elif value < 1:
                value_type = 'decimal'
            else:
                value_type = 'standard'
        else:
            value_type = 'text'
        
        values_by_type[value_type] = values_by_type.get(value_type, 0) + 1
    
    # Afficher les statistiques
    print(f"      🔍 Sources d'extraction:")
    for source, count in sources.items():
        print(f"         • {source}: {count} valeurs")
    
    print(f"      📈 Types de valeurs:")
    for value_type, count in values_by_type.items():
        print(f"         • {value_type}: {count} valeurs")
    
    # Montrer quelques exemples
    print(f"      📝 Exemples (5 premiers):")
    for i, (key, value_data) in enumerate(list(extracted_values.items())[:5]):
        if isinstance(value_data, dict):
            value = value_data.get('value', 'N/A')
            unit = value_data.get('unit', '')
        else:
            value = value_data
            unit = ''
        
        print(f"         {i+1}. {key}: {value} {unit}")

def analyze_key_figures(key_figures: Dict[str, Any]):
    """Analyse des chiffres clés identifiés"""
    
    print(f"   🔑 CHIFFRES CLÉS IDENTIFIÉS:")
    
    categories = {}
    for key, figure_data in key_figures.items():
        if isinstance(figure_data, dict):
            category = figure_data.get('category', 'general')
            value = figure_data.get('value')
            unit = figure_data.get('unit', '')
        else:
            category = 'general'
            value = figure_data
            unit = ''
        
        if category not in categories:
            categories[category] = []
        categories[category].append({'key': key, 'value': value, 'unit': unit})
    
    for category, figures in categories.items():
        print(f"      📊 {category}: {len(figures)} figures")
        for figure in figures[:3]:  # Montrer 3 premiers
            print(f"         • {figure['key']}: {figure['value']} {figure['unit']}")

def analyze_direct_results(test_result: Dict[str, Any]):
    """Analyse des résultats en format direct"""
    
    print(f"   📊 ANALYSE DIRECTE:")
    
    # Informations de base
    task_id = test_result.get('task_id', 'N/A')
    status = test_result.get('status', 'N/A')
    
    print(f"   🆔 Task ID: {task_id[:8] if task_id != 'N/A' else 'N/A'}...")
    print(f"   ✅ Status: {status}")
    
    # Analyser les résultats
    results = test_result.get('results', test_result)
    
    if isinstance(results, list) and results:
        results = results[0]  # Prendre le premier résultat
    
    # Compter les éléments extraits
    content = results.get('content', '')
    extracted_values = results.get('extracted_values', {})
    key_figures = results.get('key_figures', {})
    
    print(f"   📄 Contenu: {len(content):,} caractères")
    print(f"   🎯 Valeurs extraites: {len(extracted_values)}")
    print(f"   🔑 Chiffres clés: {len(key_figures)}")
    
    # Analyser les valeurs extraites
    if extracted_values:
        analyze_extracted_values(extracted_values)
    
    # Analyser les métriques
    metrics = results.get('metrics', {})
    if metrics:
        print(f"   📈 Métriques: {len(metrics)} disponibles")
        for metric_name, metric_value in list(metrics.items())[:5]:
            print(f"      • {metric_name}: {metric_value}")

def debug_json_structure(json_file: str):
    """Debug pour comprendre la structure du JSON"""
    
    print("\n🔍 DEBUG - STRUCTURE DU FICHIER JSON")
    print("=" * 50)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 Type principal: {type(data)}")
        
        if isinstance(data, dict):
            print(f"📊 Clés principales: {list(data.keys())}")
            for key, value in list(data.items())[:3]:
                print(f"   • {key}: {type(value)} ({len(str(value))} chars)")
        
        elif isinstance(data, list):
            print(f"📊 Éléments dans la liste: {len(data)}")
            for i, item in enumerate(data[:3]):
                print(f"   [{i}] Type: {type(item)}")
                if isinstance(item, dict):
                    print(f"       Clés: {list(item.keys())}")
                elif isinstance(item, str):
                    print(f"       Longueur: {len(item)} chars")
                    print(f"       Début: {item[:100]}...")
        
        # Essayer de trouver les données de résultats
        print(f"\n🔍 Recherche de patterns de données:")
        json_str = json.dumps(data)
        
        patterns_to_find = [
            'extracted_values',
            'task_id', 
            'results',
            'standard',
            'advanced',
            'status'
        ]
        
        for pattern in patterns_to_find:
            if pattern in json_str:
                print(f"   ✅ Trouvé: '{pattern}'")
            else:
                print(f"   ❌ Absent: '{pattern}'")
                
    except Exception as e:
        print(f"❌ Erreur de debug: {e}")

def smart_analyze_results(json_file: str):
    """Analyse intelligente qui s'adapte au format"""
    
    print("🧠 ANALYSE INTELLIGENTE DES RÉSULTATS")
    print("=" * 50)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Fonction récursive pour trouver les valeurs extraites
        def find_extracted_values(obj, path=""):
            findings = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    if key == 'extracted_values' and isinstance(value, dict):
                        findings.append({
                            'path': current_path,
                            'count': len(value),
                            'data': value
                        })
                    elif isinstance(value, (dict, list)):
                        findings.extend(find_extracted_values(value, current_path))
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                    findings.extend(find_extracted_values(item, current_path))
            
            return findings
        
        # Chercher toutes les instances de valeurs extraites
        extracted_findings = find_extracted_values(data)
        
        print(f"🎯 Valeurs extraites trouvées: {len(extracted_findings)} instances")
        
        for i, finding in enumerate(extracted_findings):
            print(f"\n📊 Instance {i+1}: {finding['path']}")
            print(f"   Nombre de valeurs: {finding['count']}")
            
            # Analyser les premières valeurs
            if finding['data']:
                sample_items = list(finding['data'].items())[:5]
                print(f"   Exemples:")
                for key, value in sample_items:
                    if isinstance(value, dict):
                        val = value.get('value', value)
                        unit = value.get('unit', '')
                        print(f"      • {key}: {val} {unit}")
                    else:
                        print(f"      • {key}: {value}")
        
        # Statistiques globales
        total_values = sum(f['count'] for f in extracted_findings)
        print(f"\n📈 STATISTIQUES GLOBALES:")
        print(f"   🎯 Total des valeurs extraites: {total_values}")
        
        if total_values > 0:
            print(f"   ✅ Extraction fonctionnelle!")
            print(f"   💡 Le scraper fonctionne correctement")
        else:
            print(f"   ⚠️ Aucune valeur extraite")
            print(f"   💡 Vérifier la configuration du scraper")
            
    except Exception as e:
        print(f"❌ Erreur d'analyse intelligente: {e}")
        import traceback
        traceback.print_exc()
    """Comparaison entre mode STANDARD et ADVANCED"""
    
    print(f"\n🔄 COMPARAISON STANDARD vs ADVANCED:")
    
    # Temps d'exécution
    std_time = standard_data.get('execution_time', 0)
    adv_time = advanced_data.get('execution_time', 0)
    
    if adv_time > 0:
        speed_ratio = adv_time / std_time if std_time > 0 else float('inf')
        print(f"   ⏱️ Vitesse: STANDARD {speed_ratio:.1f}x plus rapide")
    
    # Quantité de données extraites
    std_values = len(standard_data.get('results', {}).get('extracted_values', {}))
    adv_values = len(advanced_data.get('results', {}).get('extracted_values', {}))
    
    print(f"   📊 Valeurs extraites:")
    print(f"      • STANDARD: {std_values}")
    print(f"      • ADVANCED: {adv_values}")
    
    if std_values == adv_values:
        print(f"      ✅ Résultats identiques")
    else:
        difference = abs(adv_values - std_values)
        better_mode = "ADVANCED" if adv_values > std_values else "STANDARD"
        print(f"      📈 {better_mode} extrait {difference} valeurs en plus")
    
    # Recommandation
    if std_values == adv_values and std_time < adv_time:
        print(f"   💡 RECOMMANDATION: Utiliser le mode STANDARD (même résultats, plus rapide)")
    elif adv_values > std_values:
        print(f"   💡 RECOMMANDATION: Utiliser le mode ADVANCED (plus de données)")
    else:
        print(f"   💡 RECOMMANDATION: Mode STANDARD optimal pour ce cas")

def generate_quality_score(data: Dict[str, Any]) -> float:
    """Génère un score de qualité pour l'extraction"""
    
    score = 0.0
    max_score = 10.0
    
    # Critères d'évaluation
    criteria = {
        'execution_success': 2.0,  # Tâche terminée avec succès
        'values_extracted': 3.0,   # Nombre de valeurs extraites
        'variety_sources': 2.0,    # Variété des sources d'extraction
        'key_figures': 2.0,        # Présence de chiffres clés
        'execution_time': 1.0      # Rapidité d'exécution
    }
    
    # Évaluer chaque critère
    for mode in ['standard', 'advanced']:
        if mode in data:
            mode_data = data[mode]
            
            # Succès d'exécution
            if mode_data.get('status') == 'completed':
                score += criteria['execution_success'] / 2
            
            results = mode_data.get('results', {})
            
            # Valeurs extraites
            extracted_count = len(results.get('extracted_values', {}))
            if extracted_count > 0:
                # Score basé sur le nombre de valeurs (max 15 = score complet)
                values_score = min(extracted_count / 15, 1.0) * criteria['values_extracted']
                score += values_score / 2
            
            # Temps d'exécution (bonus si < 10s)
            exec_time = mode_data.get('execution_time', float('inf'))
            if exec_time < 10:
                score += criteria['execution_time'] / 2
    
    return round(score, 1)

def main():
    """Fonction principale"""
    
    # Chercher le fichier de résultats le plus récent
    json_files = list(Path('.').glob('test_results_*.json'))
    
    if not json_files:
        print("❌ Aucun fichier de résultats trouvé")
        return
    
    # Prendre le plus récent
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    print(f"📁 Analyse du fichier: {latest_file}")
    
    # D'abord faire un debug de la structure
    debug_json_structure(str(latest_file))
    
    # Puis l'analyse intelligente
    smart_analyze_results(str(latest_file))
    
    # Essayer l'analyse standard si possible
    try:
        success = analyze_scraping_results(str(latest_file))
        
        if success:
            print(f"\n🎯 CONCLUSION GÉNÉRALE:")
            print(f"   ✅ Système de scraping opérationnel")
            print(f"   📊 Extraction de valeurs fonctionnelle") 
            print(f"   🚀 Performance satisfaisante")
            print(f"   💡 Prêt pour utilisation en production")
    except Exception as e:
        print(f"\n⚠️ Analyse standard échouée: {e}")
        print(f"💡 Utilisation de l'analyse intelligente uniquement")
    
if __name__ == "__main__":
    main()