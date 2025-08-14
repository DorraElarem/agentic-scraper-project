#!/usr/bin/env python3
"""
Script de vérification pour s'assurer que les nouveaux scrapers sont chargés
"""

import sys
import os
sys.path.append('/app')

def check_scrapers():
    """Vérifie quels scrapers sont actuellement chargés"""
    print("🔍 VÉRIFICATION DES SCRAPERS CHARGÉS")
    print("=" * 50)
    
    try:
        # Test du scraper traditionnel
        from app.scrapers.traditional import TunisianWebScraper
        scraper = TunisianWebScraper()
        
        print("📊 SCRAPER TRADITIONNEL:")
        
        # Vérifier les méthodes spécifiques aux nouveaux scrapers
        new_methods = [
            '_build_universal_patterns',
            '_extract_target_indicators_universal', 
            '_extract_by_recognized_units',
            '_universal_scrape'
        ]
        
        old_methods = [
            '_scrape_ins_with_context',
            '_extract_with_full_context',
            'contextual_patterns'
        ]
        
        new_count = 0
        for method in new_methods:
            has_method = hasattr(scraper, method)
            print(f"   {'✅' if has_method else '❌'} {method}: {'OUI' if has_method else 'NON'}")
            if has_method:
                new_count += 1
        
        old_count = 0
        for method in old_methods:
            has_method = hasattr(scraper, method)
            print(f"   {'❌' if has_method else '✅'} {method} (ancien): {'OUI' if has_method else 'NON'}")
            if has_method:
                old_count += 1
        
        print(f"\n📈 SCORE NOUVEAU SCRAPER: {new_count}/{len(new_methods)}")
        print(f"📉 SCORE ANCIEN SCRAPER: {old_count}/{len(old_methods)}")
        
        # Test du scraper intelligent
        from app.scrapers.intelligent import IntelligentScraper
        intelligent = IntelligentScraper()
        
        print("\n🧠 SCRAPER INTELLIGENT:")
        
        intelligent_new_methods = [
            '_prepare_intelligent_patterns',
            '_perform_intelligent_universal_analysis',
            '_enrich_values_with_intelligence'
        ]
        
        intelligent_new_count = 0
        for method in intelligent_new_methods:
            has_method = hasattr(intelligent, method)
            print(f"   {'✅' if has_method else '❌'} {method}: {'OUI' if has_method else 'NON'}")
            if has_method:
                intelligent_new_count += 1
        
        print(f"\n📈 SCORE NOUVEAU INTELLIGENT: {intelligent_new_count}/{len(intelligent_new_methods)}")
        
        # Test settings
        from app.config.settings import settings
        print(f"\n⚙️ SETTINGS:")
        print(f"   📊 TARGET_INDICATORS: {len(settings.TARGET_INDICATORS)} catégories")
        print(f"   💱 RECOGNIZED_UNITS: {len(settings.RECOGNIZED_UNITS)} unités")
        print(f"   📅 TARGET_YEARS: {len(settings.TARGET_YEARS)} années")
        
        # Conclusion
        total_new = new_count + intelligent_new_count
        total_possible = len(new_methods) + len(intelligent_new_methods)
        
        print(f"\n🎯 RÉSULTAT GLOBAL:")
        print(f"   Méthodes nouvelles: {total_new}/{total_possible}")
        print(f"   Méthodes anciennes: {old_count}/{len(old_methods)}")
        
        if total_new == total_possible and old_count == 0:
            print(f"\n🎉 PARFAIT ! NOUVEAUX SCRAPERS UNIVERSELS ACTIFS")
            return True
        elif total_new > total_possible // 2:
            print(f"\n⚠️ PARTIELLEMENT CHARGÉ - Redémarrage nécessaire")
            return False
        else:
            print(f"\n❌ ANCIENS SCRAPERS ENCORE ACTIFS - Fichiers non mis à jour")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quick_extraction():
    """Test rapide d'extraction avec les nouveaux scrapers"""
    print(f"\n🧪 TEST D'EXTRACTION RAPIDE")
    print("=" * 30)
    
    try:
        from app.scrapers.traditional import TunisianWebScraper
        
        scraper = TunisianWebScraper()
        
        # Test HTML simple avec des données économiques
        test_html = """
        <html>
        <head><title>Test INS - Statistiques</title></head>
        <body>
            <h1>Indicateurs Économiques Tunisie</h1>
            <p>Inflation : 6,7% en juillet 2024</p>
            <p>PIB : 125000 millions de dinars en 2024</p>
            <p>Exportations : 15000 MD au premier trimestre</p>
            <table>
                <tr><th>Indicateur</th><th>Valeur</th></tr>
                <tr><td>Chômage</td><td>15,3%</td></tr>
                <tr><td>Population</td><td>12000000 habitants</td></tr>
            </table>
        </body>
        </html>
        """
        
        # Test avec le nouveau scraper universel
        result = scraper._universal_scrape(test_html, "https://test.ins.tn/stats")
        
        if result and result.structured_data.get('extracted_values'):
            values = result.structured_data['extracted_values']
            print(f"✅ EXTRACTION RÉUSSIE: {len(values)} valeurs")
            
            # Afficher quelques valeurs
            for i, (key, value) in enumerate(list(values.items())[:3]):
                indicator = value.get('indicator_name', 'N/A')
                val = value.get('value', 0)
                unit = value.get('unit', '')
                method = value.get('extraction_method', '')
                print(f"   {i+1}. {indicator}: {val} {unit} [{method}]")
            
            # Vérifier les métadonnées universelles
            summary = result.structured_data.get('extraction_summary', {})
            if summary:
                print(f"   📊 Target indicators: {summary.get('target_indicators_matched', 0)}")
                print(f"   📊 Categories found: {summary.get('categories_found', 0)}")
            
            return True
        else:
            print("❌ AUCUNE VALEUR EXTRAITE")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR DE TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🔍 DIAGNOSTIC COMPLET DES SCRAPERS")
    print("=" * 60)
    
    scrapers_ok = check_scrapers()
    extraction_ok = test_quick_extraction() if scrapers_ok else False
    
    print(f"\n" + "=" * 60)
    print("🎯 DIAGNOSTIC FINAL:")
    print(f"   📦 Scrapers chargés: {'✅ OUI' if scrapers_ok else '❌ NON'}")
    print(f"   🔧 Extraction fonctionnelle: {'✅ OUI' if extraction_ok else '❌ NON'}")
    
    if scrapers_ok and extraction_ok:
        print(f"\n🎉 TOUT FONCTIONNE ! Les scrapers universels sont actifs.")
        print(f"🚀 Votre tâche bloquée devrait maintenant se terminer correctement.")
    else:
        print(f"\n⚠️ PROBLÈME DÉTECTÉ:")
        if not scrapers_ok:
            print(f"   - Les nouveaux fichiers ne sont pas chargés")
            print(f"   - Solution: docker-compose build --no-cache")
        if not extraction_ok:
            print(f"   - L'extraction ne fonctionne pas")
            print(f"   - Vérifiez les imports et erreurs ci-dessus")
    
    return 0 if (scrapers_ok and extraction_ok) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)