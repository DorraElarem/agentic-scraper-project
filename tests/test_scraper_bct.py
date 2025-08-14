# Fichier : test_intelligent_urgent.py
from app.scrapers.intelligent import IntelligentScraper
from app.config.sources import TunisianSource

# 1. Initialisation
scraper = IntelligentScraper(delay=2)

# 2. Test sur l'URL BCT (avec fallback automatique)
test_url = "https://www.bct.gov.tn/bct/siteprod/tableau_statistique.jsp?params=PLFe5eyJjcHZfY3MiOiIxMTY1IiwidGFxIjoxfQ=="
result = scraper.scrape_with_analysis(test_url)

# 3. Affichage des résultats
print("=== CONTENU ANALYSÉ ===")
print(result.content[:1000] + "...\n" if result else "Échec du scraping")

print("\n=== INDICATEURS DÉTECTÉS ===")
if result and result.metadata.get('analysis'):
    for indicator in result.metadata['analysis']['indicators'][:5]:  # 5 premiers
        print(f"{indicator['category']}: {indicator['indicator']}")
        print(f"Contexte: {indicator['context']}\n")
else:
    print("Aucun indicateur détecté")

print("\n=== MÉTADONNÉES COMPLÈTES ===")
print(result.metadata if result else "Aucun résultat")