# Agentic Scraper Project

## 📋 Description du Projet

Agentic Scraper Project est un système avancé de scraping intelligent qui utilise une architecture multi-agents avec IA pour extraire et analyser automatiquement des données économiques tunisiennes. Le système combine plusieurs techniques modernes pour naviguer, scraper et analyser le contenu de sites web complexes de manière entièrement automatisée.

## 🛠️ Technologies et Outils Utilisés

### 🤖 Frameworks d'Agents IA

**LangGraph** - Pour la création de workflows multi-agents intelligents

**LangChain** - Pour l'orchestration des agents et la gestion des prompts

**Multi-agent systems** - Architecture avec agents spécialisés

### 🕸️ Outils de Scraping

**BeautifulSoup4** - Analyse et parsing HTML/XML

**Requests** - Requêtes HTTP avec sessions persistantes

**AsyncIO** - Traitement asynchrone pour le scraping parallèle

**Custom scrapers** - Scrapers spécialisés pour sites tunisiens

### 🧠 Analyse LLM

**Ollama** - Infrastructure LLM locale pour l'analyse de contenu

**Modèles Mistral/LLama** - Modèles de langage pour l'analyse économique

**Analyse contextuelle** - Compréhension des données économiques tunisiennes

### 📊 Traitement de Données

**Pydantic** - Validation et modélisation des données

**JSON Schema** - Structures de données normalisées

**Temporal filtering** - Filtrage intelligent par période temporelle

**Data validation** - Validation automatique des indicateurs économiques

## 🚀 Infrastructure

**FastAPI** - API REST moderne et performante

**Docker** - Containérisation de l'application

**Docker Compose** - Orchestration des services

**Celery** - Gestion des tâches asynchrones

## 🎯 Fonctionnalités Techniques

### Architecture Multi-Agents

**Scraper Agent** - Extraction intelligente avec sélection automatique de stratégie

**Analyzer Agent** - Analyse sémantique avec LLM et contexte tunisien

**Navigation Agent** - Découverte automatique de sources de données

**Smart Coordinator** - Orchestration avec timeouts adaptatifs

**Orchestrator** - Gestion des workflows complexes

### Techniques de Scraping Avancées

**Scraping traditionnel** - Pour APIs et données structurées

**Scraping intelligent** - Pour sites complexes avec JavaScript

**Gestion de sessions** - Maintenance d'état et cookies

**Rotation d'User-Agents** - Éviter la détection

**Retry adaptatif** - Gestion robuste des erreurs

### Analyse Intelligente

**Détection de contexte** - Reconnaissance automatique du contexte tunisien

**Extraction de motifs** - Patterns pour données économiques

**Validation sémantique** - Vérification de la cohérence des données

**Enrichissement LLM** - Amélioration automatique avec IA

## 📦 Structure Technique

app/

├── celery_app.py

├── main.py                 # FastAPI app

├── worker.py    

├── agents/                 # Système multi-agents

│   ├── orchestrator.py     # Orchestration des workflows

│   ├── scraper_agent.py    # Agent de scraping principal

│   ├── analyzer_agent.py   # Analyse LLM des données

│   ├── navigation_agent.py # Découverte de contenus

│   └── smart_coordinator.py # Coordination intelligente

├── scrapers/               # Modules de scraping

│   ├── traditional.py      # Scraping HTML traditionnel

│   └── intelligent.py      # Scraping IA avancé

├── models/                 # Modèles de données

│   └── schemas.py          # Schémas Pydantic

│   ├── database.py         # Modèles DB

├── config/

│   ├── settings.py         # Configuration

│   ├── sources.py

│   └── llm_config.py       # Config LLM

├── tasks/

│   └── scraping_tasks.py   

└── utils/                  # Utilities techniques

    ├── data_validator.py   # Validation des données
    
    ├── helpers.py          # Fonctions utilitaires
    
    ├── clean_extraction_patterns.py
    
    ├── storage.py          # Gestion stockage
    
    └── temporal_filter.py  # Filtrage temporel

    
## 🚀 Installation et Utilisation
bash
###  Cloner le repository
git clone https://github.com/DorraElarem/agentic-scraper-project.git

### Installation avec Docker
docker-compose up -d

### Ou installation manuelle
- pip install -r requirements.txt
- python -m app.main
- Le système expose une API RESTful complète pour interagir avec les différents agents et fonctionnalités de scraping.

## 📊 Résultats Techniques
Le système produit des données structurées enrichies avec:

Métadonnées techniques complètes

Scores de confiance automatiques

Contexte économique tunisien

Analyses LLm intégrées

Validation temporelle et sémantique

## 🔮 Évolutions Techniques Possibles
Intégration avec des modèles LLM plus avancés

Support de additional data sources

Amélioration des algorithmes de discovery

Optimisation des performances de scraping

Intégration avec des data warehouses
