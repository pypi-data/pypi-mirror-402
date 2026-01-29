# 🚀 Démarrage Rapide - Scanix

Guide ultra-simple pour utiliser Scanix en 5 minutes.

---

## 📦 Installation (30 secondes)

### Linux / Mac

```bash
git clone https://github.com/Ore2025/scanix.git
cd scanix
pip install -r requirements.txt
python run.py
```

### Windows

```cmd
git clone https://github.com/Ore2025/scanix.git
cd scanix
pip install -r requirements.txt
python run.py
```

**Ou utilisez les scripts d'installation :**

```bash
# Linux/Mac
chmod +x install.sh
./install.sh

# Windows
install.bat
```

---

## ⚡ Utilisation Rapide

### 1. Lancer Scanix
```bash
python run.py
```

### 2. Scanner un fichier
1. Menu principal → `1` (Scanner un fichier)
2. Naviguez jusqu'à votre fichier
3. Choisissez le mode :
   - **Rapide** : 6 vulnérabilités critiques (2s)
   - **Complet** : 25+ vulnérabilités (5s)
4. Consultez les résultats
5. Exportez si besoin (JSON, HTML, TXT, CSV)

### 3. Scanner un dossier
1. Menu principal → `2` (Scanner un dossier)
2. Sélectionnez votre projet
3. Choisissez les fichiers (ou Ctrl+A pour tout)
4. Mode Rapide ou Complet
5. Résultats + Export

---

## 🎯 Exemples

### Exemple 1 : Scan Rapide d'un Fichier Python

```bash
python run.py
# → Scanner un fichier
# → Sélectionner app.py
# → Mode Rapide
# → Voir les résultats
```

**Temps : ~2-5 secondes**

### Exemple 2 : Audit Complet d'un Projet

```bash
python run.py
# → Scanner un dossier
# → Choisir mon_projet/
# → Sélectionner tous les fichiers Python (.py)
# → Mode Complet
# → Exporter en HTML
```

**Temps : ~2-10 minutes selon la taille**

### Exemple 3 : Vérification Avant Commit

```bash
# Scan rapide des fichiers modifiés
python run.py
# → Scanner un fichier
# → Sélectionner le fichier modifié
# → Mode Rapide
```

**Temps : ~2 secondes**

---

## 📊 Types de Vulnérabilités Détectées

### Mode Rapide (6 critiques)
- ✅ Injection SQL
- ✅ XSS (Cross-Site Scripting)
- ✅ Secrets exposés (mots de passe, API keys)
- ✅ Injection de commandes
- ✅ CSRF
- ✅ Path Traversal

### Mode Complet (25+)
Tout le mode rapide + :
- ✅ Injection NoSQL, LDAP, XML
- ✅ Désérialisation non sécurisée
- ✅ Cryptographie faible
- ✅ Configuration dangereuse
- ✅ Authentification faible
- ✅ Et 15+ autres...

---

## 🎨 Navigation

### Raccourcis Clavier
- `Ctrl+Q` : Quitter l'application
- `Escape` : Retour à l'écran précédent
- `Ctrl+A` : Tout sélectionner
- `Ctrl+D` : Tout désélectionner
- `Flèches` : Naviguer dans les menus/listes

### Filtres (Sélection de Dossier)
- Python (`.py`)
- JavaScript (`.js`, `.ts`)
- PHP (`.php`)
- HTML (`.html`, `.htm`)
- Java (`.java`)
- Autre (C, C++, Go, Ruby, SQL...)

---

## 💾 Exports

Les exports sont sauvegardés dans :
- **Linux/Mac** : `~/SecureCode_Exports/`
- **Windows** : `C:\Users\VotreNom\SecureCode_Exports\`

### Formats disponibles
- **JSON** : Pour intégration CI/CD
- **HTML** : Rapport visuel élégant
- **TXT** : Rapport texte simple
- **CSV** : Import dans Excel

---

## 🔧 Résolution de Problèmes

### "Module textual not found"
```bash
pip install textual
```

### "Python not found"
```bash
# Utilisez python3 au lieu de python
python3 run.py
```

### "Permission denied" (Linux/Mac)
```bash
chmod +x run.py install.sh
```

### Dépendances manquantes
```bash
pip install -r requirements.txt --upgrade
```

---

## 📚 Ressources

- **Documentation complète** : [README.md](README.md)
- **Code source** : [GitHub](https://github.com/Ore2025/scanix)
- **Rapporter un bug** : [Issues](https://github.com/Ore2025/scanix/issues)

---

## ❓ Questions Fréquentes

**Q : Dois-je créer un environnement virtuel ?**  
R : Non, pas obligatoire. Un simple `pip install` suffit.

**Q : Combien de temps ça prend ?**  
R : Mode Rapide = 2s/fichier, Mode Complet = 5s/fichier

**Q : Quels langages sont supportés ?**  
R : Python, JavaScript, PHP, Java, C/C++, Go, Ruby, HTML, SQL

**Q : C'est gratuit ?**  
R : Oui, 100% gratuit et open-source (MIT License)

---

## 🎓 Tutoriel Complet (5 minutes)

### Étape 1 : Installation
```bash
git clone https://github.com/Ore2025/scanix.git
cd scanix
pip install -r requirements.txt
```

### Étape 2 : Premier Scan
```bash
python run.py
```

### Étape 3 : Navigation
- Menu : Utilisez les flèches ou numéros
- Sélection : Espace ou Entrée
- Retour : Escape

### Étape 4 : Choix du Mode
- **Rapide** : Pour un check quotidien
- **Complet** : Pour un audit sécurité

### Étape 5 : Résultats
- Consultez les vulnérabilités trouvées
- Filtrez par gravité (Critique, Élevée, Moyenne, Faible)
- Exportez le rapport

### Étape 6 : Export
- Choisissez le format (HTML recommandé pour rapport)
- Fichier sauvegardé dans `~/SecureCode_Exports/`

---

<div align="center">

**Prêt à scanner ! 🚀**

[⬆ Retour au README principal](README.md)

</div>