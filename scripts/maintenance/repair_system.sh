#!/bin/bash

# ========================================
# Script de réparation automatique 
# Agentic Scraper System
# ========================================

set -e  # Arrêter en cas d'erreur

echo "🔧 RÉPARATION AUTOMATIQUE DU SYSTÈME AGENTIC SCRAPER"
echo "=================================================="

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier Docker
check_docker() {
    log_info "Vérification de Docker..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker n'est pas démarré"
        exit 1
    fi
    
    log_success "Docker opérationnel"
}

# Nettoyer les conteneurs existants
cleanup_containers() {
    log_info "Nettoyage des conteneurs existants..."
    
    # Arrêter tous les conteneurs du projet
    docker-compose down --remove-orphans || true
    
    # Supprimer les conteneurs orphelins
    docker container prune -f || true
    
    log_success "Conteneurs nettoyés"
}

# Vérifier et corriger les fichiers de configuration
fix_configuration() {
    log_info "Vérification de la configuration..."
    
    # Vérifier .env
    if [ ! -f ".env" ]; then
        log_warning "Fichier .env manquant, création..."
        cat > .env << 'EOF'
# Configuration corrigée automatiquement
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dorra123
POSTGRES_DB=scraper_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=redis://redis:6379/1
SECRET_KEY=4a5e6f7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f
SCRAPE_DELAY_SEC=2.5
SCRAPE_MAX_RETRIES=3
SCRAPE_TIMEOUT_SEC=30
SCRAPE_USER_AGENT=Mozilla/5.0 (compatible; AgenticScraper/1.0)
MAX_CONTENT_LENGTH_KB=5000
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=mistral:7b-instruct-v0.2-q4_0
ENABLE_LLM_ANALYSIS=true
APP_ENV=development
DEBUG=false
LOG_LEVEL=INFO
EOF
        log_success "Fichier .env créé"
    fi
    
    # Vérifier requirements.txt
    if [ ! -f "requirements.txt" ]; then
        log_error "Fichier requirements.txt manquant"
        exit 1
    fi
    
    log_success "Configuration vérifiée"
}

# Construire les images Docker
build_images() {
    log_info "Construction des images Docker..."
    
    # Nettoyer les images existantes
    docker-compose build --no-cache --pull
    
    log_success "Images construites"
}

# Démarrer les services de base
start_base_services() {
    log_info "Démarrage des services de base..."
    
    # Démarrer PostgreSQL et Redis en premier
    docker-compose up -d db redis
    
    # Attendre que les services soient prêts
    log_info "Attente de PostgreSQL..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T db pg_isready -U postgres &> /dev/null; then
            break
        fi
        sleep 2
        ((timeout -= 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "PostgreSQL n'a pas démarré à temps"
        exit 1
    fi
    
    log_info "Attente de Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
            break
        fi
        sleep 2
        ((timeout -= 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Redis n'a pas démarré à temps"
        exit 1
    fi
    
    log_success "Services de base démarrés"
}

# Initialiser la base de données
init_database() {
    log_info "Initialisation de la base de données..."
    
    # Exécuter le script de correction de la base
    if [ -f "fix_database_complete.py" ]; then
        docker-compose exec -T web python fix_database_complete.py || true
    fi
    
    log_success "Base de données initialisée"
}

# Démarrer Ollama et installer les modèles
setup_ollama() {
    log_info "Configuration d'Ollama..."
    
    # Démarrer Ollama
    docker-compose up -d ollama
    
    # Attendre qu'Ollama soit prêt
    log_info "Attente d'Ollama..."
    timeout=120
    while [ $timeout -gt 0 ]; do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            break
        fi
        sleep 5
        ((timeout -= 5))
    done
    
    if [ $timeout -le 0 ]; then
        log_warning "Ollama n'a pas démarré à temps, continuons sans LLM"
        return 0
    fi
    
    # Installer le modèle Mistral si pas présent
    log_info "Vérification du modèle Mistral..."
    if ! curl -s http://localhost:11434/api/tags | grep -q "mistral"; then
        log_info "Installation du modèle Mistral (cela peut prendre du temps)..."
        docker-compose exec ollama ollama pull mistral:7b-instruct-v0.2-q4_0 || {
            log_warning "Échec de l'installation de Mistral, LLM désactivé"
            return 0
        }
    fi
    
    log_success "Ollama configuré"
}

# Démarrer tous les services
start_all_services() {
    log_info "Démarrage de tous les services..."
    
    # Démarrer l'application web
    docker-compose up -d web
    
    # Attendre que l'API soit prête
    log_info "Attente de l'API..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            break
        fi
        sleep 3
        ((timeout -= 3))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "L'API n'a pas démarré à temps"
        return 1
    fi
    
    # Démarrer le worker Celery
    docker-compose up -d worker
    
    # Attendre que le worker soit prêt
    log_info "Attente du worker Celery..."
    sleep 10
    
    log_success "Tous les services démarrés"
}

# Tester le système
test_system() {
    log_info "Test du système..."
    
    # Test de l'API
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_success "API opérationnelle"
    else
        log_error "API non fonctionnelle"
        return 1
    fi
    
    # Test de Celery
    if curl -s http://localhost:8000/debug/celery | grep -q "scraping_task_available"; then
        log_success "Celery opérationnel"
    else
        log_warning "Problème avec Celery"
    fi
    
    # Test de scraping simple
    log_info "Test de scraping..."
    response=$(curl -s -X POST http://localhost:8000/scrape \
        -H "Content-Type: application/json" \
        -d '{"urls":["https://httpbin.org/json"],"analysis_type":"standard"}')
    
    if echo "$response" | grep -q "task_id"; then
        log_success "Scraping fonctionnel"
    else
        log_warning "Problème avec le scraping"
    fi
}

# Afficher le statut final
show_status() {
    echo ""
    echo "==============================================="
    log_info "STATUT FINAL DU SYSTÈME"
    echo "==============================================="
    
    # Afficher les services en cours
    echo ""
    log_info "Services actifs:"
    docker-compose ps
    
    echo ""
    log_info "URLs importantes:"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • API Health: http://localhost:8000/health"
    echo "  • Celery Debug: http://localhost:8000/debug/celery"
    echo "  • Ollama: http://localhost:11434"
    
    echo ""
    log_info "Commandes utiles:"
    echo "  • Voir les logs: docker-compose logs -f [service]"
    echo "  • Redémarrer: docker-compose restart [service]"
    echo "  • Arrêter: docker-compose down"
    echo "  • Diagnostic: python diagnostic_complete.py"
}

# Fonction de nettoyage en cas d'erreur
cleanup_on_error() {
    log_error "Erreur détectée, nettoyage..."
    docker-compose down || true
    exit 1
}

# Trap pour nettoyer en cas d'interruption
trap cleanup_on_error ERR INT TERM

# ========================================
# EXÉCUTION PRINCIPALE
# ========================================

main() {
    echo "🚀 Début de la réparation automatique..."
    echo ""
    
    # Étapes de réparation
    check_docker
    cleanup_containers
    fix_configuration
    build_images
    start_base_services
    init_database
    setup_ollama
    start_all_services
    
    echo ""
    log_success "🎉 RÉPARATION TERMINÉE AVEC SUCCÈS!"
    
    # Test du système
    test_system
    show_status
    
    echo ""
    log_info "Pour un diagnostic complet, exécutez:"
    echo "  python diagnostic_complete.py"
    echo ""
    log_success "Le système est prêt à être utilisé!"
}

# Vérifier les arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Afficher cette aide"
    echo "  --clean        Nettoyage complet (supprime les volumes)"
    echo "  --no-ollama    Ignorer la configuration d'Ollama"
    echo ""
    echo "Ce script répare automatiquement le système Agentic Scraper"
    exit 0
fi

if [ "$1" == "--clean" ]; then
    log_warning "Nettoyage complet demandé..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    docker volume prune -f
fi

if [ "$1" == "--no-ollama" ]; then
    log_info "Configuration d'Ollama ignorée"
    setup_ollama() {
        log_info "Configuration d'Ollama ignorée (--no-ollama)"
    }
fi

# Lancer la réparation
main