#!/usr/bin/env python3
# tests/test_config.py

import sys
from pathlib import Path

# Ajoute le dossier racine au PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config.sources import (
    TunisianSource,
    get_source_config,
    SOURCE_CONFIG
)

def test_bct_config():
    """Teste la configuration de la BCT"""
    config = get_source_config(TunisianSource.BCT)
    assert config is not None
    assert "base_url" in config
    print("✓ Configuration BCT valide")

def test_pib_selectors():
    """Teste les sélecteurs pour le PIB"""
    pib_config = get_source_config(TunisianSource.BCT, "PIB")
    assert "table" in pib_config["selectors"]
    print("✓ Sélecteurs PIB valides")

if __name__ == "__main__":
    test_bct_config()
    test_pib_selectors()
    print("\nTous les tests passés avec succès !")