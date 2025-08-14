#!/usr/bin/env python3
"""
Script pour scraper les vraies pages de données économiques de l'INS
Au lieu de la page d'index, nous ciblons les pages spécifiques avec des valeurs
"""

import requests
import json
from typing import List, Dict

# URLs cibles contenant les vraies données économiques
ECONOMIC_DATA_URLS = {
    "inflation_ipc": "https://www.ins.tn/statistiques/90",  # IPC - Inflation
    "balance_commerciale": "https://www.ins.tn/statistiques/50",  # Balance commerciale
    "comptes_nationaux": "https://www.ins.tn/statistiques/74",  # Agrégats économiques
    "chomage": "https://www.ins.tn/statistiques/153",  # Chômage
    "population": "https://www.ins.tn/statistiques/111",  # Estimation population
    "croissance_pib": "https://www.ins.tn/statistiques/73",  # PIB et croissance
    "commerce_exterieur": "https://www.ins.tn/statistiques/52",  # Commerce extérieur
    "prix_immobilier": "https://www.ins.tn/statistiques/91",  # Prix immobilier
    "salaires": "https://www.ins.tn/statistiques/97",  # SMIG
    "production_industrielle": "https://www.ins.tn/statistiques/138"  # Production industrielle
}

def test_economic_urls_scraping():
    """
    Test de scraping des vraies pages de données économiques
    """
    
    print("🎯 TEST DES URLS AVEC VRAIES DONNÉES ÉCONOMIQUES")
    print("=" * 60)
    
    # Configuration pour les tests
    api_base = "http://localhost:8000"
    
    results = {}
    
    for category, url in ECONOMIC_DATA_URLS.items():
        print(f"\n📊 Test {category}: {url}")
        print("-" * 40)
        
        try:
            # Lancer une tâche de scraping
            response = requests.post(f"{api_base}/scrape", json={
                "urls": [url],
                "analysis_type": "standard",
                "parameters": {
                    "extract_values": True,
                    "detailed_analysis": True
                },
                "timeout": 30,
                "depth": 1
            })
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get('task_id')
                print(f"✅ Tâche créée: {task_id}")
                
                # Attendre un moment et récupérer les résultats
                import time
                time.sleep(5)  # Attendre 5 secondes
                
                # Récupérer les résultats
                result_response = requests.get(f"{api_base}/tasks/{task_id}")
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    status = result_data.get('status')
                    
                    if status == 'completed':
                        # Analyser les résultats
                        task_results = result_data.get('results', [])
                        if task_results:
                            extracted = task_results[0].get('content', {}).get('structured_data', {}).get('extracted_values', {})
                            values_count = len(extracted)
                            print(f"📈 Valeurs extraites: {values_count}")
                            
                            # Exemples de valeurs
                            if extracted:
                                print("📝 Exemples:")
                                for i, (key, value) in enumerate(list(extracted.items())[:3]):
                                    if isinstance(value, dict):
                                        val = value.get('value', value)
                                        unit = value.get('unit', '')
                                        print(f"   • {key}: {val} {unit}")
                                    else:
                                        print(f"   • {key}: {value}")
                            
                            results[category] = {
                                'url': url,
                                'values_count': values_count,
                                'status': 'success',
                                'task_id': task_id
                            }
                        else:
                            print("⚠️ Aucun résultat dans la réponse")
                            results[category] = {'url': url, 'status': 'no_results'}
                    else:
                        print(f"⏳ Status: {status}")
                        results[category] = {'url': url, 'status': status}
                else:
                    print(f"❌ Erreur récupération résultats: {result_response.status_code}")
                    results[category] = {'url': url, 'status': 'fetch_error'}
            else:
                print(f"❌ Erreur création tâche: {response.status_code}")
                results[category] = {'url': url, 'status': 'creation_error'}
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            results[category] = {'url': url, 'status': 'error', 'error': str(e)}
    
    # Résumé final
    print(f"\n🎯 RÉSUMÉ FINAL:")
    print("=" * 40)
    
    total_urls = len(ECONOMIC_DATA_URLS)
    successful = sum(1 for r in results.values() if r.get('status') == 'success')
    total_values = sum(r.get('values_count', 0) for r in results.values())
    
    print(f"📊 URLs testées: {total_urls}")
    print(f"✅ Succès: {successful}")
    print(f"🎯 Total valeurs extraites: {total_values}")
    print(f"📈 Taux de succès: {(successful/total_urls)*100:.1f}%")
    
    # Top 3 des meilleures extractions
    sorted_results = sorted(
        [(k, v) for k, v in results.items() if v.get('values_count', 0) > 0],
        key=lambda x: x[1].get('values_count', 0),
        reverse=True
    )
    
    if sorted_results:
        print(f"\n🏆 TOP 3 DES MEILLEURES EXTRACTIONS:")
        for i, (category, data) in enumerate(sorted_results[:3], 1):
            values_count = data.get('values_count', 0)
            print(f"   {i}. {category}: {values_count} valeurs")
    
    # Sauvegarder les résultats
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"economic_urls_test_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés: {filename}")
    
    return results

def analyze_page_structure(url: str):
    """
    Analyse la structure d'une page pour voir si elle contient des valeurs
    """
    
    print(f"\n🔍 ANALYSE DE STRUCTURE: {url}")
    print("-" * 50)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Analyser le contenu
        text = soup.get_text()
        
        # Chercher des patterns économiques
        import re
        
        economic_patterns = {
            'percentages': r'(\d+[,.]?\d*)\s*%',
            'millions_dinars': r'(\d+[,.]?\d*)\s*(?:MD|millions?\s*(?:de\s*)?dinars?)',
            'decimals': r'(\d+[,]\d+)',
            'large_numbers': r'(\d{1,3}(?:[\s.]\d{3})+)',
            'inflation_context': r'inflation.*?(\d+[,.]?\d*)',
            'chomage_context': r'chômage.*?(\d+[,.]?\d*)',
            'croissance_context': r'croissance.*?(\d+[,.]?\d*)'
        }
        
        findings = {}
        total_matches = 0
        
        for pattern_name, pattern in economic_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                findings[pattern_name] = matches[:5]  # Garder 5 premiers
                total_matches += len(matches)
                print(f"   ✅ {pattern_name}: {len(matches)} matches -> {matches[:3]}")
        
        print(f"\n📊 Total patterns trouvés: {total_matches}")
        
        # Chercher des tableaux
        tables = soup.find_all('table')
        print(f"📋 Tableaux trouvés: {len(tables)}")
        
        # Chercher des divs avec classes statistiques
        stat_elements = soup.find_all(class_=re.compile(r'(stat|data|value|chiffre|indicateur)', re.I))
        print(f"📈 Éléments statistiques: {len(stat_elements)}")
        
        return {
            'total_patterns': total_matches,
            'patterns_found': findings,
            'tables_count': len(tables),
            'stat_elements': len(stat_elements),
            'has_economic_data': total_matches > 0
        }
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        return {'error': str(e)}

def main():
    """Fonction principale"""
    
    print("🚀 DIAGNOSTIC DES VRAIES PAGES ÉCONOMIQUES INS")
    print("=" * 60)
    
    # D'abord analyser quelques pages pour voir leur structure
    sample_urls = [
        "https://www.ins.tn/statistiques/90",   # IPC
        "https://www.ins.tn/statistiques/50",   # Balance commerciale
        "https://www.ins.tn/statistiques/153"   # Chômage
    ]
    
    print("🔍 PHASE 1: ANALYSE DE STRUCTURE")
    structure_results = {}
    
    for url in sample_urls:
        result = analyze_page_structure(url)
        structure_results[url] = result
    
    # Voir quelles pages ont des données économiques
    promising_urls = [
        url for url, data in structure_results.items() 
        if data.get('has_economic_data', False)
    ]
    
    print(f"\n✅ Pages prometteuses: {len(promising_urls)}")
    for url in promising_urls:
        print(f"   • {url}")
    
    if promising_urls:
        print("\n🎯 PHASE 2: TEST DE SCRAPING")
        # Tester le scraping sur les pages prometteuses
        scraping_results = test_economic_urls_scraping()
        
        print(f"\n🎉 CONCLUSION:")
        if any(r.get('values_count', 0) > 0 for r in scraping_results.values()):
            print("✅ SUCCESS ! Des valeurs économiques ont été extraites !")
            print("💡 Utilisez ces URLs spécifiques au lieu de /statistiques")
        else:
            print("⚠️ Aucune valeur extraite - besoin d'ajustements")
    else:
        print("\n⚠️ Aucune page ne semble contenir des données économiques directes")
        print("💡 Les données sont probablement générées en JavaScript")

if __name__ == "__main__":
    main()