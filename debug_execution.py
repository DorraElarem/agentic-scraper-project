"""
Script de diagnostic pour identifier pourquoi l'extraction échoue
"""
import requests
from bs4 import BeautifulSoup
import re
import json

def analyze_page_content(url):
    """Analyse détaillée du contenu d'une page"""
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        analysis = {
            'url': url,
            'status_code': response.status_code,
            'content_length': len(response.text),
            'title': soup.title.text.strip() if soup.title else "No title",
            'tables_found': len(soup.find_all('table')),
            'numeric_values': [],
            'potential_indicators': [],
            'year_mentions': []
        }
        
        # Recherche de valeurs numériques
        numeric_pattern = r'\b\d{1,3}(?:[\s,]\d{3})*(?:[.,]\d+)?\s*(?:%|€|$|TND|MD|milliards?|millions?)\b'
        numbers = re.findall(numeric_pattern, response.text, re.IGNORECASE)
        analysis['numeric_values'] = list(set(numbers))[:20]  # Limiter à 20
        
        # Recherche d'indicateurs économiques tunisiens
        indicators_pattern = r'\b(?:PIB|inflation|chômage|dette|déficit|export|import|taux|cours|indice|population|emploi|salaire|prix|production)\b'
        indicators = re.findall(indicators_pattern, response.text, re.IGNORECASE)
        analysis['potential_indicators'] = list(set(indicators))
        
        # Recherche d'années
        year_pattern = r'\b(20[0-2]\d)\b'
        years = re.findall(year_pattern, response.text)
        analysis['year_mentions'] = list(set(years))
        
        # Analyse des tableaux
        tables = []
        for i, table in enumerate(soup.find_all('table')[:5]):  # Max 5 tableaux
            table_info = {
                'table_index': i,
                'rows': len(table.find_all('tr')),
                'headers': [th.text.strip() for th in table.find_all(['th', 'td'])[:10]],
                'has_numeric_data': bool(re.search(r'\d+', table.text))
            }
            tables.append(table_info)
        
        analysis['tables_detail'] = tables
        
        # Recherche de liens vers données
        data_links = []
        for link in soup.find_all('a', href=True)[:20]:
            href = link['href']
            if any(keyword in href.lower() for keyword in ['statistique', 'donnee', 'data', 'excel', 'csv', 'pdf']):
                data_links.append({
                    'href': href,
                    'text': link.text.strip()[:100]
                })
        
        analysis['data_links'] = data_links
        
        return analysis
        
    except Exception as e:
        return {
            'url': url,
            'error': str(e),
            'status': 'failed'
        }

def diagnose_extraction_issues():
    """Diagnostic complet des URLs problématiques"""
    
    urls_to_test = [
        "https://www.ins.tn/statistiques/50",
        "https://www.bct.gov.tn/bct/siteprod/tableau_statistique_a.jsp?params=PL212010",
        "https://www.finances.gov.tn/fr/les-indicateurs/synthese-des-resultats-des-finances-publiques-budget-de-letat"
    ]
    
    # URLs alternatives plus spécifiques
    alternative_urls = [
        "https://www.ins.tn/fr/publication/enquete-nationale-sur-lemploi-au-quatrieme-trimestre-2023",
        "https://www.bct.gov.tn/bct/siteprod/stat_macro.jsp",
        "https://www.finances.gov.tn/sites/default/files/2024-03/note_conj_t4_2023_fr_0.pdf"
    ]
    
    results = {
        'timestamp': '2025-08-27',
        'diagnosis': 'URLs extraction failure analysis',
        'original_urls': [],
        'alternative_urls': [],
        'recommendations': []
    }
    
    print("Analyse des URLs originales...")
    for url in urls_to_test:
        print(f"Analysing: {url}")
        analysis = analyze_page_content(url)
        results['original_urls'].append(analysis)
        print(f"- Tables found: {analysis.get('tables_found', 0)}")
        print(f"- Numeric values: {len(analysis.get('numeric_values', []))}")
        print(f"- Indicators: {analysis.get('potential_indicators', [])}")
        print()
    
    print("Test d'URLs alternatives...")
    for url in alternative_urls:
        print(f"Testing alternative: {url}")
        analysis = analyze_page_content(url)
        results['alternative_urls'].append(analysis)
    
    # Générer des recommandations
    recommendations = []
    
    for url_analysis in results['original_urls']:
        if url_analysis.get('tables_found', 0) == 0:
            recommendations.append(f"URL {url_analysis['url']}: Aucun tableau trouvé - probablement une page de navigation")
        
        if len(url_analysis.get('numeric_values', [])) < 5:
            recommendations.append(f"URL {url_analysis['url']}: Peu de données numériques - vérifier si c'est la bonne page")
        
        if len(url_analysis.get('data_links', [])) > 0:
            recommendations.append(f"URL {url_analysis['url']}: Liens vers données trouvés - explorer ces liens")
    
    results['recommendations'] = recommendations
    
    # Sauvegarder les résultats
    with open('extraction_diagnosis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

if __name__ == "__main__":
    results = diagnose_extraction_issues()
    print("\n=== DIAGNOSTIC TERMINÉ ===")
    print(f"Résultats sauvegardés dans: extraction_diagnosis.json")
    print("\nRecommandations:")
    for rec in results['recommendations']:
        print(f"- {rec}")