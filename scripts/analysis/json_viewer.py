#!/usr/bin/env python3
"""
Visualisateur du rapport d'analyse des données économiques
Affiche le contenu du fichier JSON de manière lisible
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

class AnalysisViewer:
    def __init__(self, json_file: str = None):
        if json_file is None:
            # Trouver le fichier JSON le plus récent
            json_files = [f for f in os.listdir('.') if f.startswith('economic_analysis_') and f.endswith('.json')]
            if json_files:
                self.json_file = max(json_files, key=os.path.getctime)
                print(f"📁 Utilisation du fichier: {self.json_file}")
            else:
                raise FileNotFoundError("Aucun fichier d'analyse trouvé")
        else:
            self.json_file = json_file
    
    def load_analysis(self) -> Dict[str, Any]:
        """Charge les données d'analyse depuis le fichier JSON"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            return {}
    
    def display_indicators(self, indicators: Dict[str, Any]):
        """Affiche les indicateurs économiques détaillés"""
        print("\n" + "="*60)
        print("💰 INDICATEURS ÉCONOMIQUES DÉTAILLÉS")
        print("="*60)
        
        for category, items in indicators.items():
            if items and category != 'autres':
                print(f"\n🏷️ {category.replace('_', ' ').upper()}:")
                if isinstance(items, list):
                    unique_items = list(set(items))  # Supprimer les doublons
                    for i, item in enumerate(unique_items[:10], 1):  # Top 10
                        print(f"   {i:2d}. {item}")
                    if len(unique_items) > 10:
                        print(f"      ... et {len(unique_items) - 10} autres")
        
        # Afficher les liens spéciaux s'ils existent
        if 'autres' in indicators and indicators['autres']:
            print(f"\n🔗 LIENS STATISTIQUES SPÉCIALISÉS:")
            links = indicators['autres']
            for i, link in enumerate(links[:5], 1):  # Top 5 liens
                if isinstance(link, dict):
                    print(f"   {i}. {link.get('text', 'N/A')}")
                    print(f"      URL: {link.get('url', 'N/A')}")
    
    def display_data_tables(self, tables: list):
        """Affiche les informations sur les tableaux de données"""
        print("\n" + "="*60)
        print("📊 TABLEAUX DE DONNÉES")
        print("="*60)
        
        if not tables:
            print("⚠️  Aucun tableau détecté dans cette page")
            print("💡 Conseil: Explorer les sous-pages pour trouver des données tabulaires")
            return
        
        for i, table in enumerate(tables, 1):
            print(f"\n📋 TABLEAU {i}:")
            print(f"   • Colonnes: {table.get('col_count', 0)}")
            print(f"   • Lignes: {table.get('row_count', 0)}")
            
            headers = table.get('headers', [])
            if headers:
                print(f"   • En-têtes: {', '.join(headers[:5])}")
                if len(headers) > 5:
                    print(f"     ... et {len(headers) - 5} autres colonnes")
    
    def display_thematic_sections(self, sections: list):
        """Affiche les sections thématiques trouvées"""
        print("\n" + "="*60)
        print("🏛️ SECTIONS THÉMATIQUES")
        print("="*60)
        
        if not sections:
            print("⚠️  Aucune section thématique spécifique détectée")
            return
        
        for i, section in enumerate(sections[:10], 1):  # Top 10
            print(f"\n📂 SECTION {i}:")
            if section.get('id'):
                print(f"   • ID: {section['id']}")
            if section.get('class'):
                print(f"   • Classes: {section['class']}")
            preview = section.get('text_preview', '')[:100]
            print(f"   • Aperçu: {preview}...")
    
    def display_recommendations_detailed(self, recommendations: list):
        """Affiche les recommandations avec plus de détails"""
        print("\n" + "="*60)
        print("🎯 PLAN D'ACTION DÉTAILLÉ")
        print("="*60)
        
        priorities = {
            'URGENT': [],
            'IMPORTANT': [],
            'MOYEN TERME': []
        }
        
        for rec in recommendations:
            if any(word in rec for word in ['extracteur', 'détecté', 'LLM']):
                priorities['URGENT'].append(rec)
            elif any(word in rec for word in ['tableau', 'parser', 'format']):
                priorities['IMPORTANT'].append(rec)
            else:
                priorities['MOYEN TERME'].append(rec)
        
        for priority, items in priorities.items():
            if items:
                print(f"\n🚨 {priority}:")
                for i, item in enumerate(items, 1):
                    print(f"   {i}. {item}")
    
    def suggest_next_urls(self, analysis: Dict[str, Any]):
        """Suggère les prochaines URLs à scraper"""
        print("\n" + "="*60)
        print("🎯 PROCHAINES URLS À EXPLORER")
        print("="*60)
        
        base_url = "https://www.ins.tn"
        suggested_urls = [
            f"{base_url}/statistiques/50",  # Balance commerciale
            f"{base_url}/statistiques/74",  # Comptes nationaux  
            f"{base_url}/statistiques/151", # Population active
            f"{base_url}/statistiques/90",  # Indices des prix
            f"{base_url}/publication",      # Publications
            "http://apps.ins.tn/comex/fr/index.php",  # Commerce extérieur
            "http://dataportal.ins.tn/"     # Portail de données
        ]
        
        print("📍 URLs prioritaires pour extraction de données:")
        for i, url in enumerate(suggested_urls, 1):
            print(f"   {i}. {url}")
        
        print("\n💡 Commandes pour tester:")
        for url in suggested_urls[:3]:  # Top 3
            print(f'''curl -X POST http://localhost:8000/scrape \\
  -H "Content-Type: application/json" \\
  -d '{{"urls": ["{url}"], "analysis_type": "advanced"}}\'''')
            print()
    
    def display_full_analysis(self):
        """Affiche l'analyse complète"""
        analysis = self.load_analysis()
        
        if not analysis:
            print("❌ Impossible de charger l'analyse")
            return
        
        # En-tête
        print("🔍 ANALYSE COMPLÈTE DES DONNÉES ÉCONOMIQUES INS")
        print("="*70)
        
        task_info = analysis.get('task_info', {})
        print(f"🆔 Tâche: {task_info.get('task_id')}")
        print(f"🌐 URL: {task_info.get('url')}")
        print(f"📅 Extraction: {task_info.get('scraped_at')}")
        print(f"✅ Statut: {task_info.get('status')}")
        
        # Statistiques du contenu
        stats = analysis.get('content_stats', {})
        print(f"\n📊 STATISTIQUES DU CONTENU:")
        print(f"   • Caractères: {stats.get('total_characters', 0):,}")
        print(f"   • Mots: {stats.get('word_count', 0):,}")
        print(f"   • Tableaux: {stats.get('table_count', 0)}")
        
        # Indicateurs détaillés
        indicators = analysis.get('economic_indicators', {})
        self.display_indicators(indicators)
        
        # Tableaux de données
        tables = analysis.get('data_tables', [])
        self.display_data_tables(tables)
        
        # Sections thématiques
        sections = analysis.get('thematic_sections', [])
        self.display_thematic_sections(sections)
        
        # Recommandations détaillées
        recommendations = analysis.get('recommendations', [])
        self.display_recommendations_detailed(recommendations)
        
        # Suggestions d'URLs
        self.suggest_next_urls(analysis)
        
        print("\n" + "="*70)
        print("✅ ANALYSE TERMINÉE")
        print(f"📄 Fichier source: {self.json_file}")
        print("="*70)


def main():
    """Fonction principale"""
    try:
        viewer = AnalysisViewer()
        viewer.display_full_analysis()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("💡 Assurez-vous d'avoir exécuté data_explorer.py d'abord")


if __name__ == "__main__":
    main()