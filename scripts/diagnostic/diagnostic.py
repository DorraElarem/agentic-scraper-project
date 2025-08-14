#!/bin/bash
# Script de diagnostic et réparation Agentic Scraper

echo "🔍 DIAGNOSTIC AGENTIC SCRAPER"
echo "=============================="

# 1. Vérifier l'état des conteneurs
echo "📊 État des conteneurs:"
docker-compose ps

echo ""
echo "🔍 Vérification des services individuels:"

# 2. Vérifier les logs du service web
echo "📋 Logs du service web (dernières 20 lignes):"
docker-compose logs --tail=20 web

echo ""
echo "📋 Logs du service worker (dernières 10 lignes):"
docker-compose logs --tail=10 worker

echo ""
echo "🌐 Test de connectivité des ports:"

# 3. Vérifier les ports
echo "Port 8000 (FastAPI): $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "INACCESSIBLE")"
echo "Port 5555 (Flower): $(curl -s -o /dev/null -w "%{http_code}" http://localhost:5555 || echo "INACCESSIBLE")"
echo "Port 11434 (Ollama): $(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/version || echo "INACCESSIBLE")"

echo ""
echo "🔧 Actions de réparation recommandées:"

# 4. Suggestions de réparation
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Service web inaccessible - Redémarrage nécessaire"
    echo "Commandes à exécuter:"
    echo "  docker-compose restart web"
    echo "  docker-compose logs -f web"
else
    echo "✅ Service web accessible"
fi

echo ""
echo "📝 Pour forcer un redémarrage complet:"
echo "  docker-compose down"
echo "  docker-compose up -d"
echo "  docker-compose logs -f"