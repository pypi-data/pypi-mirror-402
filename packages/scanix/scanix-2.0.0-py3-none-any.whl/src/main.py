#!/usr/bin/env python3


import sys
import os
from pathlib import Path

# Ajoute le dossier src au path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

def main():
    """Fonction principale"""
    from src.ui.app import SecureCodeApp
    
    # Vérifie Python 3.8+
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou supérieur requis")
        sys.exit(1)
    
    # Charge les variables d'environnement
    from dotenv import load_dotenv
    load_dotenv()
    
    # Vérifie l'environnement
    check_environment()
    
    # Lance l'application
    app = SecureCodeApp()
    app.run()

def check_environment():
    """Vérifie les prérequis"""
    # Vérifie que le dossier de travail est correct
    cwd = Path.cwd()
    if not (cwd / "requirements.txt").exists():
        print("⚠️  Attention: requirements.txt non trouvé dans le dossier courant")
    
    # Vérifie les dépendances
    try:
        import textual
        print(f"✅ Textual {textual.__version__} installé")
    except ImportError:
        print("❌ Textual non installé. Exécutez: pip install -r requirements.txt")
        sys.exit(1)
    
    # Message de démarrage
    print("🔒 SecureCode AI Scanner")
    print("🚀 Démarrage...")

if __name__ == "__main__":
    main()