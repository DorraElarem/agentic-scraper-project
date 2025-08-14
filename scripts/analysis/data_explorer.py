#!/usr/bin/env python3
"""
Explorateur de données économiques - Compatible avec TARGET_INDICATORS
Analyse les résultats de scraping en utilisant la configuration des settings
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re

# Configuration TARGET_INDICATORS (copie des settings pour standalone)
TARGET_INDICATORS = {
    "comptes_nationaux": [
        "Produit Intérieur Brut (aux prix du marché)",
        "Revenu national",
        "Revenu national disponible brut", 
        "Epargne nationale (brute)",
        "Epargne nationale (nette)",
        "PIB par habitant"
    ],
    "secteurs_institutionnels": [
        "Sociétés non financières",
        "Institutions financières", 
        "Administration Publique",
        "Ménages",
        "Institutions sans but lucratif"
    ],
    "prix_et_inflation": [
        "Indice des prix à la consommation (IPC; 2015=100)",
        "Inflation",
        "Déflateur du PIB", 
        "Indice des prix à la production"
    ],
    "menages": [
        "Revenu disponible brut des ménages",
        "Taille moyenne d'un ménage",
        "Dépenses de consommation finale",
        "Taux d'épargne des ménages"
    ],
    "commerce_exterieur": [
        "Exportations de biens",
        "Importations de biens", 
        "Balance commerciale",
        "Taux de couverture"
    ],
    "finance_et_monnaie": [
        "Masse monétaire M3",
        "Crédits à l'économie",
        "Taux directeur BCT",
        "Réserves de change"
    ]
}

RECOGNIZED_UNITS = {
    "md": "millions de dinars",
    "milliers": "milliers", 
    "dinars courants": "dinars courants",
    "dinars de 2015": "dinars constants 2015",
    "%": "pourcentage",
    "tnd": "dinars tunisiens",
    "usd": "dollars américains",
    "eur": "euros"
}

TARGET_YEARS = list(range(2018, 2026))

def analyze_scraped_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyse complète des données scrapées avec focus sur TARGET_INDICATORS
    """
    analysis = {
        "task_info": extract_task_info(data),
        "content_stats": analyze_content_stats(data),
        "target_indicators_analysis": analyze_target_indicators(data),
        "extracted_values": extract_all_values(data),
        "target_coverage": assess_target_coverage(data),
        "data_quality": assess_data_quality_with_targets(data),
        "recommendations": generate_target_recommendations(data)
    }
    
    return analysis

def extract_task_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait les informations de base de la tâche"""
    results = data.get('results', [])
    first_result = results[0] if results else {}
    
    return {
        "task_id": data.get('task_id', 'unknown'),
        "url": first_result.get('url', 'unknown'),
        "status": data.get('status', 'unknown'),
        "scraped_at": first_result.get('timestamp', 'unknown'),
        "analysis_type": first_result.get('analysis_type', 'unknown'),
        "extraction_method": first_result.get('content', {}).get('structured_data', {}).get('extraction_method', 'unknown')
    }

def analyze_target_indicators(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyse spécifique des TARGET_INDICATORS trouvés"""
    results = data.get('results', [])
    if not results:
        return {"error": "No results found"}
    
    first_result = results[0]
    content = first_result.get('content', {})
    structured_data = content.get('structured_data', {})
    
    target_analysis = {
        "direct_target_matches": {},
        "category_coverage": {},
        "target_indicators_with_values": {},
        "temporal_coverage": {}
    }
    
    # 1. Analyser les target_indicators extraits
    target_indicators = structured_data.get('target_indicators', {})
    if target_indicators:
        for key, indicator_data in target_indicators.items():
            if isinstance(indicator_data, dict):
                category = indicator_data.get('category', 'unknown')
                if category not in target_analysis["direct_target_matches"]:
                    target_analysis["direct_target_matches"][category] = []
                
                target_analysis["direct_target_matches"][category].append({
                    'name': indicator_data.get('indicator_name', key),
                    'value': indicator_data.get('value'),
                    'unit': indicator_data.get('unit'),
                    'confidence': indicator_data.get('confidence', 0),
                    'is_priority': indicator_data.get('is_priority_indicator', False)
                })
    
    # 2. Analyser la couverture par catégorie TARGET
    for category, target_names in TARGET_INDICATORS.items():
        found_indicators = []
        
        # Chercher dans toutes les données extraites
        all_extracted = extract_all_values(data)
        for source_type, values in all_extracted.items():
            for value_info in values:
                name = value_info.get('name', '') or value_info.get('context', '')
                if any(target_name.lower() in name.lower() for target_name in target_names):
                    found_indicators.append({
                        'source': source_type,
                        'name': name,
                        'value': value_info.get('value'),
                        'unit': value_info.get('unit')
                    })
        
        if found_indicators:
            target_analysis["category_coverage"][category] = {
                'indicators_found': len(found_indicators),
                'total_target_indicators': len(target_names),
                'coverage_percentage': (len(found_indicators) / len(target_names)) * 100,
                'details': found_indicators
            }
    
    # 3. Analyser la couverture temporelle (TARGET_YEARS)
    raw_content = content.get('raw_content', '')
    for year in TARGET_YEARS:
        if str(year) in raw_content:
            if year not in target_analysis["temporal_coverage"]:
                target_analysis["temporal_coverage"][year] = []
            
            # Chercher des valeurs associées à cette année
            year_pattern = rf'{year}.*?([0-9]+[,.]?[0-9]*)\s*(?:%|MD|TND|millions?)'
            matches = re.findall(year_pattern, raw_content, re.IGNORECASE)
            for match in matches:
                target_analysis["temporal_coverage"][year].append(match)
    
    return target_analysis

def assess_target_coverage(data: Dict[str, Any]) -> Dict[str, Any]:
    """Évalue la couverture des TARGET_INDICATORS"""
    target_analysis = analyze_target_indicators(data)
    
    coverage = {
        "categories_covered": len(target_analysis.get("category_coverage", {})),
        "total_target_categories": len(TARGET_INDICATORS),
        "overall_coverage_percentage": 0,
        "years_covered": len(target_analysis.get("temporal_coverage", {})),
        "target_years_span": len(TARGET_YEARS),
        "coverage_by_category": {},
        "priority_indicators_found": 0
    }
    
    # Calculer la couverture globale
    if coverage["total_target_categories"] > 0:
        coverage["overall_coverage_percentage"] = (coverage["categories_covered"] / coverage["total_target_categories"]) * 100
    
    # Détail par catégorie
    category_coverage = target_analysis.get("category_coverage", {})
    for category, details in category_coverage.items():
        coverage["coverage_by_category"][category] = details.get("coverage_percentage", 0)
    
    # Compter les indicateurs prioritaires
    direct_matches = target_analysis.get("direct_target_matches", {})
    for category_matches in direct_matches.values():
        for indicator in category_matches:
            if indicator.get('is_priority', False):
                coverage["priority_indicators_found"] += 1
    
    return coverage

def assess_data_quality_with_targets(data: Dict[str, Any]) -> Dict[str, Any]:
    """Évalue la qualité des données avec focus TARGET_INDICATORS"""
    all_values = extract_all_values(data)
    target_coverage = assess_target_coverage(data)
    
    total_values = sum(len(values) for values in all_values.values())
    
    # Calculer la qualité basée sur TARGET_INDICATORS
    target_score = target_coverage["overall_coverage_percentage"] / 100
    
    # Qualité basée sur les unités reconnues
    recognized_unit_values = 0
    for source_values in all_values.values():
        for value_info in source_values:
            unit = value_info.get('unit', '').lower()
            if any(recognized_unit in unit for recognized_unit in RECOGNIZED_UNITS.keys()):
                recognized_unit_values += 1
    
    unit_quality_score = min(recognized_unit_values / max(total_values, 1), 1.0)
    
    # Qualité temporelle (TARGET_YEARS)
    temporal_score = min(target_coverage["years_covered"] / len(TARGET_YEARS), 1.0)
    
    # Score global
    overall_score = (target_score * 0.5 + unit_quality_score * 0.3 + temporal_score * 0.2)
    
    quality_level = 'poor'
    if overall_score > 0.7:
        quality_level = 'excellent'
    elif overall_score > 0.5:
        quality_level = 'good'
    elif overall_score > 0.3:
        quality_level = 'fair'
    
    return {
        'total_values_extracted': total_values,
        'target_coverage_score': target_score,
        'recognized_units_score': unit_quality_score,
        'temporal_coverage_score': temporal_score,
        'overall_score': overall_score,
        'quality_level': quality_level,
        'target_indicators_found': target_coverage["priority_indicators_found"],
        'categories_covered': target_coverage["categories_covered"],
        'recognized_unit_values': recognized_unit_values
    }

def extract_all_values(data: Dict[str, Any]) -> Dict[str, List[Any]]:
    """Extrait toutes les valeurs numériques avec classification TARGET"""
    results = data.get('results', [])
    if not results:
        return {}
    
    first_result = results[0]
    content = first_result.get('content', {})
    structured_data = content.get('structured_data', {})
    
    extracted_values = {
        'target_indicators': [],
        'key_figures': [],
        'table_values': [],
        'economic_indicators': [],
        'intelligent_analysis': [],
        'recognized_units': []
    }
    
    # 1. Extraire les TARGET_INDICATORS spécifiques
    target_indicators = structured_data.get('target_indicators', {})
    for name, info in target_indicators.items():
        if isinstance(info, dict) and 'value' in info:
            extracted_values['target_indicators'].append({
                'name': info.get('indicator_name', name),
                'value': info['value'],
                'unit': info.get('unit', 'unknown'),
                'category': info.get('category', 'unknown'),
                'confidence': info.get('confidence', 0.0),
                'is_priority': info.get('is_priority_indicator', False),
                'source': 'target_extraction'
            })
    
    # 2. Extraire les chiffres clés (existant)
    key_figures = structured_data.get('key_figures', {})
    for name, info in key_figures.items():
        if isinstance(info, dict) and 'value' in info:
            # Classifier selon TARGET_INDICATORS
            category = classify_indicator_as_target(name)
            extracted_values['key_figures'].append({
                'name': name,
                'value': info['value'],
                'unit': info.get('unit', 'unknown'),
                'target_category': category,
                'source': 'key_figures'
            })
    
    # 3. Extraire des tableaux (existant)
    tables_data = structured_data.get('tables_data', [])
    for table in tables_data:
        if isinstance(table, dict):
            rows = table.get('rows', [])
            for row in rows:
                if isinstance(row, dict):
                    for col_name, col_data in row.items():
                        if isinstance(col_data, dict) and 'value' in col_data:
                            indicator_name = row.get('indicator_name', col_name)
                            category = classify_indicator_as_target(indicator_name)
                            extracted_values['table_values'].append({
                                'indicator': indicator_name,
                                'value': col_data['value'],
                                'unit': col_data.get('unit', 'unknown'),
                                'target_category': category,
                                'source': 'table'
                            })
    
    # 4. Valeurs par unités reconnues
    for source_type, values in extracted_values.items():
        for value_info in values:
            unit = value_info.get('unit', '').lower()
            if any(recognized_unit in unit for recognized_unit in RECOGNIZED_UNITS.keys()):
                extracted_values['recognized_units'].append({
                    'original_source': source_type,
                    'name': value_info.get('name', '') or value_info.get('indicator', ''),
                    'value': value_info.get('value'),
                    'recognized_unit': next((k for k in RECOGNIZED_UNITS.keys() if k in unit), 'unknown'),
                    'unit_description': RECOGNIZED_UNITS.get(next((k for k in RECOGNIZED_UNITS.keys() if k in unit), ''), 'unknown')
                })
    
    return extracted_values

def classify_indicator_as_target(name: str) -> str:
    """Classifie un indicateur selon TARGET_INDICATORS"""
    if not name:
        return 'unknown'
    
    name_lower = name.lower()
    
    for category, target_indicators in TARGET_INDICATORS.items():
        for target_indicator in target_indicators:
            if target_indicator.lower() in name_lower or any(word in name_lower for word in target_indicator.lower().split()[:2]):
                return category
    
    # Classification par mots-clés si pas de correspondance exacte
    keyword_mapping = {
        'prix_et_inflation': ['inflation', 'prix', 'ipc'],
        'comptes_nationaux': ['pib', 'revenu', 'épargne', 'national'],
        'commerce_exterieur': ['export', 'import', 'balance', 'commercial'],
        'menages': ['ménage', 'consommation', 'dépense'],
        'finance_et_monnaie': ['monétaire', 'crédit', 'taux', 'banque'],
        'secteurs_institutionnels': ['secteur', 'institution', 'administration']
    }
    
    for category, keywords in keyword_mapping.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    
    return 'other'

def generate_target_recommendations(data: Dict[str, Any]) -> List[str]:
    """Génère des recommandations basées sur TARGET_INDICATORS"""
    recommendations = []
    
    target_coverage = assess_target_coverage(data)
    data_quality = assess_data_quality_with_targets(data)
    
    # Recommandations sur la couverture TARGET
    coverage_pct = target_coverage["overall_coverage_percentage"]
    if coverage_pct == 0:
        recommendations.append("🚨 CRITIQUE: Aucun TARGET_INDICATOR détecté - Vérifier la compatibilité du scraper")
        recommendations.append("🔧 Implémenter les patterns spécifiques pour TARGET_INDICATORS")
    elif coverage_pct < 30:
        recommendations.append(f"⚠️ Couverture TARGET faible ({coverage_pct:.1f}%) - Optimiser l'extraction")
        recommendations.append("🎯 Créer des extracteurs spécialisés par catégorie TARGET")
    else:
        recommendations.append(f"✅ Couverture TARGET acceptable ({coverage_pct:.1f}%)")
    
    # Recommandations par catégorie manquante
    missing_categories = set(TARGET_INDICATORS.keys()) - set(target_coverage["coverage_by_category"].keys())
    if missing_categories:
        recommendations.append(f"📋 Catégories TARGET manquantes: {', '.join(missing_categories)}")
        for category in missing_categories:
            recommendations.append(f"🔍 Développer patterns pour {category}")
    
    # Recommandations sur les unités
    recognized_unit_score = data_quality["recognized_units_score"]
    if recognized_unit_score < 0.5:
        recommendations.append("📏 Améliorer la détection des RECOGNIZED_UNITS")
        recommendations.append("🔧 Implémenter la normalisation des unités selon settings")
    
    # Recommandations temporelles
    temporal_score = data_quality["temporal_coverage_score"] 
    if temporal_score < 0.3:
        recommendations.append(f"📅 Couverture temporelle faible ({target_coverage['years_covered']}/{len(TARGET_YEARS)} années)")
        recommendations.append("🕐 Développer l'extraction de données historiques TARGET_YEARS")
    
    # Recommandations techniques
    if data_quality["target_indicators_found"] == 0:
        recommendations.append("🤖 Activer le mode 'intelligent' pour extraction TARGET avancée")
        recommendations.append("🚀 Tester l'analyse LLM pour identifier les TARGET_INDICATORS")
    
    # Recommandations d'amélioration globale
    quality_level = data_quality["quality_level"]
    if quality_level in ['poor', 'fair']:
        recommendations.append(f"📈 Qualité globale {quality_level} - Optimisations nécessaires")
        recommendations.append("🔄 Réviser les patterns d'extraction pour TARGET_INDICATORS")
    
    # Recommandations stratégiques
    recommendations.append("💾 Sauvegarder les TARGET_INDICATORS extraits pour analyse historique")
    recommendations.append("📊 Créer un dashboard de suivi des TARGET_INDICATORS")
    recommendations.append("🔄 Programmer extractions régulières selon TARGET_YEARS")
    
    return recommendations

def print_target_analysis_summary(analysis: Dict[str, Any]):
    """Affiche un résumé formaté de l'analyse TARGET_INDICATORS"""
    print("🚀 ANALYSE TARGET_INDICATORS - DONNÉES ÉCONOMIQUES TUNISIENNES")
    print("=" * 70)
    
    task_info = analysis['task_info']
    print(f"🔍 Tâche: {task_info['task_id']}")
    print(f"🌐 URL: {task_info['url']}")
    print(f"📅 Extraction: {task_info['scraped_at']}")
    print(f"🔧 Méthode: {task_info['extraction_method']}")
    
    print("\n" + "=" * 70)
    print("📊 COUVERTURE TARGET_INDICATORS")
    print("=" * 70)
    
    target_coverage = analysis['target_coverage']
    print(f"📈 Couverture globale: {target_coverage['overall_coverage_percentage']:.1f}%")
    print(f"📋 Catégories couvertes: {target_coverage['categories_covered']}/{target_coverage['total_target_categories']}")
    print(f"🎯 Indicateurs prioritaires: {target_coverage['priority_indicators_found']}")
    print(f"📅 Années TARGET: {target_coverage['years_covered']}/{target_coverage['target_years_span']}")
    
    # Détail par catégorie
    if target_coverage['coverage_by_category']:
        print(f"\n🔍 DÉTAIL PAR CATÉGORIE TARGET:")
        for category, percentage in target_coverage['coverage_by_category'].items():
            status = "✅" if percentage > 50 else "⚠️" if percentage > 0 else "❌"
            print(f"   {status} {category.replace('_', ' ').title()}: {percentage:.1f}%")
    
    # Analyse des valeurs extraites
    extracted_values = analysis['extracted_values']
    print(f"\n💰 VALEURS EXTRAITES PAR SOURCE:")
    total_values = 0
    for source, values in extracted_values.items():
        if values:
            count = len(values)
            total_values += count
            print(f"   • {source.replace('_', ' ').title()}: {count} valeurs")
            
            # Afficher quelques exemples TARGET
            if source == 'target_indicators':
                for value in values[:3]:
                    print(f"     - {value.get('name', 'N/A')}: {value.get('value', 'N/A')} {value.get('unit', '')}")
                if len(values) > 3:
                    print(f"     ... et {len(values) - 3} autres TARGET_INDICATORS")
    
    print(f"\n📊 TOTAL VALEURS: {total_values}")
    
    # Qualité des données
    quality = analysis['data_quality']
    print(f"\n🎯 QUALITÉ DES DONNÉES TARGET:")
    print(f"   • Score global: {quality['overall_score']:.2f} ({quality['quality_level'].upper()})")
    print(f"   • Score TARGET: {quality['target_coverage_score']:.2f}")
    print(f"   • Unités reconnues: {quality['recognized_units_score']:.2f}")
    print(f"   • Couverture temporelle: {quality['temporal_coverage_score']:.2f}")
    
    # Analyse TARGET_INDICATORS spécifique
    target_analysis = analysis.get('target_indicators_analysis', {})
    direct_matches = target_analysis.get('direct_target_matches', {})
    if direct_matches:
        print(f"\n🎯 TARGET_INDICATORS DIRECTS TROUVÉS:")
        for category, indicators in direct_matches.items():
            print(f"   📁 {category.replace('_', ' ').title()}:")
            for indicator in indicators[:2]:  # Limiter l'affichage
                name = indicator.get('name', 'N/A')
                value = indicator.get('value', 'N/A')
                unit = indicator.get('unit', '')
                confidence = indicator.get('confidence', 0)
                print(f"     • {name}: {value} {unit} (conf: {confidence:.2f})")
    
    # Recommandations
    recommendations = analysis['recommendations']
    print(f"\n🎯 RECOMMANDATIONS TARGET ({len(recommendations)}):")
    for i, rec in enumerate(recommendations[:8], 1):  # Afficher les 8 premières
        print(f"   {i}. {rec}")
    
    if len(recommendations) > 8:
        print(f"   ... et {len(recommendations) - 8} autres recommandations")

def export_target_analysis(analysis: Dict[str, Any]) -> str:
    """Exporte l'analyse TARGET vers un fichier JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"target_indicators_analysis_{timestamp}.json"
    
    # Ajouter métadonnées sur la configuration TARGET
    analysis['metadata'] = {
        'target_indicators_config': TARGET_INDICATORS,
        'recognized_units_config': RECOGNIZED_UNITS,
        'target_years_config': TARGET_YEARS,
        'analysis_timestamp': timestamp,
        'total_target_indicators': sum(len(indicators) for indicators in TARGET_INDICATORS.values()),
        'total_target_categories': len(TARGET_INDICATORS)
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    
    return filename

def validate_target_indicators_extraction(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valide l'extraction contre les TARGET_INDICATORS définis"""
    validation = {
        'total_targets_defined': sum(len(indicators) for indicators in TARGET_INDICATORS.values()),
        'targets_found': 0,
        'categories_with_findings': 0,
        'validation_errors': [],
        'suggestions': []
    }
    
    try:
        extracted_values = extract_all_values(data)
        target_indicators = extracted_values.get('target_indicators', [])
        
        # Compter les TARGET trouvés
        validation['targets_found'] = len(target_indicators)
        
        # Compter les catégories avec des trouvailles
        categories_found = set()
        for indicator in target_indicators:
            category = indicator.get('category', 'unknown')
            if category in TARGET_INDICATORS:
                categories_found.add(category)
        
        validation['categories_with_findings'] = len(categories_found)
        
        # Identifier les catégories manquantes
        missing_categories = set(TARGET_INDICATORS.keys()) - categories_found
        if missing_categories:
            validation['validation_errors'].append(f"Catégories TARGET manquantes: {list(missing_categories)}")
            validation['suggestions'].append("Développer des patterns spécifiques pour les catégories manquantes")
        
        # Vérifier les unités
        invalid_units = []
        for indicator in target_indicators:
            unit = indicator.get('unit', 'unknown')
            if unit not in RECOGNIZED_UNITS.values() and unit not in ['unknown', 'percentage', 'millions_dinars']:
                invalid_units.append(unit)
        
        if invalid_units:
            validation['validation_errors'].append(f"Unités non reconnues: {list(set(invalid_units))}")
            validation['suggestions'].append("Normaliser les unités selon RECOGNIZED_UNITS")
        
        # Score de validation
        target_coverage = validation['targets_found'] / validation['total_targets_defined'] if validation['total_targets_defined'] > 0 else 0
        category_coverage = validation['categories_with_findings'] / len(TARGET_INDICATORS) if TARGET_INDICATORS else 0
        
        validation['coverage_score'] = (target_coverage + category_coverage) / 2
        validation['validation_status'] = 'excellent' if validation['coverage_score'] > 0.7 else 'good' if validation['coverage_score'] > 0.4 else 'needs_improvement'
        
    except Exception as e:
        validation['validation_errors'].append(f"Erreur durant la validation: {str(e)}")
        validation['validation_status'] = 'error'
    
    return validation

def generate_target_extraction_report(data: Dict[str, Any]) -> str:
    """Génère un rapport détaillé sur l'extraction TARGET_INDICATORS"""
    report_lines = []
    
    # En-tête
    report_lines.append("# RAPPORT D'EXTRACTION TARGET_INDICATORS")
    report_lines.append("=" * 50)
    report_lines.append("")
    
    # Informations de base
    task_info = extract_task_info(data)
    report_lines.append("## Informations de base")
    report_lines.append(f"- Tâche: {task_info['task_id']}")
    report_lines.append(f"- URL: {task_info['url']}")
    report_lines.append(f"- Méthode: {task_info['extraction_method']}")
    report_lines.append("")
    
    # Validation
    validation = validate_target_indicators_extraction(data)
    report_lines.append("## Validation TARGET_INDICATORS")
    report_lines.append(f"- Statut: {validation['validation_status'].upper()}")
    report_lines.append(f"- Score de couverture: {validation['coverage_score']:.2f}")
    report_lines.append(f"- TARGET trouvés: {validation['targets_found']}/{validation['total_targets_defined']}")
    report_lines.append(f"- Catégories couvertes: {validation['categories_with_findings']}/{len(TARGET_INDICATORS)}")
    report_lines.append("")
    
    if validation['validation_errors']:
        report_lines.append("### Erreurs de validation:")
        for error in validation['validation_errors']:
            report_lines.append(f"- ❌ {error}")
        report_lines.append("")
    
    if validation['suggestions']:
        report_lines.append("### Suggestions d'amélioration:")
        for suggestion in validation['suggestions']:
            report_lines.append(f"- 💡 {suggestion}")
        report_lines.append("")
    
    # Détail par catégorie
    target_analysis = analyze_target_indicators(data)
    category_coverage = target_analysis.get('category_coverage', {})
    
    report_lines.append("## Détail par catégorie TARGET")
    for category, target_indicators in TARGET_INDICATORS.items():
        coverage_info = category_coverage.get(category, {})
        found_count = coverage_info.get('indicators_found', 0)
        total_count = len(target_indicators)
        percentage = coverage_info.get('coverage_percentage', 0)
        
        status = "✅" if percentage > 50 else "⚠️" if percentage > 0 else "❌"
        report_lines.append(f"### {status} {category.replace('_', ' ').title()}")
        report_lines.append(f"- Couverture: {found_count}/{total_count} ({percentage:.1f}%)")
        
        if coverage_info.get('details'):
            report_lines.append("- Indicateurs trouvés:")
            for detail in coverage_info['details'][:3]:  # Limiter à 3
                name = detail.get('name', 'N/A')
                value = detail.get('value', 'N/A')
                unit = detail.get('unit', '')
                report_lines.append(f"  • {name}: {value} {unit}")
        
        report_lines.append("")
    
    return "\n".join(report_lines)

def main():
    """Fonction principale avec focus TARGET_INDICATORS"""
    if len(sys.argv) != 2:
        print("Usage: python data_explorer.py <json_file>")
        print("Analyse les résultats de scraping selon TARGET_INDICATORS")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not Path(json_file).exists():
        print(f"❌ Fichier non trouvé: {json_file}")
        sys.exit(1)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("🔍 Analyse TARGET_INDICATORS en cours...")
        analysis = analyze_scraped_data(data)
        
        print_target_analysis_summary(analysis)
        
        # Validation spécifique
        validation = validate_target_indicators_extraction(data)
        print(f"\n🔍 VALIDATION TARGET_INDICATORS:")
        print(f"   Status: {validation['validation_status'].upper()}")
        print(f"   Score: {validation['coverage_score']:.2f}")
        
        if validation['validation_errors']:
            print(f"   Erreurs: {len(validation['validation_errors'])}")
        
        # Générer le rapport
        report_content = generate_target_extraction_report(data)
        report_filename = f"target_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Exporter l'analyse complète
        output_file = export_target_analysis(analysis)
        
        print(f"\n💾 Fichiers générés:")
        print(f"   📊 Analyse complète: {output_file}")
        print(f"   📋 Rapport TARGET: {report_filename}")
        print("✅ Analyse TARGET_INDICATORS terminée!")
        
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur durant l'analyse TARGET: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()