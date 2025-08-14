# Dockerfile corrigé pour résoudre les problèmes d'import

FROM python:3.11-slim

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    gnupg \
    ca-certificates \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Installer Flower pour le monitoring Celery
RUN pip install --no-cache-dir flower

RUN pip install psutil

# Copier le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p logs && \
    mkdir -p data && \
    chmod -R 755 logs data

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /bin/bash appuser && \
    chown -R appuser:appgroup /app

# Changer vers l'utilisateur non-root
USER appuser

# Port exposé
EXPOSE 8000

# Point d'entrée par défaut
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]